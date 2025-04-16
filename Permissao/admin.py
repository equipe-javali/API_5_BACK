from django.contrib import admin
from .models import Permissao

class PermissaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)

admin.site.register(Permissao, PermissaoAdmin)