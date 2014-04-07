from django.db import models
from django.contrib.auth.models import User

from tagging.models import Tag

from django.utils import timezone


class TimelineEvent(models.Model):
    member = models.ForeignKey(User, related_name="event creator")
    datestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    title = models.CharField(max_length=140)
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    link = models.CharField(max_length=255)
    related_key = models.IntegerField()
    viewers = models.ManyToManyField(User, related_name="allowed viewers")

    def __str__(self):
        return str(self.datestamp) + " " + self.member.username + " " + self.title


class Project(models.Model):

    """
    Defines a Project model which can have tags, 
    tasks, and additional members associated with it.

    This is the basis of the application.
    """
    manager = models.ForeignKey(User, related_name="Project Manager")
    subprojects = models.ManyToManyField('Project', related_name="Subprojects")
    parents = models.ManyToManyField('Project', related_name="Parents")
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=140)
    status = models.CharField(max_length=50)
    phase = models.CharField(max_length=50)
    lines = models.IntegerField(default=0)
    loc_per_h = models.BooleanField(default=True)
    members = models.ManyToManyField(User, related_name="Project Members")
    active = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag, related_name="Project Tags")

    def __str__(self):
        return self.name + " (manager: " + self.manager.__str__() + ")"
