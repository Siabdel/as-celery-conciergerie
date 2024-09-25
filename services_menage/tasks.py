
from celery import shared_task
from .models import Reservation, CleaningTask

@shared_task
def schedule_cleaning(reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    cleaning_time = reservation.check_out + timezone.timedelta(hours=2)
    available_employee = find_available_employee(cleaning_time)
    
    if available_employee:
        cleaning_task = CleaningTask.objects.create(
            reservation=reservation,
            employee=available_employee,
            scheduled_time=cleaning_time
        )
        
        Event.objects.create(
            start=cleaning_time,
            end=cleaning_time + timezone.timedelta(hours=2),
            title=f"Nettoyage: Chambre de {reservation.client}",
            calendar=available_employee.calendar
        )