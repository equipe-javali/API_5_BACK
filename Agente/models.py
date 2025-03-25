from django.db import models
from Permissao.models import Permissao

class AgenteManager(models.Manager):
    def create_agente(self, nome, descricao, Permissao_id):
        agente = self.create(nome=nome, descricao=descricao, Permissao_id=Permissao_id)
        return agente

class Agente(models.Model):
    nome = models.CharField(max_length=94, null=False, blank=False)
    descricao = models.TextField(null=False, blank=False)
    Permissao_id = models.ForeignKey(Permissao, on_delete=models.PROTECT, null=False, blank=False)

    objects = AgenteManager()
