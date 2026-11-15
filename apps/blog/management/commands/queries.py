from datetime import date, timedelta
from typing import Any, Callable

from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser
)
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.blog.models import Category, Post, Tag
from apps.blog import queries
from apps.auths.models import User


RESULT_LIMIT = 5
DEF_SLUG = "non-existent-post"

QUERIES: dict [int, Callable[..., Any]] = {
    1: queries.categories_by_name,
    2: queries.published_posts,
    3: queries.newest_published_posts,
    4: queries.post_by_slug,
    5: queries.active_user_count,
    6: queries.has_drafts,
    7: queries.published_posts_page,
    8: queries.posts_with_word_in_title,
    9: queries.users_with_email_domain,
    10: queries.posts_without_category,
    11: queries.categories_by_slugs,
    12: queries.posts_in_month,
    13: queries.posts_last_days,
    14: queries.posts_between,
    15: queries.author_published_posts,
    16: queries.posts_with_tag,
    17: queries.comments_in_category,
    18: queries.users_with_published_posts,
    19: queries.posts_without_tags,
    20: queries.users_without_comments,
    21: queries.posts_with_both_tags,
    22: queries.search_posts,
    23: queries.published_posts_missing_info,
    24: queries.edited_posts,
    25: queries.comments_by_post_author,
    26: queries.comments_before_post,
    27: queries.published_authors_emails,
    28: queries.published_posts_overview,
    29: queries.posts_stats,
    30: queries.average_comments_per_cost,
    31: queries.categories_wuth_post_count,
    32: queries.categories_with_published_count,
    33: queries.top_authors,
    34: queries.popular_tags,
    35: queries.posts_per_status,
    36: queries.users_activity,
    37: queries.search_users_by_full_name,
    38: queries.published_per_month,
    39: queries.posts_with_popularity,
    40: queries.get_or_create_tag,
    41: queries.publish_old_drafts,
    42: queries.tag_category_post,
    43: queries.merge_categories,
    44: queries.delete_inactive_users_comments,
    45: queries.published_feed,
    46: queries.newest_posts_with_tags,
    47: queries.categories_with_published_posts,
    48: queries.posts_with_last_comments,
    49: queries.posts_witf_staff_comments,
    50: queries.users_with_draft_as_latest_post,
}

class Command(BaseCommand):
    help = "Run ORM queries"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--number",
            type = int,
        )

        parser.add_argument(
            "--sql",
            action="store_true"
        )

    def handle(self, *args, **options: Any) -> None:
        number = options["number"]
        show_sql = options["sql"]

        if number is not None:
            if number not in QUERIES:
                raise CommandError(
                    f"Query number {number} does not exist"
                )

            numbers = [number]
        else:
            numbers = list(QUERIES.keys())

        arguments = self.get_sample_argument()

        for query_number in numbers:
            function = QUERIES[query_number]
            function_arguments = arguments.get(query_number, {})

            with CaptureQueriesContext(connection) as context:
                result = function(**function_arguments)

                if hasattr(result,"query"):
                    annotations = list(
                        result.query.annotations.keys()
                    )
                    result = list (result)

                elif isinstance(result, (list, tuple)):
                    annotations = []
                    relist = list(result)
                else:
                    annotations = []

            self.stdout.write(
                self.style.SUCCESS(
                    f"{query_number} {function.__name__}"
                    f" - {len(context.captured_queries)} SQL query"
                )
            )

            self.display_result(result, annotations)

            if show_sql:
                for sql_number, query_data in enumerate(
                    context.captured_queries,
                    start = 1 
                ):
                    self.stdout.write(
                        f"SQL#{sql_number}"
                    )
                    self.stdout.write(query_data["sql"])
            self.stdout.write("")

    def get_sample_argument(seld) -> dict[int, dict[str,Any]]:
        now = timezone.now()

        latest_post = (
            Post.objects.order_by("-created_at").first()
        )

        latest_post_date = (
            latest_post.created_at.date()
            if latest_post
            else now.date()
        )


        categories_slugs = list(
            Category.objects.values_list("slug", flat = True)[:2]
        )

        tag_slugs = list(
            Tag.objects.values_list("slug", flat = True)[:2]
        )

        published_author_email = (
            User.objects.filter(post__status = Post.Status.PUBLISHED).values_list("email", flat= True).first()
        )



        return {
            4: {
                "slug": (
                    latest_post.slug
                    if latest_post
                    else DEF_SLUG
                ),
            },
            7:{
                "page":1
            },
            8: {
                "word":(
                    latest_post.title.split()[0]
                    if latest_post
                    else "a"
                )
            },
            9:{
                "domain": "example.com"
            },
            11: {
                "slug": categories_slugs
            },
            12: {
                "year": latest_post_date.year,
                "month": latest_post_date.month
            },
            13: {
                "days":30
            },
            14: {
                "start": now.date() - timedelta(days = 365),
                "end": now.date()
            },
            15: {
                "email": published_author_email or "nobody@example.com"
            },
            16: {
                "tag_slug": tag_slugs[0] if tag_slugs else "non-existent-tag"
            },
            17: {
                "category_slug": (
                    categories_slugs[0]
                    if categories_slugs
                    else "non-existent-category"
                )
            },
            21: {
                "first_slug": tag_slugs[0] if tag_slugs else "missings-first",
                "second_slug": tag_slugs[1] if len(tag_slugs) > 1 else "missing-second"
            },
            22: {
                "text":"a"
            },
            34: {
                "min_posts":2
            },
            37:{
                "text": "a"
            },
            40: {
                "name": "Homework Tag"
            },
            41: {
                "days": 30
            },
            42: {
                "category_slug": categories_slugs[0] if categories_slugs else "missing-category",
                "tag_slug": tag_slugs[0] if tag_slugs else "missing-tag"
            },
            43: {
                "source_slug": categories_slugs[0] if len(categories_slugs) >=2 else "missing-source",
                "target_slug": categories_slugs[1] if len(categories_slugs) >=2 else "missing-target"
            }
        }

    def display_result(
            self,
            result: Any,
            annotanions : list[str]
    ) -> None:
        if isinstance(result, list):
            for item in result[:RESULT_LIMIT]:
                if annotanions:
                    annotanion_values = {
                        name: getattr(item, name)
                        for name in annotanions
                    }

                    self.stdout.write(
                        f"{item} {annotanion_values}"
                    )
                else:
                    self.stdout.write(f" {item}")

            self.stdout.write(
                f"   ({len(result)} rows )"
            )
        else:
            self.stdout.write(f"    {result}")