from django.db import models

from django.contrib.auth.models import User

from project.models import Project
from tagging.models import Tag


class ProjectTask(models.Model):

    """
    Defines a task (which may or may not be associated 
    with a project).
    """
    assigned = models.ManyToManyField(User, related_name="Assigned Members")
    creator = models.ForeignKey(User, related_name="Creator")
    summary = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    completed = models.BooleanField(default=False)
    startDate = models.DateTimeField(auto_now=False, auto_now_add=True)
    dueDate = models.DateTimeField(auto_now=False, auto_now_add=True)
    inProgress = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, related_name="Task Tags")
    project = models.ForeignKey(Project, related_name="Project", null=True)

    def __str__(self):
        return "Task " + str(self.summary)
