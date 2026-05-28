from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  ListView, TemplateView, UpdateView)

from .forms import (AbsenceForm, AnnouncementForm, CalendarEventForm,
                    EmployeeRegistrationForm, EventForm, ProfileForm,
                    SupportTicketForm)
from .mixins import RoleRequiredMixin
from .models import (AbsenceRecord, Announcement, CalendarEvent, Department,
                     Employee, InAppNotification, Role, SupportTicket,
                     TicketReply, VmedaBrochure, VmedaInfoSection)


class CustomLoginView(LoginView):
    template_name = 'core/login.html'


class RegisterView(FormView):
    template_name = 'core/register.html'
    form_class = EmployeeRegistrationForm
    success_url = '/dashboard/'
    
    def form_valid(self, form):
        # 1. Сохраняем пользователя, но пока не пишем в БД (commit=False)
        user = form.save(commit=False)
        
        # 2. ПРИНУДИТЕЛЬНО ставим роль "Пользователь"
        user.role = Role.USR 
        
        # 3. Теперь сохраняем в базу
        user.save()
        
        # 4. Авторизуем пользователя
        login(self.request, user)
        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        today = now.date()
        
        # 1. Уведомления
        ctx['unread_notifs'] = InAppNotification.objects.filter(
            recipient=user, is_read=False
        ).count()
        
        # 2. Ближайшие события
        now = timezone.now()
        two_weeks_later = now + timedelta(days=14)

        ctx['upcoming_events'] = CalendarEvent.objects.filter(
            Q(creator=user) | 
            Q(visibility='all') |
            (Q(visibility='dept') & Q(creator__department=user.department))
        ).filter(
            # 🔥 Окно: начало не дальше 14 дней
            start_dt__lte=two_weeks_later
        ).filter(
            # 🔥 ИЛИ: ещё не началось ИЛИ сейчас идёт (не закончилось)
            Q(start_dt__gte=now) |           # Будущие
            (Q(end_dt__isnull=True) & Q(start_dt__lte=now)) |  # Текущие без конца
            (Q(end_dt__gte=now) & Q(start_dt__lte=now))  # Текущие с концом
        ).distinct().order_by('start_dt')[:5]
        
        # 3. Дни рождения (возвращаем сами объекты Employee, как ждёт шаблон)
        employees_with_bday = Employee.objects.filter(
            is_active=True,
            birth_date__isnull=False
        ).exclude(birth_date__year=1900)
        
        birthdays_today = []
        birthdays_tomorrow = []
        birthdays_upcoming = []
        
        for emp in employees_with_bday:
            bday_this_year = date(today.year, emp.birth_date.month, emp.birth_date.day)
            if bday_this_year < today:
                bday_this_year = date(today.year + 1, emp.birth_date.month, emp.birth_date.day)
            
            days_diff = (bday_this_year - today).days
            
            if days_diff == 0:
                birthdays_today.append(emp)
            elif days_diff == 1:
                birthdays_tomorrow.append(emp)
            elif 2 <= days_diff <= 7:
                birthdays_upcoming.append(emp)
                
        # Сортировка ближайших по дате
        birthdays_upcoming.sort(key=lambda x: (x.birth_date.month, x.birth_date.day))
        
        ctx['birthdays_today'] = birthdays_today
        ctx['birthdays_tomorrow'] = birthdays_tomorrow
        ctx['birthdays_upcoming'] = birthdays_upcoming
        
        # 4. Сейчас отсутствуют
        ctx['current_absences'] = AbsenceRecord.objects.filter(
            start_dt__lte=today,
            end_dt__gte=today
        ).select_related('employee', 'employee__department')
        
        # 5. Объявления
# 🔥 Используем поле scope вместо visible_to_all
        ctx['announcements'] = Announcement.objects.filter(
            Q(scope='all') | Q(department=user.department)
        ).order_by('-created_at')[:5]
        
        # 6. Вспомогательные переменные для шаблона
        ctx['today'] = today
        ctx['now'] = now
        
        return ctx
class EmployeeDirectoryView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'core/directory.html'
    context_object_name = 'employees'
    
    def get_queryset(self):
        from django.db.models import Q
        
        qs = Employee.objects.filter(is_active=True, is_superuser=False)
        q = self.request.GET.get('q')
            
        if q and len(q) >= 2:
            # 🔥 Python-фильтрация для регистронезависимого поиска
            q_lower = q.lower()
            results = []
            for emp in qs.select_related('department'):
                if (q_lower in emp.last_name.lower() or
                    q_lower in emp.first_name.lower() or
                    (emp.department and q_lower in emp.department.name.lower())):
                    results.append(emp)
            return results
        
        return qs.order_by('last_name', 'first_name')



class CalendarView(LoginRequiredMixin, ListView):
    model = CalendarEvent
    template_name = 'core/calendar.html'
    context_object_name = 'events'

    def get_queryset(self):
        user = self.request.user
        show_past = self.request.GET.get('show_past') == '1'
        
        # 🔥 Используем timezone, который уже импортирован сверху
        now = timezone.now()

        # Базовый фильтр видимости
        q = Q(creator=user)
        if user.department:
            q |= Q(visibility='dept', creator__department=user.department)
        q |= Q(visibility='all')

        queryset = CalendarEvent.objects.filter(q).distinct()

        # 🔥 Фильтр прошедших событий (исправленный)
        if not show_past:
            queryset = queryset.filter(
                # 1. Либо конец строго в будущем
                Q(end_dt__gt=now) | 
                # 2. Либо конца нет, но начало тоже в будущем
                (Q(end_dt__isnull=True) & Q(start_dt__gt=now))
            )

        return queryset.order_by('-start_dt')

class EventCreateView(LoginRequiredMixin, CreateView):
    model = CalendarEvent
    form_class = EventForm
    template_name = 'core/event_form.html'
    success_url = reverse_lazy('calendar')

    def form_valid(self, form):
        # 🔥 ВАЖНО: явно указываем автора события
        form.instance.creator = self.request.user
        print(f"✅ Сохраняю событие от пользователя {self.request.user}")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(f"❌ Ошибки формы: {form.errors}")
        return super().form_invalid(form)


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = CalendarEvent
    template_name = 'core/event_confirm_delete.html'
    success_url = reverse_lazy('calendar')
    
    def get_queryset(self):
        return CalendarEvent.objects.filter(creator=self.request.user)


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'core/announcements.html'
    context_object_name = 'announcements'
    
    def get_queryset(self):
        user = self.request.user
        return Announcement.objects.filter(
            Q(scope='all') | Q(scope='dept', department=user.department)
        ).order_by('-created_at')


class AnnouncementCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [Role.ADM, Role.SUP, Role.SID]
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'core/announcement_form.html'
    success_url = reverse_lazy('announcements')
    
    def form_valid(self, form):
        # 1. Сохраняем оповещение, но пока не фиксируем в БД (чтобы получить ID)
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save() # Теперь у объекта есть ID
        
        # 2. Создаём уведомления для сотрудников
        self._create_notifications_for_announcement(self.object)
        
        # 3. Возвращаем стандартный ответ
        return super().form_valid(form)

    def _create_notifications_for_announcement(self, announcement):
        """Создаёт уведомления в колокольчик при публикации оповещения"""
        
        # Определяем, кому показывать
        if announcement.scope == 'all':
            # Всем активным сотрудникам
            recipients = Employee.objects.filter(is_active=True)
        elif announcement.scope == 'dept':
            # Только своему отделу (предполагаем, что scope='dept' означает отдел создателя)
            if self.request.user.department:
                recipients = Employee.objects.filter(
                    is_active=True, 
                    department=self.request.user.department
                )
            else:
                recipients = Employee.objects.none() # Если отдела нет, никому
        else:
            recipients = Employee.objects.none()

        # Исключаем самого создателя (зачем ему уведомлять себя?)
        recipients = recipients.exclude(id=self.request.user.id)

        # Готовим список объектов для массового создания (быстро и эффективно)
        notifications = [
            InAppNotification(
                recipient=emp,
                message=f" {announcement.text}",
                notif_type='📢 Оповещение',
                link='/announcements/' # Ссылка ведет на список всех оповещений
            )
            for emp in recipients
        ]

        # Массовая вставка в БД (1 запрос вместо 1000)
        if notifications:
            InAppNotification.objects.bulk_create(notifications)


class AbsenceCreateView(LoginRequiredMixin, CreateView):
    model = AbsenceRecord
    form_class = AbsenceForm
    template_name = 'core/absence_form.html'
    success_url = reverse_lazy('absences')
    
    def get_initial(self):
        initial = super().get_initial()
        reason = self.request.GET.get('reason')
        if reason in ['sick', 'vacation', 'other']:
            initial['reason'] = reason
        return initial
    
    def form_valid(self, form):
        form.instance.employee = self.request.user
        return super().form_valid(form)


class AbsenceListView(LoginRequiredMixin, ListView):
    model = AbsenceRecord
    template_name = 'core/absences.html'
    context_object_name = 'absences'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from datetime import timedelta

        from django.utils import timezone
        
        today = timezone.now().date()
        
        # 🔴 Текущие отсутствия
        current = AbsenceRecord.objects.filter(
            start_dt__lte=today,
            end_dt__gte=today
        ).select_related('employee', 'employee__department')
        
        # 🔮 Будущие отсутствия (14 дней)
        future_qs = AbsenceRecord.objects.filter(
            start_dt__gt=today,
            start_dt__lte=today + timedelta(days=14)
        ).select_related('employee', 'employee__department').order_by('start_dt')
        
        # 📊 Добавляем вычисляемые поля
        future = []
        for absence in future_qs:
            days_until = (absence.start_dt - today).days
            future.append({
                'absence': absence,
                'days_until': days_until,
                'duration_days': (absence.end_dt - absence.start_dt).days + 1 if absence.end_dt else 0
            })
        
        # 📜 Прошедшие (опционально)
        past = AbsenceRecord.objects.filter(
            end_dt__lt=today
        ).select_related('employee', 'employee__department').order_by('-end_dt')[:10]
        
        ctx['current_absences'] = current
        ctx['future_absences'] = future  # ← Список словарей с доп. полями
        ctx['past_absences'] = past
        ctx['today'] = today
        return ctx


class SupportTicketCreateView(LoginRequiredMixin, CreateView):
    model = SupportTicket
    form_class = SupportTicketForm
    template_name = 'core/support_form.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = ProfileForm
    template_name = 'core/profile.html'
    success_url = reverse_lazy('dashboard')
    
    def get_object(self):
        return self.request.user


class TicketListView(LoginRequiredMixin, ListView):
    model = SupportTicket
    template_name = 'core/ticket_list.html'
    context_object_name = 'tickets'
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['adm', 'sup']:
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(author=user)


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = SupportTicket
    template_name = 'core/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        user = self.request.user
        if user.role in ['adm', 'sup']:
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(author=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role in ['adm', 'sup']:
            context['potential_assignees'] = Employee.objects.filter(
                role__in=['adm', 'sup'], is_active=True
            )
        return context

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        reply_text = request.POST.get('reply', '').strip()
        new_status = request.POST.get('status')
        new_assignee_id = request.POST.get('assigned_to')

        if reply_text:
            TicketReply.objects.create(ticket=ticket, author=request.user, message=reply_text)
            if ticket.author != request.user:
                InAppNotification.objects.create(
                    recipient=ticket.author,
                    message=f"💬 Ответ на вашу заявку #{ticket.id}: {reply_text[:40]}...",
                    notif_type='ticket',
                    link=f'/it/tickets/{ticket.id}/'
                )

        if request.user.role in ['adm', 'sup']:
            if new_status and new_status != ticket.status:
                old_status = ticket.get_status_display()
                ticket.status = new_status
                ticket.save(update_fields=['status', 'updated_at'])
                InAppNotification.objects.create(
                    recipient=ticket.author,
                    message=f"📝 Статус заявки #{ticket.id} изменён: {old_status} → {ticket.get_status_display()}",
                    notif_type='ticket',
                    link=f'/it/tickets/{ticket.id}/'
                )
            if new_assignee_id:
                try:
                    assignee = Employee.objects.get(id=int(new_assignee_id), role__in=['adm', 'sup'])
                    if ticket.assigned_to != assignee:
                        ticket.assigned_to = assignee
                        ticket.save(update_fields=['assigned_to', 'updated_at'])
                        InAppNotification.objects.create(
                            recipient=assignee,
                            message=f"📝 Вам назначена заявка #{ticket.id}",
                            notif_type='ticket',
                            link=f'/it/tickets/{ticket.id}/'
                        )
                except Employee.DoesNotExist:
                    pass
        return redirect('ticket_detail', pk=ticket.pk)


class DepartmentsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/departments.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Берём активные подразделения + сразу подтягиваем сотрудников (1 запрос вместо N)
        depts_qs = Department.objects.filter(is_active=True).prefetch_related('employees')
        
        depts = []
        for dept in depts_qs:
            leaders = dept.employees.filter(role=Role.SID, is_active=True)
            count = dept.employees.filter(is_active=True).count()
            candidates = dept.employees.filter(is_active=True).exclude(role=Role.ADM)
            
            depts.append({
                'id': dept.id,
                'code': dept.code,
                'name': dept.name,
                'mis': dept.mis_info,  # Теперь берётся из БД
                'leaders': leaders,
                'count': count,
                'candidates': candidates
            })
            
        context['departments'] = depts
        context['is_manager'] = self.request.user.role in [Role.ADM, Role.SUP]
        return context
    
    def post(self, request, *args, **kwargs):
        if request.user.role not in [Role.ADM, Role.SUP]:
            messages.error(request, "❌ Недостаточно прав")
            return redirect('departments')
            
        dept_id = request.POST.get('dept_id')
        emp_id = request.POST.get('emp_id')
        
        if dept_id and emp_id:
            try:
                dept = Department.objects.get(id=dept_id)
                emp = Employee.objects.get(id=emp_id)
                emp.department = dept
                emp.role = Role.SID
                emp.save()
                messages.success(request, f"✅ {emp.get_full_name()} назначен руководителем {dept.name}")
            except (Department.DoesNotExist, Employee.DoesNotExist):
                messages.error(request, "❌ Ошибка: сотрудник или подразделение не найдены")
                
        return redirect('departments')


class EmployeeManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'core/sup/employee_management.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in [Role.ADM, Role.SUP]:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 👇 Передаём список подразделений (модель, а не choices)
        context['departments'] = Department.objects.filter(is_active=True).order_by('name')
        context['employees'] = Employee.objects.select_related('department').order_by('last_name', 'first_name')
        context['role_choices'] = Role.choices  # Role остаётся TextChoices
        return context
    
    def post(self, request, *args, **kwargs):
        emp_id = request.POST.get('emp_id')
        if emp_id:
            emp = get_object_or_404(Employee, id=emp_id)
            
            # 👇 Обновляем подразделение (по ID)
            dept_id = request.POST.get('dept_id')
            if dept_id:
                emp.department = get_object_or_404(Department, id=dept_id)
            else:
                emp.department = None  # Можно снять привязку
            
            # Обновляем роль
            role = request.POST.get('role')
            if role in [Role.USR, Role.SUP, Role.SID, Role.ADM]:
                emp.role = role
            
            # Обновляем статус активности
            emp.is_active = request.POST.get('is_active') == '1'
            
            emp.save()
            messages.success(request, f"✅ Данные {emp.get_full_name()} обновлены")
        
        return redirect('employee_management')


class VmedaInfoView(LoginRequiredMixin, TemplateView):
    """Usr-2.3: Страница ВМедА (теперь управляемая из БД)"""
    template_name = 'core/vmeda.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем все разделы в правильном порядке
        context['sections'] = VmedaInfoSection.objects.all().order_by('order')
        # Получаем последний загруженный файл-памятку
        brochure = VmedaBrochure.objects.last()
        context['brochure'] = brochure
        return context


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/analytics.html'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.db.models import Q
        from django.utils import timezone
        
        today = timezone.now().date()
        
        # Только текущие отсутствия (активны СЕГОДНЯ)
        current_absences = AbsenceRecord.objects.filter(
            start_dt__lte=today,
            end_dt__gte=today
        )
        
        # 🔥 Фильтрация по текстовым значениям
        stats = {
            'sick': current_absences.filter(reason='sick').count(),
            'vacation': current_absences.filter(reason='vacation').count(),
            'other': current_absences.exclude(
                Q(reason='sick') | Q(reason='vacation')
            ).count(),
            'total': current_absences.count()
        }
        
        ctx['absences_by_reason'] = stats
        
        # Заявки в IT
        ctx['tickets_by_status'] = {
            'new': SupportTicket.objects.filter(status='new').count(),
            'in_progress': SupportTicket.objects.filter(status='in_progress').count(),
            'resolved': SupportTicket.objects.filter(status='resolved').count(),
            'closed': SupportTicket.objects.filter(status='closed').count(),
        }
        
        return ctx
    

# Проверка прав (Админ или Начальник)
class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ['adm', 'sup']

#  Редактирование сотрудника
class EmployeeUpdateView(ManagerRequiredMixin, UpdateView):
    model = Employee
    # Укажите поля, которые можно менять
    fields = [
            'last_name', 
            'first_name', 
            'patronymic', 
            'department', 
            'phone_internal', 
            'phone_external', 
            'office', 
            'email', 
            'is_active'
        ]
    template_name = 'core/employee_form.html' # Создайте этот шаблон или используйте существующий
    
    def get_success_url(self):
        # После сохранения возвращаем в справочник
        return reverse_lazy('directory')

#  Удаление сотрудника
class EmployeeDeleteView(ManagerRequiredMixin, DeleteView):
    model = Employee
    template_name = 'core/employee_confirm_delete.html'
    success_url = reverse_lazy('directory')
# ==================== API Views ====================

@login_required
def search_employees(request):
    """API: Живой поиск сотрудников для шапки (возвращает HTML для HTMX)"""
    from django.db.models import Q
    from django.http import HttpResponse
    
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return HttpResponse('')  # Пустой ответ скроет блок результатов
    
    # 🔥 ИСПРАВЛЕНО: department__name__icontains вместо department__icontains
    employees = Employee.objects.filter(
        is_active=True,
        is_superuser=False
    ).filter(
        Q(first_name__icontains=q) | 
        Q(last_name__icontains=q) | 
        Q(department__name__icontains=q)  # ← Ищем по name в связанной модели
    ).select_related('department')[:8]  # Берём топ-8 результатов
    
    #  Возвращаем HTML, а не JSON (HTMX вставляет ответ напрямую в DOM)
    return render(request, 'core/partials/search_dropdown.html', {'employees': employees})


@login_required
@require_POST
def share_event(request, pk):
    """API: Поделиться событием с коллегой"""
    import logging
    logger = logging.getLogger(__name__)
    
    event = get_object_or_404(CalendarEvent, pk=pk)
    if event.creator != request.user:
        logger.warning(f"User {request.user.id} tried to share event {pk} without permission")
        return JsonResponse({'status': 'error', 'message': 'Нет прав'}, status=403)
    
    target_id = request.POST.get('employee_id', '').strip()
    logger.info(f"Share event {pk}: employee_id='{target_id}'")
    
    if not target_id:
        return JsonResponse({'status': 'error', 'message': 'Не выбран сотрудник'}, status=400)
        
    try:
        target = Employee.objects.get(id=int(target_id), is_active=True)
    except (Employee.DoesNotExist, ValueError) as e:
        logger.warning(f"Employee not found: {target_id}, error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Сотрудник не найден'}, status=404)
        
    if request.user == target:
        return JsonResponse({'status': 'error', 'message': 'Нельзя поделиться с собой'}, status=400)
        
    event.shared_with.add(target)
    InAppNotification.objects.create(
        recipient=target,
        message=f"📅 {request.user.get_full_name()} поделился событием: «{event.title}»",
        notif_type='event',
        link='/calendar/'
    )
    logger.info(f"Event {pk} shared with user {target.id}")
    return JsonResponse({'status': 'ok'})


@login_required
def api_search(request):
    """API: Живой поиск (HTML для шапки, JSON для модалок)"""
    from django.db.models import Q
    from django.http import HttpResponse, JsonResponse
    
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        if request.GET.get('format') == 'json':
            return JsonResponse([], safe=False)
        return HttpResponse('')
    
    # Python-фильтрация (обход SQLite + кириллица)
    employees = Employee.objects.filter(is_active=True, is_superuser=False).select_related('department')
    q_lower = q.lower()
    results = [
        emp for emp in employees
        if q_lower in emp.last_name.lower() or
           q_lower in emp.first_name.lower() or
           (emp.department and q_lower in emp.department.name.lower())
    ][:8]
    
    # 🔥 Если запрошен JSON (календарь) → отдаём JSON
    if request.GET.get('format') == 'json':
        data = []
        for emp in results:
            data.append({
                'id': emp.id,
                'last_name': emp.last_name,
                'first_name': emp.first_name,
                'patronymic': emp.patronymic or '',
                'department': emp.department.name if emp.department else ''
            })
        return JsonResponse(data, safe=False)
    
    # 🔥 Иначе (шапка сайта) → отдаём HTML для HTMX
    return render(request, 'core/partials/search_dropdown.html', {'employees': results})


@login_required
def notifications_list(request):
    """Страница всех уведомлений"""
    notifs = InAppNotification.objects.filter(recipient=request.user).order_by('-created_at')
    notifs.update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifs})


@login_required
def mark_notification_read(request, pk):
    """Пометить одно уведомление как прочитанное (старый эндпоинт)"""
    notif = get_object_or_404(InAppNotification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def api_notifications_list(request):
    """API: Последние 10 уведомлений + счётчик непрочитанных"""
    unread_count = InAppNotification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    notifs = InAppNotification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:10]
    
    data = [{
        'id': n.id,
        'message': n.message,
        'type': n.get_notif_type_display(),
        'link': n.link,
        'is_read': n.is_read,
        'created': n.created_at.strftime('%d.%m %H:%M')
    } for n in notifs]
    return JsonResponse({'notifications': data, 'unread_count': unread_count})


@login_required
@require_POST
def api_mark_notification_read(request, pk):
    """API: Пометить одно уведомление как прочитанное"""
    try:
        notif = InAppNotification.objects.get(pk=pk, recipient=request.user)
        notif.is_read = True
        notif.save()
        return JsonResponse({'status': 'ok'})
    except InAppNotification.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


@login_required
@require_POST
def api_mark_all_read(request):
    """API: Пометить ВСЕ уведомления как прочитанные"""
    InAppNotification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)
    return JsonResponse({'status': 'ok'})


@login_required
def api_notifications_count(request):
    """API: Только счётчик непрочитанных (для polling)"""
    count = InAppNotification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    return JsonResponse({'count': count})
