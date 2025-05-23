from django.db import models
from django.utils import timezone
from Usuario.models import Usuario
from Agente.models import Agente

class ChatManager(models.Manager):
    def create_chat(self, Usuario_id, Agente_id):
        chat = self.create(Usuario_id=Usuario_id, Agente_id=Agente_id)
        return chat

class Chat(models.Model):
    Usuario_id = models.ForeignKey(Usuario, on_delete=models.PROTECT, null=False, blank=False)
    Agente_id = models.ForeignKey(Agente, on_delete=models.PROTECT, null=False, blank=False)
    
    objects = ChatManager()
    
class MensagemManager(models.Manager):
    def create_mensagem(self, texto, Chat_id, usuario):
        mensagem = self.create(texto=texto, Chat_id=Chat_id, usuario=usuario)
        return mensagem

class Mensagem(models.Model):
    texto = models.TextField(null=False, blank=False)
    Chat_id = models.ForeignKey(Chat, on_delete=models.PROTECT, null=False, blank=False)
    usuario = models.BooleanField(null=False, blank=False)
    dataCriacao = models.DateTimeField(default=timezone.now)
    objects = MensagemManager()
