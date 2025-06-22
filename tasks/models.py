from django.db import models
import uuid
from django.conf import settings
from users.models import Group


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, help_text="Short description of the task.")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the task.")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        help_text="the user who created the task"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text="the user currently assigned to this task"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True,
        help_text="The group this task belongs to"
    )

    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ongoing',
        help_text="Current status of the task."
    )
    due_date = models.DateField(null=True, blank=True, help_text="Due date for the task completion.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the task was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the task was last updated.")

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (Status: {self.status.capitalize()})"
    
    def save(self, *args, **kwargs):
        from datetime import date
        if self.due_date and self.due_date < date.today() and self.status != 'completed':
            self.status = 'overdue'
        super().save(*args, **kwargs)