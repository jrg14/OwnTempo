import time

from django.core.management.base import BaseCommand

from apps.expenses.monthly_reports import (
    claim_pending_report as claim_pending_expense_report,
    generate_monthly_report as generate_expense_report,
    recover_stale_reports as recover_stale_expense_reports,
)
from apps.training.monthly_reports import (
    claim_pending_report as claim_pending_training_report,
    generate_monthly_report as generate_training_report,
    recover_stale_reports as recover_stale_training_reports,
)


class Command(BaseCommand):
    help = "Procesa las colas de informes mensuales de entrenamiento y gastos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--watch",
            action="store_true",
            help="Mantiene el proceso esperando nuevos informes.",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=3,
            help="Segundos entre consultas cuando se usa --watch.",
        )

    def handle(self, *args, **options):
        recovered = recover_stale_training_reports() + recover_stale_expense_reports()
        if recovered:
            self.stdout.write(f"Informes recuperados tras una interrupción: {recovered}")
        while True:
            report_id = claim_pending_training_report()
            if report_id is not None:
                report = generate_training_report(report_id)
                self.stdout.write(
                    f"Informe de entrenamiento {report.id}: {report.status}"
                )
                continue

            report_id = claim_pending_expense_report()
            if report_id is not None:
                report = generate_expense_report(report_id)
                self.stdout.write(f"Informe de gastos {report.id}: {report.status}")
                continue

            if not options["watch"]:
                break
            time.sleep(max(options["interval"], 0.5))

