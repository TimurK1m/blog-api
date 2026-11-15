from datetime import date, timedelta
from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone

from apps.auths.models import User
from apps.blog.models import Category, Post


POST_PER_PAGE = 10
NEWEST_POST = 5


def categories_by_name() -> QuerySet[Category]:
    return Category.objects.order_by("name")

def published_posts() -> QuerySet[Post]:
    return Post.objects.filter(
        status = Post.Status.PUBLISHED
    ). order_by("-created_at")

def newest_published_posts() ->QuerySet[Post]:
    return published_posts()[:NEWEST_POST]

def post_by_slug(slug:str) -> Optional[Post]:
    return Post.objects.filter(slug=slug).first()

def active_user_count() -> int:
    return User.objects.filter(
        is_active = True,
        is_staff =False
    ).count()

def has_drafts() -> bool:
    return Post.objects.filter(
        status = Post.Status.DRAFT
    ).exists()

def published_posts_page(page :int) -> QuerySet[Post]:
    start = (page-1)*POST_PER_PAGE
    end = start+POST_PER_PAGE

    return published_posts()[start:end]

def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    return Post.objects.filter(
        title__icontains = word
    )

def users_with_email_domain(domain:str ) ->QuerySet[User]:
    return User.objects.filter(
        email__iendswith = f"@{domain}"
    )

def posts_without_category() -> QuerySet[Post]:
    return Post.objects.filter(
        category__isnull = True
    )

def categories_by_slugs(slug: list[str]) -> QuerySet[Category]:
    return Category.objects.filter(
        slug__in =slug
    )

def posts_in_month(year:int , month: int) -> QuerySet[Post]:
    return Post.objects.filter(
        created_at__year = year,
        created_at__month = month
    )

def posts_last_days(days:int) -> QuerySet[Post]:
    date_limit = timezone.now() - timedelta( days=days)

    return Post.objects.filter(
        created_at__gte=date_limit
    )

def posts_between(start: date, end: date) -> QuerySet[Post]:
    return Post.objects.filter(
        created_at__date__range =(start,end)
    )

