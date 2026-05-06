from celery import shared_task
from django.utils import timezone
from .models import CalendarEvent, InAppNotification

@shared_task
def send_event_reminders():
    tomorrow = timezone.now() + timezone.timedelta(days=1)
    events = CalendarEvent.objects.filter(
        start_dt__date=tomorrow.date(),
        notify_before__isnull=False
    )
    for ev in events:
        InAppNotification.objects.create(
            recipient=ev.creator,
            message=f" Завтра в {ev.start_dt.time().strftime('%H:%M')}: {ev.title}"
        )