import os

from apps.blog.models import Post

def env_callback(request):
    env = os.getenv('BLOG_ENV_ID', 'local').lower()

    if env == "prod":
        return ["Production", "Danger"]

    return ["Local", "WArning"]

def drafts_badge(request):
    return Post.objects.filter(status=Post.Status.DRAFT).count()

def superuser_only(request):
    return request.user.is_superuser  

def dashboard_callback(request, context):
    return context