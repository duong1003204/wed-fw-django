from django.apps import AppConfig


class DonhangConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donhang'
    
    def ready(self):
        import donhang.signals  # Đăng ký signals