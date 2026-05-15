FROM python:3.12-slim

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles media data
RUN python manage.py collectstatic --noinput --clear

RUN echo "0 9 * * * root cd /app && /usr/local/bin/python manage.py check_upcoming_events >> /var/log/reminders.log 2>&1" > /etc/cron.d/mit-reminders
RUN chmod 0644 /etc/cron.d/mit-reminders
RUN crontab /etc/cron.d/mit-reminders

EXPOSE 8000

CMD ["sh", "-c", "cron && python -m gunicorn --bind 0.0.0.0:8000 --workers 3 --access-logfile - --error-logfile - med_it_portal.wsgi:application"]