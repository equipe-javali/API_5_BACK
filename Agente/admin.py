from django.contrib import admin
from .models import Agente

class AgenteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'descricao', 'Permissao_id')
    list_filter = ('Permissao_id',)
    search_fields = ('nome', 'descricao')

admin.site.register(Agente, AgenteAdmin)