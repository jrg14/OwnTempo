from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.middleware.csrf import CsrfViewMiddleware, get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CurrentUserSerializer


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


def enforce_csrf(request):
    check = CSRFCheck(lambda _request: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})

    if reason:
        raise PermissionDenied("La comprobación de seguridad CSRF ha fallado.")


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrf_token": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    enforce_csrf(request)

    username = request.data.get("username")
    password = request.data.get("password")

    if not isinstance(username, str) or not username.strip():
        return Response(
            {"detail": "Introduce el nombre de usuario."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(password, str) or not password:
        return Response(
            {"detail": "Introduce la contraseña."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    username = username.strip()
    user = authenticate(request=request, username=username, password=password)

    if user is None:
        user_model = get_user_model()
        account = user_model.objects.filter(username=username).only("is_active").first()
        detail = (
            "La cuenta está desactivada. Contacta con el administrador."
            if account is not None and not account.is_active
            else "El nombre de usuario o la contraseña no son correctos."
        )
        return Response({"detail": detail}, status=status.HTTP_401_UNAUTHORIZED)

    django_login(request, user)
    return Response({"user": CurrentUserSerializer(user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def logout(request):
    enforce_csrf(request)
    django_logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)

    def patch(self, request):
        serializer = CurrentUserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
