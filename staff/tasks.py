# staff/tasks.py (corrigé)
from conciergerie.models import ServiceTask
from staff.models import Employee, PayrollEntry

@shared_task
def compute_daily_payroll(target_date=None):
    """
    Calcule la paie quotidienne sur la base des tâches terminées (ServiceTask)
    """
    if target_date is None:
        target_date = timezone.now().date()

    employees = Employee.objects.filter(active=True).select_related("contract")
    results = []
    for emp in employees:
        contract = getattr(emp, "contract", None)
        if not contract or not contract.active:
            continue

        completed_tasks = ServiceTask.objects.filter(
            employee=emp,
            completed=True,
            start_time__date=target_date
        ).count()

        total = (contract.daily_salary or Decimal("0")) * completed_tasks

        payroll, created = PayrollEntry.objects.update_or_create(
            employee=emp,
            date=target_date,
            defaults={
                "shifts_worked": completed_tasks,
                "total_salary": total
            }
        )
        results.append({
            "employee": emp.id,
            "date": str(target_date),
            "tasks": completed_tasks,
            "total_salary": str(total)
        })
    return results



@shared_task
def generate_service_tasks_for_reservation(reservation_id):
    from conciergerie.models import Reservation, ServiceTask
    from staff.models import Employee

    try:
        res = Reservation.objects.get(pk=reservation_id)
    except Reservation.DoesNotExist:
        return {"error": "Reservation not found", "id": reservation_id}

    # sélection d’un agent disponible
    cleaner = Employee.objects.filter(
        agency=res.agency, role=Employee.Role.CLEANER, active=True
    ).first()

    start = res.check_out - timezone.timedelta(hours=1)
    end = res.check_out + timezone.timedelta(hours=1)

    task = ServiceTask.objects.create(
        agency=res.agency,
        property=res.property,
        reservation=res,
        employee=cleaner,
        task_type=ServiceTask.TaskType.CLEANING,
        start_time=start,
        end_time=end
    )
    return {"task_id": task.id, "employee": cleaner.id if cleaner else None}
