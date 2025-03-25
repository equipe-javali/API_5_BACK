from django.db import models
from Permissao.models import Permissao

class Agente(models.Model):
    nome = models.CharField(max_length=94, null=False, blank=False)
    descricao = models.TextField(null=False, blank=False)
    Permissao_id = models.ForeignKey(Permissao, on_delete=models.PROTECT, null=False, blank=False)
