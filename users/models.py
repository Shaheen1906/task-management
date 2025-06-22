from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.conf import settings

# Create your models here.

class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the group")
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='managed_groups',
        help_text="The user who manages this group"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ['created_at']

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        help_text="the user who is a member of the group"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='members',
        help_text="the group to which the user belongs"
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
        unique_together = ('user', 'group')
        ordering = ['date_joined']

    def __str__(self):
        return f"{self.user.username} - {self.group.name}"

