from django.contrib import admin
from .models import Contexto

class ContextoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pergunta', 'Agente_id')
    list_filter = ('Agente_id',)
    search_fields = ('pergunta', 'resposta')

admin.site.register(Contexto, ContextoAdmin)