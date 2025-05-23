from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed, NotFound
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .models import Usuario
from .serializers import UsuarioSerializer
from django.contrib.auth.models import User
from Agente.models import Agente
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

class AdminCreateView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]  # Permite acesso sem autenticação

    def create(self, request, *args, **kwargs):
        # Modificar o request antes da validação
        data = request.data.copy()
        
        # Obter um ID de agente válido (o primeiro disponível)
        primeiro_agente = Agente.objects.first()
        if primeiro_agente:
            # Garantir que haja pelo menos um agente na lista de permissões
            data['permissoes'] = [primeiro_agente.id]
        
        # Atualizar o request com os dados modificados
        request._full_data = data
        
        # Continuar com o processamento normal
        return super().create(request, *args, **kwargs)
        
    def perform_create(self, serializer):
        # Cria o usuário com admin=True
        usuario = serializer.save(admin=True)
        
        # Adicionar TODOS os agentes às permissões do administrador
        agentes = Agente.objects.all()
        
        # Limpar permissões existentes para evitar duplicatas
        usuario.permissoes.clear()
        
        # Adicionar todos os agentes
        for agente in agentes:
            usuario.permissoes.add(agente.id)

class UsuarioCreateView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]  # Requer autenticação
   
    def post(self, request, *args, **kwargs):
        # Verifica se o usuário autenticado é administrador
        if not request.user.is_staff:
            raise PermissionDenied("Apenas administradores podem cadastrar novos usuários.")
        
        # Assegurar que haja pelo menos uma permissão
        data = request.data.copy()
        if not data.get('permissoes') or len(data.get('permissoes')) == 0:
            # Obter primeiro agente disponível para atribuir permissão mínima
            primeiro_agente = Agente.objects.first()
            if primeiro_agente:
                data['permissoes'] = [primeiro_agente.id]
        
        request._full_data = data
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        usuario = serializer.save(admin=False)

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
        if str(request.user.id) != str(self.kwargs["pk"]):
            raise PermissionDenied("Você só pode atualizar seus próprios dados.")

        return super().put(request, *args, **kwargs)

    def get_object(self):
        try:
            # Busca o usuário pelo ID fornecido na URL
            user = Usuario.objects.get(pk=self.kwargs["pk"])
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

@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Email"),
            "senha": openapi.Schema(type=openapi.TYPE_STRING, description="Senha"),
        },
        required=["email", "senha"],
    ),
    responses={
        200: "Retorna o token e informações adicionais",
        404: "Email não cadastrado",
        401: "Credenciais inválidas"
    }
)
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
def listar_usuario(request, pk):
    try:
        usuario = Usuario.objects.get(pk=pk)
    except:
        return Response({
            "msg": "Usuário não encontrato."
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not request.user.is_staff and request.user.id != pk:
        raise PermissionDenied("Somente administradores podem acessar outros usuários")
    
    return Response({
        "usuarios": UsuarioSerializer(usuario).data
    })

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

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def atualizar_permissoes_usuario(request, pk):
    """
    Endpoint específico para atualizar apenas as permissões de um usuário.
    """
    try:
        usuario = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permissões (admin ou próprio usuário)
    if not request.user.is_staff and request.user.id != pk:
        raise PermissionDenied("Você só pode atualizar suas próprias permissões.")
    
    # Obter as permissões do request
    permissoes_ids = request.data.get("permissoes", [])
    if not isinstance(permissoes_ids, list):
        return Response({"message": "O campo 'permissoes' deve ser uma lista de IDs."}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Atualizar as permissões
        usuario.permissoes.clear()  # Remove permissões existentes
        for permissao_id in permissoes_ids:
            usuario.permissoes.add(permissao_id)
        
        # Retornar os dados atualizados usando o serializer
        return Response({
            "message": "Permissões atualizadas com sucesso.",
            "usuario": UsuarioSerializer(usuario).data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": f"Erro ao atualizar permissões: {str(e)}"}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["PUT"])
@permission_classes([AllowAny])
def mandar_email_troca_senha(request):
    """
    Endpoint específico para enviar um email com uma nova senha do usuário
    """
    email = request.data.get("email", "")
        
    load_dotenv()
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    from_addr = smtp_username
    to_addr = email
    subject = "Troca de senha"
    body = "Esse é um email de troca de senha"

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    email_server = smtplib.SMTP(smtp_server, smtp_port)
    try:
        email_server.starttls()
        email_server.login(smtp_username, smtp_password)

        email_server.sendmail(from_addr, to_addr, msg.as_string())

        return Response({"message": "foi"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": f"Não foi: {str(e)}"}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        email_server.quit()