from django.apps import AppConfig


class PeriodsConfig(AppConfig):
    name = 'periods'

    def ready(self):
        import periods.signals as _  # noqa
