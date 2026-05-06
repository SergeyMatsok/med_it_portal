from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Employee, CalendarEvent, Announcement, AbsenceRecord, SupportTicket, InAppNotification, Role
from .forms import (EmployeeRegistrationForm, ProfileForm, CalendarEventForm, 
                    AnnouncementForm, AbsenceForm, SupportTicketForm)
from .mixins import RoleRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import SupportTicket, TicketReply


class CustomLoginView(LoginView):
    template_name = 'core/login.html'

class RegisterView(CreateView):
    model = Employee
    form_class = EmployeeRegistrationForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('login')

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['unread_notifs'] = InAppNotification.objects.filter(recipient=self.request.user, is_read=False).count()
        ctx['upcoming_events'] = CalendarEvent.objects.filter(
            Q(creator=self.request.user) | 
            Q(visibility='dept', creator__department=self.request.user.department) |
            Q(visibility='all')
        ).filter(start_dt__gte=timezone.now()).order_by('start_dt')[:5]
        return ctx

class EmployeeDirectoryView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'core/directory.html'
    context_object_name = 'employees'
    def get_queryset(self):
        qs = Employee.objects.filter(is_active=True)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(department__icontains=q))
        return qs.order_by('last_name', 'first_name')

class CalendarView(LoginRequiredMixin, ListView):
    model = CalendarEvent
    template_name = 'core/calendar.html'
    context_object_name = 'events'
    def get_queryset(self):
        user = self.request.user
        return CalendarEvent.objects.filter(
            Q(creator=user) |
            Q(visibility='dept', creator__department=user.department) |
            Q(visibility='all')
        ).filter(start_dt__gte=timezone.now()).order_by('start_dt')

class EventCreateView(LoginRequiredMixin, CreateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = 'core/event_form.html'
    success_url = reverse_lazy('calendar')
    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

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
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class AbsenceCreateView(LoginRequiredMixin, CreateView):
    model = AbsenceRecord
    form_class = AbsenceForm
    template_name = 'core/absence_form.html'
    success_url = reverse_lazy('absences')
    def form_valid(self, form):
        form.instance.employee = self.request.user
        return super().form_valid(form)

class AbsenceListView(LoginRequiredMixin, ListView):
    model = AbsenceRecord
    template_name = 'core/absences.html'
    context_object_name = 'absences'
    def get_queryset(self):
        today = timezone.now().date()
        return AbsenceRecord.objects.filter(start_dt__lte=today, end_dt__gte=today).select_related('employee')

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
        # Передаём список Adm/Sup в шаблон для выпадающего списка
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

        # 1. Обработка ответа
        if reply_text:
            TicketReply.objects.create(ticket=ticket, author=request.user, message=reply_text)
            if ticket.author != request.user:
                InAppNotification.objects.create(
                    recipient=ticket.author,
                    message=f"💬 Ответ на вашу заявку #{ticket.id}: {reply_text[:40]}...",
                    notif_type='ticket',
                    link=f'/it/tickets/{ticket.id}/'
                )

        # 2. Обработка действий Adm/Sup
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

@login_required
def search_employees(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    users = Employee.objects.filter(is_active=True).filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(department__icontains=q)
    ).values('id', 'first_name', 'last_name', 'department')[:10]
    return JsonResponse(list(users), safe=False)

@login_required
@require_POST
def share_event(request, pk):
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
#  Уведомления: список и пометка прочитанным
@login_required
def notifications_list(request):
    notifs = InAppNotification.objects.filter(recipient=request.user).order_by('-created_at')
    notifs.update(is_read=True)  # помечаем все как прочитанные при открытии
    return render(request, 'core/notifications.html', {'notifications': notifs})

@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(InAppNotification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

