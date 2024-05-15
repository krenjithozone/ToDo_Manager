from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('', views.home, name="home_page"),
    path('login', views.login, name="login_page"),
    path('logout', views.userLogout, name="user_logout"),
    path('registration', views.registration, name="registration_page"),
    path('dashboard', views.dashboard, name="user_dashboard"),
    path('newproject', views.newProject, name="new_project_page"),
    path('viewprojects', views.viewProjects, name="view_projects_page"),
    path('detailedview/<int:project_id>', views.detailedview, name="detailedview_page"),
    path('editproject/<int:project_id>', views.editproject, name="edit_project"),
    path('deleteproject/<int:project_id>', views.deleteproject, name="delete_project"),
    path('deletetask/<int:task_id>', views.deletetask, name="delete_task"),
    path('completedprojects', views.completedProjects, name="completed_projects"),
    path('pendingprojects', views.pendingProjects, name="pending_projects"),
    path('export_gist/<int:project_id>/', views.export_as_gist, name='export_as_gist'),

] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)