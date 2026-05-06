# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import (Employee, CalendarEvent, Announcement, 
#                      AbsenceRecord, SupportTicket, InAppNotification, TicketReply)


# @admin.register(Employee)
# class EmployeeAdmin(UserAdmin):
#     list_display = ('username', 'get_full_name', 'role', 'department', 'is_active')
#     list_filter = ('role', 'department', 'is_active')
#     search_fields = ('first_name', 'last_name', 'username')
#     fieldsets = (
#         (None, {'fields': ('username', 'password')}),
#         ('Личные данные', {'fields': ('first_name', 'last_name', 'email', 'birth_date', 'office', 'phone_external', 'phone_internal', 'department')}),
#         ('Роли и доступ', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#     )
#     add_fieldsets = (
#         (None, {'fields': ('username', 'password1', 'password2')}),
#         ('Данные', {'fields': ('first_name', 'last_name', 'email', 'role', 'department')}),
#     )

# @admin.register(CalendarEvent)
# class CalendarEventAdmin(admin.ModelAdmin):
#     list_display = ('title', 'creator', 'start_dt', 'visibility')
#     list_filter = ('visibility', 'creator__department')

# @admin.register(Announcement)
# class AnnouncementAdmin(admin.ModelAdmin):
#     list_display = ('text_preview', 'scope', 'department', 'created_by', 'created_at')
#     list_filter = ('scope', 'department')
#     def text_preview(self, obj): return obj.text[:50] + ('...' if len(obj.text)>50 else '')

# class TicketReplyInline(admin.TabularInline):
#     model = TicketReply
#     extra = 0
#     readonly_fields = ('author', 'created_at', 'message')
#     can_delete = False

# @admin.register(SupportTicket)
# class SupportTicketAdmin(admin.ModelAdmin):
#     list_display = ('id', 'author', 'status', 'assigned_to', 'created_at')
#     list_filter = ('status', 'author__department')
#     search_fields = ('message', 'author__first_name', 'author__last_name')
#     inlines = [TicketReplyInline]
#     readonly_fields = ('created_at', 'updated_at')

# @admin.register(TicketReply)
# class TicketReplyAdmin(admin.ModelAdmin):
#     list_display = ('ticket', 'author', 'created_at', 'message')
#     list_filter = ('author__department',)
#     search_fields = ('message',)

# admin.site.register(AbsenceRecord)
# admin.site.register(SupportTicket)
# admin.site.register(InAppNotification)

# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Employee, CalendarEvent, Announcement, 
    AbsenceRecord, SupportTicket, TicketReply, InAppNotification
)

@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('first_name', 'last_name', 'username')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'email', 'birth_date', 'office', 'phone_external', 'phone_internal', 'department')}),
        ('Роли и доступ', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        ('Данные', {'fields': ('first_name', 'last_name', 'email', 'role', 'department')}),
    )

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'start_dt', 'visibility')
    list_filter = ('visibility', 'creator__department')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'scope', 'department', 'created_by', 'created_at')
    list_filter = ('scope', 'department')
    def text_preview(self, obj): 
        return obj.text[:50] + ('...' if len(obj.text)>50 else '')

@admin.register(AbsenceRecord)
class AbsenceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reason', 'start_dt', 'end_dt')
    list_filter = ('reason',)

# class TicketReplyInline(admin.TabularInline):
#     model = TicketReply
#     extra = 0
#     readonly_fields = ('author', 'created_at', 'message')
#     can_delete = False

# @admin.register(SupportTicket)
# class SupportTicketAdmin(admin.ModelAdmin):
#     list_display = ('id', 'author', 'status', 'assigned_to', 'created_at')
#     list_filter = ('status', 'author__department')
#     search_fields = ('message', 'author__first_name', 'author__last_name')
#     inlines = [TicketReplyInline]
#     readonly_fields = ('created_at', 'updated_at')

class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1  # 👈 Показывать 1 пустую форму для нового ответа
    fields = ('author', 'message', 'created_at')
    readonly_fields = ('author', 'created_at')  # 👈 message НЕ в readonly, чтобы можно было писать
    can_delete = False

    def get_formset(self, request, obj=None, **kwargs):
        # При создании нового тикета — не показывать inline (нечего комментировать)
        if obj is None or obj.pk is None:
            self.extra = 0
            self.max_num = 0
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Автоматически подставлять текущего админа как автора ответа
        if db_field.name == "author":
            kwargs["initial"] = request.user.id
            kwargs["disabled"] = True  # Чтобы нельзя было подделать автора
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'status', 'assigned_to', 'created_at', 'updated_at')
    list_filter = ('status', 'author__department', 'assigned_to')
    search_fields = ('message', 'author__first_name', 'author__last_name', 'replies__message')
    inlines = [TicketReplyInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Информация', {'fields': ('author', 'message', 'status', 'assigned_to')}),
        ('Мета', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def save_formset(self, request, form, formset, change):
        """
        Автоматически проставляет автора и создаёт уведомления при добавлении ответа в админке.
        """
        instances = formset.save(commit=False)
        for instance in instances:
            if instance.pk is None:  # Новый ответ
                instance.author = request.user
                instance.save()
                # Уведомление автору тикета, если отвечает не он
                if instance.ticket.author != request.user:
                    from core.models import InAppNotification
                    InAppNotification.objects.create(
                        recipient=instance.ticket.author,
                        message=f"💬 Ответ админа на заявку #{instance.ticket.id}: {instance.message[:40]}...",
                        notif_type='ticket',
                        link=f'/it/tickets/{instance.ticket.id}/'
                    )
        formset.save_m2m()
        
@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'created_at', 'message')
    list_filter = ('author__department',)
    search_fields = ('message',)

@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notif_type', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'notif_type', 'recipient__department')