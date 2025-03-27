from django.contrib import admin
from .models import TrainedModel

class TrainedModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'Agente_id', 'created_at', 'examples_count', 'performance_score', 'is_active')
    list_filter = ('Agente_id', 'is_active')
    search_fields = ('Agente_id__nome',)
    ordering = ('-created_at',)

admin.site.register(TrainedModel, TrainedModelAdmin)