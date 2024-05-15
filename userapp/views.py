from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from .models import Project, Todo
import requests, os
from django.conf import settings

# Create your views here.

def home(request):
    return render(request, "home.html")

def login(request):
    if request.user.is_authenticated:
        return redirect('user_dashboard')
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, "login.html")
    else:
        return render(request, "login.html")

def userLogout(request):
    logout(request)
    return redirect('home_page')

def registration(request):
    if request.user.is_authenticated:
        return redirect('user_dashboard')
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration Successful. Please login.')
            return redirect('login_page')
        else:
            return render(request, "register.html", {'form': form})
    else:
        return render(request, "register.html")

@login_required
def dashboard(request):
    user = request.user
    total_projects = Project.objects.filter(owner=user).count()
    active_projects = Project.objects.filter(owner=user, todo__status=False).distinct().count()
    completed_projects_count = 0
    for project in Project.objects.filter(owner=user):
        if all(task.status for task in project.todo_set.all()):
            completed_projects_count += 1
    total_pending_tasks = Todo.objects.filter(project__owner=user, status=False).count()
    context = {
        'user': user,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects_count': completed_projects_count,
        'total_pending_tasks': total_pending_tasks,
    }
    return render(request, 'dashboard.html', context)

@login_required
def newProject(request):
    user = request.user
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        tasks = request.POST.getlist('task')
        project = Project.objects.create(title=project_name, owner=user)
        for task_description in tasks:
            Todo.objects.create(description=task_description, project=project)
        messages.success(request, 'Project created successfully.')
        return redirect('user_dashboard')
    else:
        return render(request, "new_project.html", {'user': user})

@login_required
def viewProjects(request):
    user = request.user
    project = Project.objects.filter(owner=user)
    return render(request, "view_projects.html", {'user': user, 'project': project})

@login_required
def detailedview(request, project_id):
    user = request.user
    project = Project.objects.get(id=project_id, owner=user)
    gist_url = request.session.pop('gist_url', None)
    local_file_path = request.session.pop('local_file_path', None)
    all_tasks = project.todo_set.all()
    total_tasks = all_tasks.count()
    completed_tasks = all_tasks.filter(status=True).count()
    pending_tasks = total_tasks - completed_tasks
    pending_todos = all_tasks.filter(status=False)
    completed_todos = all_tasks.filter(status=True)
    return render(request, "detailedview.html", {'user': user,
                                                'project': project,
                                                'total_tasks': total_tasks,
                                                'completed_tasks': completed_tasks,
                                                'pending_tasks': pending_tasks,
                                                'pending_todos': pending_todos,
                                                'completed_todos': completed_todos,
                                                'gist_url': gist_url,
                                                'local_file_path': local_file_path,})

@login_required
def editproject(request, project_id):
    user = request.user
    project = Project.objects.get(id=project_id, owner=user)
    if request.method == 'POST':
        project.title = request.POST.get('project_name')
        project.save()
        task_ids = request.POST.getlist('task_id')
        task_descriptions = request.POST.getlist('task')
        task_statuses = request.POST.getlist('status')
        for task_id, description, status in zip(task_ids, task_descriptions, task_statuses):
            if task_id:
                task = Todo.objects.get(id=task_id, project=project)
                task.description = description
                task.status = status == 'completed'
                task.save()
            else:
                Todo.objects.create(project=project, description=description, status=status == 'completed')
        messages.success(request, 'Project edited successfully.')
        return redirect('detailedview_page', project_id=project.id)
    else:
        return render(request, "edit_project.html", {'user': user, 'project': project})

@login_required
def deleteproject(request, project_id):
    user = request.user
    project = Project.objects.get(id=project_id, owner=user)
    project.delete()
    return redirect('view_projects_page')

@login_required
def deletetask(request, task_id):
    user = request.user
    task = get_object_or_404(Todo, id=task_id, project__owner=user)
    project_id = task.project.id
    task.delete()
    return redirect('edit_project', project_id=project_id)

@login_required
def completedProjects(request):
    user = request.user
    projects = Project.objects.filter(
        owner=user,
        todo__status=True
    ).distinct()
    completed_projects = []
    for project in projects:
        if all(task.status for task in project.todo_set.all()):
            completed_projects.append(project)
    return render(request, 'completed_projects.html', {'projects': completed_projects})

@login_required
def pendingProjects(request):
    user = request.user
    projects = Project.objects.filter(
        owner=user,
    ).distinct()
    pending_projects = []
    for project in projects:
        if any(not task.status for task in project.todo_set.all()):
            pending_projects.append(project)
    return render(request, 'pending_projects.html', {'projects': pending_projects})

@login_required
def export_as_gist(request, project_id):
    user = request.user
    project = get_object_or_404(Project, id=project_id, owner=user)
    tasks = project.todo_set.all()
    completed_tasks = tasks.filter(status=True)
    pending_tasks = tasks.filter(status=False)
    gist_content = f"# {project.title}\n\n"
    gist_content += f"**Summary:** {completed_tasks.count()} / {tasks.count()} completed.\n\n"
    gist_content += "## Pending Tasks\n\n"
    for task in pending_tasks:
        gist_content += f"- [ ] {task.description}\n"
    gist_content += "\n## Completed Tasks\n\n"
    for task in completed_tasks:
        gist_content += f"- [x] {task.description}\n"
    local_file_path = os.path.join(settings.MEDIA_ROOT, f"{project.title}.md")
    with open(local_file_path, 'w') as file:
        file.write(gist_content)
    gist_data = {
        "description": f"Gist for project: {project.title}",
        "public": False,
        "files": {
            f"{project.title}.md": {
                "content": gist_content
            }
        }
    }
    github_token = settings.GITHUB_TOKEN
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post("https://api.github.com/gists", json=gist_data, headers=headers)
    if response.status_code == 201:
        gist_url = response.json().get("html_url")
        messages.success(request, f"Gist created successfully.")
        request.session['gist_url'] = gist_url
        request.session['local_file_path'] = local_file_path
    else:
        messages.error(request, f"Failed to create gist. Error: {response.json().get('message')}")
    return redirect('detailedview_page', project_id=project_id)