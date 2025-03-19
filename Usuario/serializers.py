from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ["nome", "email", "senha", "admin"]

    def create(self, validated_data):
        senha = validated_data.pop('senha')

        nome = validated_data.get("nome")
        username = nome.lower().replace(" ", "_")
        validated_data["username"] = username

        user = Usuario.objects.create_user(**validated_data)
        user.set_password(senha)
        user.save()
        return user