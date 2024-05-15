from django.contrib import admin
from . models import Project, Todo

# Register your models here.

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_date', 'owner']

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['description', 'status', 'created_date', 'updated_date', 'project']