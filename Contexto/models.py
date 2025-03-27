from django.db import models
from Agente.models import Agente

class ContextoManager(models.Manager):
    def create_contexto(self, pergunta, resposta, Agente_id):
        contexto = self.create(pergunta=pergunta, resposta=resposta, Agente_id=Agente_id)
        return contexto

class Contexto(models.Model):
    pergunta = models.TextField(null=False, blank=False)
    resposta = models.TextField(null=False, blank=False)
    Agente_id = models.ForeignKey(Agente, on_delete=models.PROTECT, null=False, blank=False)
    
    objects = ContextoManager()