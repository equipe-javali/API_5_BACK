from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, status
from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework.permissions import AllowAny
from .models import Usuario
from .serializers import UsuarioSerializer

class UsuarioCreateView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Autentica o usuário e gera o JWT.
    """
    email = request.data.get("email")
    password = request.data.get("senha")

    try:
        user = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return Response({
            "msg": "Email não cadastrado."
        }, status=status.HTTP_404_NOT_FOUND)

    if user.check_password(password):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "access_token": access_token
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "msg": "Credenciais inválidas"
        }, status=status.HTTP_401_UNAUTHORIZED)