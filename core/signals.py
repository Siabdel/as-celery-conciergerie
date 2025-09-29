# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from staff.models import Employee
from core.models import CustomCalendar, OwnerProfile

@receiver(post_save, sender=Employee)
def create_employee_calendar(sender, instance, created, **kwargs):
    if created:
        CustomCalendar.objects.get_or_create(
            name=f"Cal {instance.user.get_full_name()}",
            slug=f"emp-{instance.user.id}",
        )


@receiver(post_save, sender=OwnerProfile)
def create_owner_calendar(sender, instance, created, **kwargs):
    if created:
        CustomCalendar.objects.get_or_create(
            name=f"Cal Owner {instance.user.get_full_name()}",
            slug=f"own-{instance.user.id}",
        )