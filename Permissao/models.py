from django.db import models
from Usuario.models import Usuario

class PermissaoManager(models.Manager):
    def create_permissao(self, nome):
        permissao = self.create(nome=nome)
        return permissao

class Permissao(models.Model):
    nome = models.CharField(max_length=47, null=False, blank=False)

    objects = PermissaoManager()

class PermissaoUsuarioManager(models.Manager):
    def create_permissaoUsuario(self, Permissao_id, Usuario_id):
        permissaoUsuario = self.create(Permissao_id=Permissao_id, Usuario_id=Usuario_id)
        return permissaoUsuario
    
class PermissaoUsuario(models.Model):
    Permissao_id = models.ForeignKey(Permissao, on_delete=models.CASCADE, null=True, blank=False)
    Usuario_id = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=False)

    objects = PermissaoUsuarioManager()
