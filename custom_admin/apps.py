from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CustomAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'custom_admin'
    verbose_name = _('Custom Admin')

    def ready(self):
        import custom_admin.middleware
        
        # Import signals to register them
        try:
            import custom_admin.signals  # noqa F401
        except ImportError:
            # Skip if signals.py doesn't exist or has errors
            pass
