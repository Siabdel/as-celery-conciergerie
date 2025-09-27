
# core/management/commands/create_owner_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Agency, OwnerProfile

User = get_user_model()

class Command(BaseCommand):
    help = "Convertit les utilisateurs existants en OwnerProfile rattachés à l’agence par défaut"

    def add_arguments(self, parser):
        parser.add_argument("--agency", type=str, help="Nom de l’agence", default="Default Agency")

    def handle(self, *args, **options):
        agency, _ = Agency.objects.get_or_create(name=options["agency"], slug="default")
        created = 0
        for u in User.objects.filter(owner__isnull=True):
            OwnerProfile.objects.create(user=u, agency=agency)
            created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} OwnerProfile créés pour l’agence «{agency}»"))