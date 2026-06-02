from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (AbsenceRecord, Announcement, CalendarEvent, Department,
                     Employee, InAppNotification, SupportTicket, TicketReply,
                     VmedaBrochure, VmedaInfoSection, VmedaLink)


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('first_name', 'last_name', 'username')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональные данные', {'fields': ('first_name', 'last_name', 'patronymic', 'email', 'birth_date')}),
        ('Работа', {'fields': ('department', 'role', 'office', 'phone_external', 'phone_internal')}), 
        ('Статус', {'fields': ('is_active',)}),
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

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'employee_count')
    list_editable = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('name',)

    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = 'Сотрудников'
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

@admin.register(VmedaInfoSection)
class VmedaInfoSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'content_preview')
    list_editable = ('order',)
    search_fields = ('title',)
    ordering = ('order',)

    def content_preview(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = 'Текст'

@admin.register(VmedaBrochure)
class VmedaBrochureAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'file_link')

    def file_link(self, obj):
        if obj.file:
            return f'<a href="{obj.file.url}" target="_blank">Скачать текущий</a>'
        return '—'
    file_link.allow_tags = True


@admin.register(VmedaLink)
class VmedaLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'url')