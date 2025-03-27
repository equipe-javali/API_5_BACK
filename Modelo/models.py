from django.db import models
from Agente.models import Agente

class TrainedModelManager(models.Manager):
    def create_trained_model(self, Agente_id, model_path, vectorizer_path, examples_count, performance_score):
        trained_model = self.create(
            Agente_id=Agente_id,
            model_path=model_path,
            vectorizer_path=vectorizer_path,
            examples_count=examples_count,
            performance_score=performance_score
        )
        return trained_model

class TrainedModel(models.Model):
    Agente_id = models.ForeignKey(Agente, on_delete=models.CASCADE)
    model_path = models.CharField(max_length=255)
    vectorizer_path = models.CharField(max_length=255)
    examples_count = models.IntegerField()
    performance_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    objects = TrainedModelManager()

