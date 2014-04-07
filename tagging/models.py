from django.db import models

from django.contrib.auth.models import User


class Tag(models.Model):

    """
    Defines a Tag, which can be associated with Projects and 
    ProjectTasks in order to better classify projects and tasks 
    and provide a method of filtering views.
    """
    owner = models.ForeignKey(User, related_name="Owner")
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    public = models.BooleanField(default=False)
    users = models.ManyToManyField(User, related_name="Tag users")
    viewers = models.ManyToManyField(User, related_name="Tag viewers")
    usage = models.CharField(max_length=100)
    visible = models.BooleanField(default=True)
    system = models.CharField(max_length=100, default="")

    def __str__(self):
        return "Tag " + self.name + ": " + str(self.owner)
