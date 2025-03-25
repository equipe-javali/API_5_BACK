from django.db import models
from Agente.models import Agente


class Contexto(models.Model):
    pergunta = models.TextField(null=False, blank=False)
    pergunta = models.TextField(null=False, blank=False)
    Agente_id = models.ForeignKey(Agente, on_delete=models.PROTECT, null=False, blank=False)
