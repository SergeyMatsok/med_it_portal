from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Role(models.TextChoices):
    ADM = 'adm', 'Администратор'
    SUP = 'sup', 'Начальник'
    DEP = 'dep', 'Заместитель начальника'
    SID = 'sid', 'Руководитель направления'
    DOC = 'doc_clerk', 'Делопроизводитель' 
    USR = 'usr', 'Сотрудник'
    

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    code = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Код (emias, parus, it_dev...)")
    mis_info = models.TextField(blank=True, verbose_name="Информация о МИС / Задачи")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
        ordering = ['name']

    def __str__(self):
        return self.name



class Employee(AbstractUser):
    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    patronymic = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    
    #  ИСПРАВЛЕНО: max_length=20, чтобы влезло 'doc_clerk' (было 3)
    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.USR, 
        verbose_name='Роль'
    )
    
    department = models.ForeignKey(
        Department, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        verbose_name='Подразделение', 
        related_name='employees'
    )
    office = models.CharField(max_length=50, blank=True, verbose_name='Кабинет')
    phone_external = models.CharField(max_length=20, blank=True, verbose_name='Внешний телефон')
    phone_internal = models.CharField(max_length=20, blank=True, verbose_name='Внутренний телефон')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts) or self.username

    def get_full_name_with_patronymic(self):
        if self.patronymic:
            return f"{self.last_name} {self.first_name} {self.patronymic}"
        return self.get_full_name()

    # Свойства для быстрой проверки ролей
    @property
    def is_admin(self): return self.role == Role.ADM
    
    @property
    def is_sup(self): return self.role == Role.SUP
    
    @property
    def is_sid(self): return self.role == Role.SID
    
    #  ДОБАВЛЕНО: свойство для Делопроизводителя
    @property
    def is_doc(self): return self.role == Role.DOC

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
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Подразделение')
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

    @property
    def duration_days(self):
        """Возвращает количество дней отсутствия"""
        if self.start_dt and self.end_dt:
            delta = self.end_dt - self.start_dt
            return delta.days + 1  # +1 чтобы включить оба дня
        return 0
    
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
    

class VmedaInfoSection(models.Model):
    """Блок информации на странице ВМедА"""
    title = models.CharField(max_length=100, verbose_name="Заголовок раздела")
    content = models.TextField(verbose_name="Текст раздела (поддерживает переносы строк)")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")
    
    class Meta:
        verbose_name = 'Раздел справки ВМедА'
        verbose_name_plural = 'Разделы справки ВМедА'
        ordering = ['order']

    def __str__(self):
        return self.title

class VmedaBrochure(models.Model):
    """Модель для хранения файла-памятки"""
    title = models.CharField(max_length=100, default="Памятка сотрудника", verbose_name="Название")
    file = models.FileField(upload_to='brochures/', verbose_name="PDF файл")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = 'Файл-памятка'
        verbose_name_plural = 'Файлы-памятки'

    def __str__(self):
        return f"Памятка: {self.title}"
    

class Report(models.Model):
    title = models.CharField("Название документа", max_length=255)
    file = models.FileField("Файл", upload_to='reports/%Y/%m/')
    description = models.TextField("Описание", blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        editable=False,
        verbose_name="Автор"
    )
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Отдел"
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Рапорт"
        verbose_name_plural = "Рапорты"

    def __str__(self):
        return self.title

    @property
    def file_extension(self):
        return self.file.name.split('.')[-1].lower() if self.file else ''




class VmedaLink(models.Model):
    title = models.CharField("Название ссылки", max_length=200)
    url = models.URLField("Адрес ссылки (URL)")
    description = models.TextField("Описание (появится при раскрытии)", blank=True)
    order = models.PositiveIntegerField("Порядок сортировки", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = 'Полезная ссылка'
        verbose_name_plural = 'Полезные ссылки'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title