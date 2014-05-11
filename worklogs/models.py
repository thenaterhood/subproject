from django.db import models

from django.contrib.auth.models import User

from project.models import Project


class Worklog(models.Model):

    """
    Defines a model that contains data for work logged
    on a Project.
    """
    project = models.ForeignKey(Project)
    owner = models.ForeignKey(User)
    summary = models.CharField(max_length=140)
    description = models.CharField(max_length=300)
    hours = models.IntegerField(default=0)
    minutes = models.IntegerField(default=0)
    datestamp = models.DateTimeField(auto_now=False, auto_now_add=True)

    def __str__(self):
        return self.project.__str__() + " log (" + str(self.datestamp) + " )"

class WorklogPrefs(models.Model):
    owner = models.ForeignKey(User)
    public = models.BooleanField(default=False)
