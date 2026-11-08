from typing import Any
import random
import time

from faker import Faker

from django.core.management.base import BaseCommand, CommandParser, CommandError
from django.utils.text import slugify
from django.db import transaction
from django.contrib.auth.hashers import make_password

from apps.blog.models import Category, Tag, Post, Comment
from apps.auths.models import User

CREATE_USERS = 20
CREATE_POSTS = 100
CREATE_COMMENTS = 500

SEED_PASSWORD = "TestPassword123"

CATEGORIES = [
    "Python",
    "Django",
    "JavaScript",
    "React",
    "Node.js",
    "CSS",
    "HTML",
    "SQL"
]

TAGS = [
    "Web Development",
    "Backend",
    "Frontend",
    "Database",
    "API",
    "Testing",
    "Deployment",
    "Security",
    "JWT",
    "Authentication",
    "Authorization",
    "REST",
    "GraphQL",
    "Docker",
    "Kubernetes",
    "DevOps",
    "Cloud",
    "Microservices",
    "Performance",
    "Optimization",
    "Accessibility"
]

class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments (self, parser: CommandParser) -> None:
        parser.add_argument(
            "--users",
            type = int,
            default = CREATE_USERS,
            help = "Numbers of users to create."
        )

        parser.add_argument(
            "--posts",
            type = int,
            default = CREATE_POSTS,
            help = "Numbers of posts to create."
        )

        parser.add_argument(
            "--comments",
            type = int,
            default = CREATE_COMMENTS,
            help = "Numbers of comments to create."
        )

        parser.add_argument(
            "--clear",
            action = "store_true",
            help = "Clear the database before seeding."
        )

    def handle(self, *args, **options: Any) -> None:
        start_time = time.perf_counter()

        users_count: int = options ["users"]
        clear: bool = options["clear"]
        comments_count: int = options["comments"]
        posts_count: int = options["posts"]

        if min(users_count, posts_count, comments_count) < 1:
            raise CommandError("Users, posts and comments must be greater than 0.")

        with transaction.atomic():
            if clear:
                self.clear_data()

            users_created = self.create_users(users_count)
            categories_created = self.create_categories()
            tags_created = self.create_tags()

            users = list(User.objects.all())

            if posts_count > 0 and not users:
                raise CommandError("You must create users before creating posts.")

            posts_created = self.create_posts(posts_count, users)

            published_posts = list(Post.objects.filter(status = Post.Status.PUBLISHED))

            if comments_count > 0 and not published_posts:
                raise CommandError("You must create published posts before creating comments.")

            comments_created = self.create_comments(comments_count, published_posts, users)

            elapsed = time.perf_counter() - start_time

            self.stdout.write(
                self.style.SUCCESS(
                    f"Users:     {users_created:>5} created"
                )
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Categories:     {categories_created:>5} created"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Tags:     {tags_created:>5} created"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Posts:     {posts_created:>5} created"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Comments:     {comments_created:>5} created"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done in:     {elapsed:.2f} seconds"
                )
            )            


    def clear_data(self) -> None:
        self.stdout.write(self.style.WARNING("Clearing data..."))
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Data cleared."))


    def create_users(self, count: int) -> int:

        fake = Faker()

        used_emails = set(
            User.objects.values_list("email", flat=True)
        )

        password_hash = make_password(SEED_PASSWORD)

        users = []

        for _ in range (count):
            first_name = fake.first_name()
            last_name = fake.last_name()

            base_email = (f"{slugify(first_name)}.{slugify(last_name)}@example.com")

            email = base_email

            suffix = 2

            while email in used_emails:
                email = f"{slugify(first_name)}.{slugify(last_name)}{suffix}@example.com"
                suffix += 1

            used_emails.add(email)

            users.append(
                User(
                    email = email,
                    first_name = first_name,
                    last_name = last_name,
                    password = password_hash,
                    is_active = random.random() >= 0.15,
                    is_staff = random.random() < 0.05,
                )
            )

            User.objects.bulk_create(users)

            return len(users)

    def create_categories(self) -> int:
                existing_names = set(Category.objects.values_list("name", flat=True))
    
                existing_slugs = set(Category.objects.values_list("slug", flat=True))
    
                categories = []
    
                for name in CATEGORIES:
                    slug = slugify(name)
    
                    if name in existing_names or slug in existing_slugs:
                        continue
    
                    categories.append(
                        Category(
                            name = name,
                            slug = slug
                        )
                    )
    
                    existing_names.add(name)
                    existing_slugs.add(slug)
    
                Category.objects.bulk_create(categories)
    
                return len(categories)
    
    
    def create_tags(self) -> int:
                existing_names = set(Tag.objects.values_list("name", flat=True))
                
                existing_slugs = set(Tag.objects.values_list("slug", flat=True))
    
                tags = []
    
                for name in TAGS:
                    slug = slugify(name)
                    
                    if name in existing_names or slug in existing_slugs:
                        continue
    
                    tags.append(
                        Tag(
                            name = name,
                            slug = slug 
                        )
                    )
    
                    existing_names.add(name)
                    existing_slugs.add(slug)
    
                Tag.objects.bulk_create(tags)
    
                return len(tags)
    
    def create_posts(self, count: int, users: list[User]) -> int:
                fake = Faker()
    
                categories = list(Category.objects.all())
                tags = list(Tag.objects.all())
    
                used_slugs = set(
                    Post.objects.values_list("slug", flat=True)
                )
    
                posts = []
    
                for _ in range(count):
                    title = fake.sentence(nb_words = 6)[:100].rstrip(".")
    
                    base_slug = slugify(title)
                    slug = base_slug
    
                    suffix = 2
    
                    while slug in used_slugs: 
                        slug = f"{base_slug}-{suffix}"
                        suffix+=1
    
                    used_slugs.add(slug)
    
                    body = "\n\n".join(fake.paragraphs(nb = 3))
    
                    category = None
    
                    if (categories and random.random() < 0.9):
                        category = random.choice(categories)
    
                    status = random.choices(
                        [Post.Status.PUBLISHED, Post.Status.DRAFT],
                        weights = [0.7, 0.3],
                        k=1,
                    )[0]
    
                    posts.append(
                        Post(
                            author = random.choice(users),
                            title = title,
                            slug = slug,
                            body = body,
                            category = category,
                            status = status
                        )
                    )
    
                Post.objects.bulk_create(posts)
    
                for post in posts:
                    tags_count = random.randint(0, min(5, len(tags)))
    
                    selected_tags = random.sample(tags, k=tags_count)
    
                    post.tags.set(selected_tags)
    
                return len(posts)
    
    def create_comments(self, count: int, published_posts: list, users: list ) -> int:
                fake = Faker()
    
                comments = []
    
                for _ in range(count):
                    sentences_count = random.randint(1, 3)
    
                    body = " ".join(fake.sentences(nb = sentences_count))
    
                    comments.append(
                        Comment(
                            post = random.choice(published_posts),
                            author = random.choice(users),
                            body = body
                        )
                    )
    
                    Comment.objects.bulk_create(comments)
    
                    return len(comments)