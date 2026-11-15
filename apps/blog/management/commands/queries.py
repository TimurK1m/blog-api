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

from apps.blog.models import Category, Post
from apps.blog import queries


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


        categories = list(
            Category.objects.values_list("slug", flat = True)[:2]
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
                "slug": categories
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