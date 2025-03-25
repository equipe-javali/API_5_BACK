from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Usuario
from .serializers import UsuarioSerializer

class UsuarioCreateView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny] # Não precisa estar autenticado
    
    def post(self, request, *args, **kwargs):
        if request.method != "POST":
            raise MethodNotAllowed("Utilize o método POST para cadastrar")
        return super().post(request, *args, **kwargs)

class UsuarioUpdateView(generics.UpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated] # Precisa estar autenticado

    def put(self, request, *args, **kwargs):
        if request.method != "PUT":
            raise MethodNotAllowed("Utilize o método PUT para atualizar")
        return super().put(request, *args, **kwargs)

    def get_object(self):
        try:
            user = Usuario.objects.get(pk=self.kwargs['pk'])
            return user
        except Usuario.DoesNotExist:
            raise NotFound("Usuário não encontrado")

@api_view(["POST"])
@permission_classes([AllowAny]) # Não precisa estar autenticado
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
