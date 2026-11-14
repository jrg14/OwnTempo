from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Report whether the API and its database dependency are available."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        database_status = "ok"
        response_status = status.HTTP_200_OK

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            database_status = "unavailable"
            response_status = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(
            {
                "status": "ok" if response_status == status.HTTP_200_OK else "degraded",
                "service": "owntempo-api",
                "checks": {
                    "django": "ok",
                    "database": database_status,
                },
                "timestamp": timezone.now(),
            },
            status=response_status,
        )

