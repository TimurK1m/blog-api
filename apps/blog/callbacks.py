import os
import json

from django.db.models import Count

from apps.blog.models import Post, Comment, Category
from apps.auths.models import User

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
    total_users = User.objects.count()
    published_posts = Post.objects.filter(
        status = Post.Status.PUBLISHED
    ).count()
    draft_posts = Post.objects.filter(
        status = Post.Status.DRAFT
    ).count()

    total_comments = Comment.objects.count()

    total_posts = published_posts + draft_posts

    published_percent = (
        published_posts/total_posts *100
        if total_posts else 0
    )
    draft_percent = (
        draft_posts/total_posts*100
        if total_posts else 0
    )

    categories = (
        Category.objects.annotate(posts_count = Count("posts")).order_by("-posts_count")
    )

    chart_data = json.dumps({
        "labels": [category.name for category in categories],
        "datasets": [
            {
                "label": "Posts",
                "data": [category.posts_count for category in categories]
            }
        ]
    })

    top_authors = (
        User.objects.annotate(posts_count = Count("post")).filter(posts_count__gt =0). order_by("-posts_count")[:5]
    )

    context.update({
        "total_users": total_users,
        "published_posts": published_posts,
        "draft_posts":draft_posts,
        "total_comments":total_comments,
        "chart_data":chart_data,
        "top_authors_table":{
            "headers": ["Author", "Email", "Posts"],
            "rows": [
                [
                    f"{author.first_name} {author.last_name}".strip(),
                    author.email,
                    author.posts_count,
                ]
                for author in top_authors
            ]
        },
        "published_percent": published_percent,
        "draft_percent": draft_percent
    })

    return context