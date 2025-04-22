from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed, NotFound
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Usuario
from .serializers import UsuarioSerializer

class AdminCreateView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]  # Permite acesso sem autenticação

    def perform_create(self, serializer):
        # Garante que o usuário criado será um administrador
        serializer.save(admin=True)

class UsuarioCreateView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
   

    def post(self, request, *args, **kwargs):
        # Verifica se o usuário autenticado é administrador
        if not request.user.is_staff:
            raise PermissionDenied("Apenas administradores podem cadastrar novos usuários.")
        return super().post(request, *args, **kwargs)

class UsuarioUpdateView(generics.UpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        # Verifica se o método é PUT
        if request.method != "PUT":
            raise MethodNotAllowed("Utilize o método PUT para atualizar")

        # Verifica se o usuário é administrador
        if request.user.is_staff:
            return super().put(request, *args, **kwargs)

        # Se não for administrador, verifica se está tentando atualizar seus próprios dados
        if str(request.user.id) != str(self.kwargs['pk']):
            raise PermissionDenied("Você só pode atualizar seus próprios dados.")

        return super().put(request, *args, **kwargs)

    def get_object(self):
        try:
            # Busca o usuário pelo ID fornecido na URL
            user = Usuario.objects.get(pk=self.kwargs['pk'])
            return user
        except Usuario.DoesNotExist:
            raise NotFound("Usuário não encontrado")

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_user(request, pk):
    try:
        usuario = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        return Response({
            "msg": "Usuário não encontrado."
        }, status=status.HTTP_404_NOT_FOUND)
    if request.user.is_staff:
        usuario.delete()
        return Response({
            "msg": "Usuário excluído com sucesso."
        }, status=status.HTTP_200_OK)

    # Se não for administrador, verifica se está tentando excluir seu próprio usuário
    if str(request.user.id) == str(pk):
        usuario.delete()
        return Response({
            "msg": "Usuário excluído com sucesso."
        }, status=status.HTTP_200_OK)
    raise PermissionDenied("Você só pode excluir seu próprio usuário.")

@api_view(["POST"])
@permission_classes([AllowAny])  # Não precisa estar autenticado
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
        # Gera os tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Retorna o token e informações adicionais
        return Response({
            "access_token": access_token,
            "refresh_token": str(refresh),
            "is_admin": user.is_staff,  # Indica se o usuário é administrador
            "nome": user.nome,  # Nome do usuário
            "email": user.email  # Email do usuário
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "msg": "Credenciais inválidas"
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_usuarios_todos(request):
    if not request.user.is_staff:
        raise PermissionDenied("Somente administratores podem acessar todos os usuários.")
    
    try:
        usuarios = Usuario.objects.all()
    except:
        return Response({
            "msg": "Usuários não encontratos."
        }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "usuarios": UsuarioSerializer(usuarios, many=True).data
    })
