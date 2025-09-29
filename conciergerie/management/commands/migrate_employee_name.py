# staff/management/commands/migrate_employee_name.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from staff.models import Employee

User = get_user_model()


class Command(BaseCommand):
    help = "Copie Employee.name vers User.first_name/last_name puis supprime le champ name"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="N’applique pas la suppression du champ")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated = 0
        errors = 0

        for emp in Employee.objects.all():
            try:
                parts = emp.name.split(" ", 1)
                emp.user.first_name = parts[0][:30]
                emp.user.last_name = parts[1][:30] if len(parts) > 1 else ""
                emp.user.save(update_fields=["first_name", "last_name"])
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"{emp.user.username} → {emp.user.get_full_name()}"))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"{emp.user.username} : {e}"))

        self.stdout.write(self.style.WARNING(f"Copiés : {updated}  –  Erreurs : {errors}"))

        if not dry_run:
            # Suppression physique du champ
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE staff_employee DROP COLUMN IF EXISTS name;")
            self.stdout.write(self.style.SUCCESS("Champ 'name' supprimé dans la table staff_employee."))
        else:
            self.stdout.write(self.style.WARNING("Dry-run : suppression non effectuée."))