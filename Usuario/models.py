from django.contrib.auth.models import AbstractUser
from django.db import models
# from Departamento.models import Departamento

class Usuario(AbstractUser):
    nome = models.CharField(max_length=94, null=False, blank=False)
    # email: AbstractUser já possui um campo para e-mail
    # senha: AbstractUser já possui um campo para senha
    # Departamento_id = models.ForeignKey(Departamento, on_delete=models.PROTECT, null=False, blank=False)
    admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="usuario_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="usuario_permissions",
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email')
        ]
