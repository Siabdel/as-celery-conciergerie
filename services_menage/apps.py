from django.apps import AppConfig


class ServicesMenageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "services_menage"

    def ready(self):
        ## import services_menage.signals  # remplacez 'your_app_name' par le nom réel de votre application
        pass # éviter l'import circulaire
    

