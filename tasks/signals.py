from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Task
from projects.models import Project


@receiver(post_save, sender=Task)
def update_project_progress(sender, instance, created, **kwargs):

    project = instance.project

    tasks = Task.objects.filter(project=project)

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status="Completed").count()

    if total_tasks == 0:
        progress = 0
    else:
        progress = (completed_tasks / total_tasks) * 100

    print(f"Project {project.name} progress updated to {progress}%")

@receiver(post_save, sender=Task)
def task_created_notification(sender, instance, created, **kwargs):

    if created:
        print(f"New task created: {instance.title}")