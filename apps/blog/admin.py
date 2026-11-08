from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.sections import TableSection
from unfold.contrib.filters.admin import (AutocompleteSelectFilter, RangeDateTimeFilter, ChoicesDropdownFilter, RelatedDropdownFilter, MultipleRelatedDropdownFilter)

from django.contrib import admin
from django.db.models import Count, Prefetch

from apps.blog.models import Category, Tag, Post, Comment

# Register your models here.
class CategoryPostsSections(TableSection):
    verbose_name = "Posts in this Category"
    related_name = "posts"
    fields = ["title", "status", "created_at"]

class TagPostsSections(TableSection):
    verbose_name = "Posts with this tag"
    related_name = "posts"
    fields = ["title", "status", "created_at"]

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "slug", "post_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug":["name"]}
    list_sections = [CategoryPostsSections]

    def get_queryset(self, request):
        return (
            super().get_queryset(request).annotate(posts_count = Count("posts", distinct= True))
        )

    @display(description = "Posts", ordering = "posts_count")
    def post_count(self, obj):
        return obj.posts_count

@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ["name", "slug", "post_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug":["name"]}
    list_sections = [TagPostsSections]

    def get_queryset(self, request):
        return (
            super().get_queryset(request).annotate(posts_count = Count("posts", distinct=True))
        )

    @display(description = "Posts", ordering = "posts_count")
    def post_count(self, obj):
        return obj.posts_count


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = [
        "post",
        "author",
        "body_preview",
        "created_at"
    ]

    search_fields = [
        "body",
        "author__email",
        "post__title"
    ]

    list_filter = [
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter)
    ]

    list_filter_submit = True

    autocomplete_fields = ["post", "author"]

    list_select_related = ["post", "author"]

    @display(description = "Comment")
    def body_preview(self, obj):
        if len(obj.body) > 50:
            return obj.body[:50] +"..."
        return obj.body

@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = [
        "post_info",
        "status_label",
        "category",
        "tags_dropdown",
        "comment_count",
        "created_at"
    ]


    search_fields = [
        "title",
        "body",
        "author__email"
    ]

    list_filter =[
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter)
    ]

    list_filter_submit = True

    autocomplete_fields = [
        "author",
        "category",
        "tags"
    ]

    list_selected_related = [
        "author",
        "category"
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request).annotate(comments_count = Count("comments", distinct = True)).prefetch_related("tags")
        )

    @display(description = "Post", header = True)
    def post_info(self, obj):
        author_name = (
            f"{obj.author.first_name} {obj.author.last_name}".strip()
        )

        initials = (
            f"{obj.author.first_name[:1]} {obj.author.last_name[:1]}".upper()
        )

        return [
            obj.title,
            author_name or obj.author.email,
            initials
        ]

    @display(description = "Status",
            label = {
                "published": "success",
                "draft": "Warning"
                }
            )
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    @display(description = "Tags", dropdown = True)
    def tags_dropdown(self, obj):
        tags = list(obj.tags.all())

        return {
            "title": f"{len(tags)} tags",
            "items": [
                {"title": tag.name}
                for tag in tags
            ]
        }

    @display(description = "Comments", ordering = "comments_count")
    def comment_count(self, obj):
        return obj.comments_count