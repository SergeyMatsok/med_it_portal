# core/apps.py
from django.apps import AppConfig

# core/apps.py
from django.apps import AppConfig
from django.db.backends.signals import connection_created

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        def fix_sqlite_cyrillic(sender, connection, **kwargs):
            # Применяем PRAGMA только для SQLite
            if connection.vendor == 'sqlite':
                with connection.cursor() as cursor:
                    cursor.execute('PRAGMA case_sensitive_like = OFF;')
        
        connection_created.connect(fix_sqlite_cyrillic)