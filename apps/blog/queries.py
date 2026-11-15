from datetime import date, timedelta
from typing import Optional, Any

from django.db.models import QuerySet, Q, F, Count, Value, Avg, Min, Max, Case, When, CharField, Prefetch, OuterRef, Subquery, Exists
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.models import Category, Post, Tag, Comment


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


def author_published_posts(email:str) -> QuerySet[Post]:
    return Post.objects.filter(
        author__email__iexact = email,
        status = Post.Status.PUBLISHED
    )


def posts_with_tag(tag_slug:str) -> QuerySet[Post]:
    return Post.objects.filter(
        tags__slug=tag_slug
    ).distinct()


def comments_in_category(category_slug:str) -> QuerySet[Comment]:
    return Comment.objects.filter(
        post__category__slug = category_slug
    )


def users_with_published_posts() -> QuerySet[User]:
    return User.objects.filter(
        post__status = Post.Status.PUBLISHED
    ).distinct()


def posts_without_tags() ->QuerySet[Post]:
    return Post.objects.filter(
        tags__isnull=True
    )


def users_without_comments() -> QuerySet[User]:
    return User.objects.filter(
        comments__isnull = True
    )


def posts_with_both_tags(first_slug: str, second_slug:str) -> QuerySet[Post]:
    return (Post.objects.filter(tags__slug = first_slug).filter(tags__slug=second_slug).distinct())



def search_posts(text:str) ->QuerySet[Post]:
    return Post.objects.filter(
        Q(title__icontains=text) |
        Q(body__icontains = text)
    )


def published_posts_missing_info() -> QuerySet[Post]:
    return (
        Post.objects.filter(status=Post.Status.PUBLISHED).filter(Q(category__isnull =True) | Q(tags__isnull = True)).distinct()
    )


def edited_posts() ->QuerySet[Post]:
    return Post.objects.filter(
        updated_at__gt = F("created_at") + timedelta(hours=1)
    )


def comments_by_post_author() -> QuerySet[Comment]:
    return Comment.objects.filter(
        author = F("post__author")
    )


def comments_before_post() -> QuerySet[Comment]:
    return Comment.objects.filter(
        created_at__lt = F("post__created_at")
    )


def published_authors_emails() -> list[str]:
    return list(
        User.objects.filter(post__status = Post.Status.PUBLISHED).order_by("email").values_list("email", flat=True).distinct()
    )


def published_posts_overview() -> list[dict[str, Any]]:
    return list(
        Post.objects.filter(status = Post.Status.PUBLISHED)
        .order_by("pk")
        .values("title", 
                author_email = F("author__email"), 
                category_name = Coalesce(
                    F("category__name"),
                    Value("Uncategorized")
                    )
        )
    )


def posts_stats() -> dict[str, Any]:
    return Post.objects.aggregate(
        total = Count("id"),
        published = Count(
            "id",
            filter=Q(status = Post.Status.PUBLISHED)
        ),
        drafts = Count(
            "id",
            filter = Q(status = Post.Status.DRAFT)
        ),
        first_post_at = Min("created_at"),
        last_post_at = Max("created_at")
    )


def average_comments_per_cost() -> float:
    result = (
        Post.objects
        .filter(status = Post.Status.PUBLISHED)
        .annotate(comment_count = Count("comments"))
        .aggregate(average = Avg("comment_count"))
    )

    return round(float(result["average"] or 0), 2)


def categories_wuth_post_count() ->QuerySet[Category]:
    return (
        Category.objects.annotate(post_count = Count("posts")).order_by("-post_count", "name")
    )


def categories_with_published_count() -> QuerySet[Category]:
    return (
        Category.objects
        .annotate(
            published_count = Count(
                "posts",
                filter = Q(posts__status = Post.Status.PUBLISHED)
            )
        ).order_by("-published_count", "name")
    )


def top_authors() -> QuerySet[User]:
    return (
        User.objects
        .annotate(
            published_count = Count(
                "post",
                filter = Q(post__status = Post.Status.PUBLISHED),
                distinct=True
            )
        ).filter(published_count__gt = 0)
        .order_by("-published_count", "email")[:5]
    )


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    return (
        Tag.objects
        .annotate(post_count = Count("posts", distinct = True))
        .filter(post_count__gte = min_posts)
        .order_by("-post_count", "name")
    )


def posts_per_status() -> list[dict[str,Any]]:
    return list(
        Post.objects
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def users_activity() -> QuerySet[User]:
    return (
        User.objects
        .annotate(
            post_count =Count("post", distinct = True),
            comment_count = Count("comments", distinct = True)
        ).order_by("email")
    )


def search_users_by_full_name(text:str) -> QuerySet[User]:
    return (
        User.objects
        .annotate(
            full_name = Concat(
                "first_name",
                Value(" "),
                "last_name"
            )
        )
        .filter(full_name__icontains = text)
    )


def published_per_month() -> list[dict[str,Any]]:
    return list(
        Post.objects
        .filter(status = Post.Status.PUBLISHED)
        .annotate(month = TruncMonth("created_at"))
        .values("month")
        .annotate(count = Count("id"))
        .order_by("month")
    )


def posts_with_popularity() ->QuerySet[Post]:
    return (
        Post.objects
        .annotate(comment_count = Count("comments"))
        .annotate(
            popularity = Case (
                When(comment_count__gte = 10, then =Value("hot")),
                When(comment_count__gte=3, then = Value("normal")),
                default = Value("quiet"),
                output_field=CharField(),
            )
        )
        .order_by("-comment_count")
    )


def get_or_create_tag(name:str) -> tuple[Tag, bool]:
    tag, created = Tag.objects.get_or_create(
        name = name,
        defaults={
            "slug" : slugify(name)
        }
    )

    return tag, created


def publish_old_drafts(days:int) -> int:
    date_limit = timezone.now() - timedelta(days=days)

    return Post.objects.filter(
        status = Post.Status.DRAFT,
        created_at__lt = date_limit
    ).update(
        status = Post.Status.PUBLISHED,
        updated_at = timezone.now()
    )


def tag_category_post(category_slug: str, tag_slug: str) -> int:
    posts = Post.objects.filter(category__slug=category_slug)
    tag = Tag.objects.get(slug = tag_slug)
    posts_count = posts.count()

    tag.posts.add(*posts)

    return posts_count


def merge_categories(source_slug: str, target_slug: str) -> int:
    if source_slug == target_slug:
        return 0

    source = Category.objects.get(slug = source_slug)
    target = Category.objects.get(slug = target_slug)

    moved_count = Post.objects.filter(category = source).update(category = target)

    source.delete()

    return moved_count


def delete_inactive_users_comments() ->int:
    deleted_count, _ = Comment.objects.filter(
        author__is_active = False
    ).delete()


    return deleted_count


def published_feed() -> list[str]:
    posts = (
        Post.objects
        .filter(status = Post.Status.PUBLISHED)
        .select_related( "author" , "category")
        .order_by("-created_at")[:50]
    )


    return [
        (
            f"{post.title} | "
            f"{post.author.email} | "
            f"{post.category.name if post.category else 'Uncategorized'}"
        )
        for post in posts
    ]


def newest_posts_with_tags() -> list[str]:
    posts = (
        Post.objects
        .prefetch_related("tags")
        .order_by("-created_at")[:20]
    )

    return [
        f"{post.title}: {','.join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]


def categories_with_published_posts() -> dict[str, list[str]]:
    published_posts_queryset = (
        Post.objects.filter(status = Post.Status.PUBLISHED)
        .order_by("-created_at")
    )

    categories = (
        Category.objects
        .prefetch_related(
            Prefetch(
                "posts",
                queryset = published_posts_queryset,
                to_attr="published_posts_list"
            )
        )
        .order_by("name")
    )

    return {
        category.name: [
            post.title for post in category.published_posts_list
        ]
        for category in categories
    }


def posts_with_last_comments() ->QuerySet[Post]:

    latest_comment = (
        Comment.objects
        .filter(post = OuterRef("pk"))
        .order_by("-created_at")
        .values("body")[:1]
    )

    return (
        Post.objects
        .filter(status = Post.Status.PUBLISHED)
        .annotate(last_comment = Subquery(latest_comment))
        .order_by("-created_at")
    )


def posts_witf_staff_comments() ->QuerySet[Post]:
    staff_comments = Comment.objects.filter(
        post = OuterRef("pk"),
        author__is_staff = True
    )

    return (
        Post.objects
        .annotate( has_staff_comment = Exists(staff_comments))
        .filter(has_staff_comment = True)
        .order_by("-created_at")
    )


def users_with_draft_as_latest_post() -> QuerySet[User]:
    latest_post = (
        Post.objects
        .filter(author = OuterRef("pk"))
        .order_by("-created_at")
        .values("status")[:1]
    )

    return (
        User.objects
        .annotate(latest_post_status = Subquery(latest_post))
        .filter(latest_post_status = Post.Status.DRAFT)
        .order_by("email")
    )