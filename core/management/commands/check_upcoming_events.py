from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from core.models import CalendarEvent, InAppNotification

class Command(BaseCommand):
    help = 'Отправляет напоминания о событиях на завтра'

    def handle(self, *args, **options):
        now = timezone.now()
        tomorrow_date = (now + timedelta(days=1)).date()
        notified = 0

        # События, которые начнутся завтра
        events = CalendarEvent.objects.filter(
            start_dt__date=tomorrow_date
        ).select_related('creator').prefetch_related('shared_with')

        for event in events:
            recipients = [event.creator] + list(event.shared_with.all())
            
            for recipient in recipients:
                # Защита от дублей: проверяем, не отправляли ли напоминание сегодня
                is_sent = InAppNotification.objects.filter(
                    recipient=recipient,
                    notif_type='event',
                    created_at__date=now.date(),
                    message__contains=event.title
                ).exists()

                if not is_sent:
                    InAppNotification.objects.create(
                        recipient=recipient,
                        message=f"📅 Напоминание: завтра событие «{event.title}» в {event.start_dt.strftime('%H:%M')}",
                        notif_type='event',
                        link='/calendar/'
                    )
                    notified += 1

        self.stdout.write(self.style.SUCCESS(f' Отправлено напоминаний: {notified}'))