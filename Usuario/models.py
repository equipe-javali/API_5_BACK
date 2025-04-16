from django.contrib.auth.models import AbstractUser
from django.db import models
from Permissao.models import Permissao

class Usuario(AbstractUser):
    nome = models.CharField(max_length=94, null=False, blank=False)
    # email: AbstractUser já possui um campo para e-mail
    # senha: AbstractUser já possui um campo para senha
    admin = models.BooleanField(default=False)
    permissoes = models.ManyToManyField(Permissao)

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

    def __str__(self):
        return self.nome

    @property
    def is_admin(self):
        """
        Retorna True se o usuário for administrador.
        """
        return self.admin

    @property
    def is_user(self):
        """
        Retorna True se o usuário for um usuário comum (não administrador).
        """
        return not self.admin
