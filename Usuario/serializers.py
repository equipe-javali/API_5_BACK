from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ["nome", "email", "senha", "admin"]

    def create(self, validated_data):
        senha = validated_data.pop("senha")

        nome = validated_data.get("nome")
        username = nome.lower().replace(" ", "_")
        validated_data["username"] = username

        user = Usuario.objects.create_user(**validated_data)
        user.set_password(senha)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        nome = validated_data.get("nome", None)
        email = validated_data.get("email", None)
        senha = validated_data.get("senha", None)
        Departamento_id = validated_data.get("Departamento_id", None)
        admin = validated_data.get("admin", None)

        if nome not in [None, ""]:
            instance.nome = nome
        if email not in [None, ""]:
            instance.email = email
        if senha not in [None, ""]:
            instance.senha = senha
        if Departamento_id not in [None, ""]:
            instance.Departamento_id = Departamento_id
        if admin not in [None, ""]:
            instance.admin = admin
        
        instance.save()
        return instance
