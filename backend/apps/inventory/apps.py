from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventory"
    verbose_name = "库存"
    label = "inventory"

    def ready(self):
        # 导入 signal 处理器，确保 Django 启动时注册
        import apps.inventory.signals  # noqa: F401
