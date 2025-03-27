from django.contrib import admin
from .models import Permissao, PermissaoUsuario

class PermissaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)

class PermissaoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'Usuario_id', 'Permissao_id')
    list_filter = ('Permissao_id',)

admin.site.register(Permissao, PermissaoAdmin)
admin.site.register(PermissaoUsuario, PermissaoUsuarioAdmin)