# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AbsenceRecord, InAppNotification, Employee

@receiver(post_save, sender=AbsenceRecord)
def auto_notify_absence(sender, instance, created, **kwargs):
    """
    Автоматически уведомляет коллег при создании записи об отсутствии.
    Срабатывает только при первом сохранении (created=True).
    """
    if not created:
        return

    # Формируем текст уведомления
    reason_text = instance.get_reason_display()
    if instance.reason == 'other' and instance.custom_reason.strip():
        reason_text = instance.custom_reason.strip()
        
    msg = f"📋 {instance.employee.get_full_name()} отсутствует: {reason_text} ({instance.start_dt} — {instance.end_dt})"

    # Определяем аудиторию: подразделение сотрудника. 
    # Если поле department пустое -> уведомляем всех активных.
    dept = instance.employee.department
    qs = Employee.objects.filter(is_active=True)
    if dept:
        qs = qs.filter(department=dept)
        
    # Исключаем самого сотрудника
    recipients = qs.exclude(id=instance.employee.id)

    # Создаем уведомления оптом (быстрее, чем цикл с save())
    notifications = [
        InAppNotification(
            recipient=emp,
            message=msg,
            notif_type='absence',
            link='/absences/'
        )
        for emp in recipients
    ]
    
    InAppNotification.objects.bulk_create(notifications)