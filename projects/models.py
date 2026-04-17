from django.db import models

# Create your models here.

class Project(models.Model):

    STATUS_CHOICES = [
        ('Active','Active'),
        ('Completed','Completed')
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE)
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    