from django.contrib import admin
from project.models import *

admin.site.register(Project)
admin.site.register(ProjectTask)
admin.site.register(Worklog)
admin.site.register(Tag)
