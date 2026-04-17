from django.db import models

# Create your models here.

class Task(models.Model):

    PRIORITY_CHOICES = [
        ('High','High'),
        ('Medium','Medium'),
        ('Low','Low')
    ]

    STATUS_CHOICES = [
        ('Todo','Todo'),
        ('In Progress','In Progress'),
        ('Review','Review'),
        ('Completed','Completed')
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)

    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    due_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)