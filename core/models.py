from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.TextChoices):
    ADM = 'adm', 'Администратор'
    SUP = 'sup', 'Начальник'
    SID = 'sid', 'Руководитель подразделения'
    USR = 'usr', 'Сотрудник'

class Department(models.TextChoices):
    EMIAS = 'emias', 'ЕМИАС'
    PARUS = 'parus', 'ПАРУС'
    PACS = 'pacs', 'ПАКС'
    LIS = 'lis', 'ЛИС'
    IT_DEPT = 'it_dev', 'Отдел разработки'
    OTHER = 'other', 'Прочее'

class Employee(AbstractUser):
    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    role = models.CharField(max_length=3, choices=Role.choices, default=Role.USR, verbose_name='Роль')
    department = models.CharField(max_length=10, choices=Department.choices, blank=True, default=Department.OTHER, verbose_name='Подразделение')
    office = models.CharField(max_length=50, blank=True, verbose_name='Кабинет')
    phone_external = models.CharField(max_length=20, blank=True, verbose_name='Внешний телефон')
    phone_internal = models.CharField(max_length=20, blank=True, verbose_name='Внутренний телефон')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self): return self.role == Role.ADM
    @property
    def is_sup(self): return self.role == Role.SUP
    @property
    def is_sid(self): return self.role == Role.SID

class CalendarEvent(models.Model):
    VISIBILITY = [('private', 'Только я'), ('dept', 'Подразделение'), ('all', 'Весь отдел')]
    
    class Meta:
        verbose_name = 'Событие календаря'
        verbose_name_plural = 'События календаря'
        ordering = ['start_dt']

    title = models.CharField(max_length=200, verbose_name='Название события')
    description = models.TextField(blank=True, verbose_name='Описание')
    start_dt = models.DateTimeField(verbose_name='Дата и время начала')
    end_dt = models.DateTimeField(null=True, blank=True, verbose_name='Дата и время окончания')
    creator = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='created_events', verbose_name='Создатель')
    visibility = models.CharField(max_length=10, choices=VISIBILITY, default='private', verbose_name='Видимость')
    notify_before = models.DurationField(null=True, blank=True, help_text="Например: 1 day", verbose_name='Напоминать за')
    shared_with = models.ManyToManyField(Employee, related_name='shared_events', blank=True, verbose_name='Поделиться с')

    def __str__(self):
        return f"{self.title} ({self.start_dt.date()})"

class Announcement(models.Model):
    SCOPE = [('all', 'Весь отдел'), ('dept', 'Подразделение')]
    
    class Meta:
        verbose_name = 'Оповещение'
        verbose_name_plural = 'Оповещения'
        ordering = ['-created_at']

    text = models.TextField(verbose_name='Текст оповещения')
    scope = models.CharField(max_length=10, choices=SCOPE, default='all', verbose_name='Область рассылки')
    department = models.CharField(max_length=10, choices=Department.choices, blank=True, verbose_name='Подразделение')
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return self.text[:50] + ('...' if len(self.text) > 50 else '')

class AbsenceRecord(models.Model):
    REASONS = [('vacation', 'Отпуск'), ('sick', 'Болезнь'), ('other', 'Другая причина')]
    
    class Meta:
        verbose_name = 'Запись об отсутствии'
        verbose_name_plural = 'Записи об отсутствии'
        ordering = ['-start_dt']

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Сотрудник')
    reason = models.CharField(max_length=10, choices=REASONS, verbose_name='Причина')
    custom_reason = models.CharField(max_length=150, blank=True, verbose_name='Другая причина (текст)')
    start_dt = models.DateField(verbose_name='Дата начала')
    end_dt = models.DateField(verbose_name='Дата окончания')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f"{self.employee} ({self.get_reason_display()})"

class SupportTicket(models.Model):
    class Meta:
        verbose_name = 'Заявка в IT'
        verbose_name_plural = 'Заявки в IT'
        ordering = ['-created_at']

    author = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Автор')
    message = models.TextField(verbose_name='Сообщение')
    is_resolved = models.BooleanField(default=False, verbose_name='Решено')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f"Заявка от {self.author} ({self.created_at.date()})"

class InAppNotification(models.Model):
    TYPES = [('info', 'ℹ️ Инфо'), ('event', '📅 Событие'), ('absence', '📋 Отсутствие'), ('ticket', '🆘 Тикет')]
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    recipient = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Получатель')
    message = models.TextField(verbose_name='Сообщение')
    notif_type = models.CharField(max_length=10, choices=TYPES, default='info', verbose_name='Тип')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    link = models.CharField(max_length=200, blank=True, help_text="URL для перехода", verbose_name='Ссылка')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f"[{self.recipient}] {self.message[:30]}"
    

class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('new', '🆕 Новая'),
        ('in_progress', '🔧 В работе'),
        ('resolved', '✅ Решена'),
        ('closed', '📁 Закрыта')
    ]
    author = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Автор")
    message = models.TextField(verbose_name="Сообщение")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='assigned_tickets', verbose_name="Исполнитель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = 'Заявка в IT'
        verbose_name_plural = 'Заявки в IT'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка #{self.id} от {self.author} ({self.get_status_display()})"

class TicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies', verbose_name="Заявка")
    author = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Автор ответа")
    message = models.TextField(verbose_name="Ответ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    class Meta:
        verbose_name = 'Ответ на заявку'
        verbose_name_plural = 'Ответы на заявки'
        ordering = ['created_at']

    def __str__(self):
        return f"Ответ от {self.author} к заявке #{self.ticket.id}"