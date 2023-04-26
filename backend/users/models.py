from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Email address',
        max_length=254,
        unique=True,
        blank=False,
    )
    username = models.CharField(
        verbose_name='Login',
        max_length=150,
        unique=True,
        blank=False
    )
    first_name = models.CharField(
        verbose_name='First name',
        max_length=150,
        blank=False
    )
    last_name = models.CharField(
        verbose_name='Last name',
        max_length=150,
        blank=False
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return f'{self.username} - {self.email}'
