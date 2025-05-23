from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ["id", "nome", "email", "senha", "admin", "permissoes"]

    def create(self, validated_data):
        print("Dados recebidos:", validated_data)
        admin_flag = validated_data.pop("admin", False) 
        senha = validated_data.pop("senha")
        
        # Permissões são opcionais para usuários comuns
        permissoes = validated_data.pop("permissoes", [])
    
        username = validated_data.get("email")
        validated_data["username"] = username
    
        user = Usuario.objects.create_user(**validated_data)
        user.set_password(senha)
        user.is_staff = admin_flag
        user.save()
    
        # Adicionar permissões apenas se a lista não estiver vazia
        if permissoes:
            for permissao in permissoes:
                user.permissoes.add(permissao)
    
        return user
    
    def update(self, instance, validated_data):
        nome = validated_data.get("nome", None)
        email = validated_data.get("email", None)
        senha = validated_data.get("senha", None)
        admin = validated_data.get("admin", None)
        permissoes = validated_data.get("permissoes", None) 

        usuario = Usuario.objects.get(email=email)

        if nome not in [None, ""]:
            usuario.nome = nome
        if email not in [None, ""]:
            usuario.email = email
        if senha not in [None, ""]:
            usuario.set_password(senha)
        if admin not in [None, ""]:
            usuario.admin = admin
        if permissoes is not None:  
            usuario.permissoes.set(permissoes)

        usuario.save()

        return usuario
