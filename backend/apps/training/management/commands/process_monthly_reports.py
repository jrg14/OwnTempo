import time

from django.core.management.base import BaseCommand

from apps.training.monthly_reports import (
    claim_pending_report,
    generate_monthly_report,
    recover_stale_reports,
)


class Command(BaseCommand):
    help = "Procesa la cola de informes mensuales de entrenamiento."

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
        recovered = recover_stale_reports()
        if recovered:
            self.stdout.write(f"Informes recuperados tras una interrupción: {recovered}")
        while True:
            report_id = claim_pending_report()
            if report_id is not None:
                report = generate_monthly_report(report_id)
                self.stdout.write(
                    f"Informe {report.id}: {report.status}"
                )
                continue

            if not options["watch"]:
                break
            time.sleep(max(options["interval"], 0.5))

