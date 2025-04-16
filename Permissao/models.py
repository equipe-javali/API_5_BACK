from django.db import models

class PermissaoManager(models.Manager):
    def create_permissao(self, nome):
        permissao = self.create(nome=nome)
        return permissao

class Permissao(models.Model):
    nome = models.CharField(max_length=47, null=False, blank=False)

    objects = PermissaoManager()
