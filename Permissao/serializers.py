from rest_framework import serializers
from .models import Permissao

class PermissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permissao
        fields = ["nome"]

    def create(self, validated_data):
        permissao = Permissao.objects.create_permissao(**validated_data)
        return permissao