from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from unfold.sections import TableSection
from unfold.contrib.filters.admin import (AutocompleteSelectFilter, RangeDateTimeFilter, ChoicesDropdownFilter, RelatedDropdownFilter, MultipleRelatedDropdownFilter)
from unfold.contrib.forms.widgets import WysiwygWidget

from django.contrib import admin, messages
from django.db.models import Count, Prefetch
from django.shortcuts import redirect
from django.db import models

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

class CommentInline(TabularInline):
    model = Comment

    fields = [
        "author",
        "body",
        "created_at"
    ]

    readonly_fields = [
        "created_at"
    ]

    extra = 0
    tab = True
    per_page = 10
    show_change_link = True

class PostCommentSection(TableSection):
    verbose_name = "Comments"
    related_name = "comments"
    fields = [
        "author",
        "body",
        "created_at"
    ]
    

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

    autocomplete_fields = [
        "author",
        "category",
        "tags"
    ]

    fieldsets = (
        ("Content", {
            "classes":["tab"],
            "fields": (
                "title",
                "slug",
                "body",
            )
        }),
        ("Classification", {
            "classes": ["tab"],
            "fields": (
                "category",
                "tags",
                "status",
            ),
        }),
        ("Meta", {
            "classes": ["tab"],
            "fields": (
                "author",
                "created_at",
                "updated_at"
            )
        })
    )

    prepupulated_field = {
        "slug": ("title",)
    }

    autocomplete_fields = [
        "author",
        "category",
        "tags"
    ]

    readonly_fields = [
        "created_at",
        "updated_at"
    ]

    forfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        }
    }

    warn_unsaved_form = True

    inlines = [CommentInline]

    list_filter =[
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter)
    ]

    list_sections = [PostCommentSection]
    list_per_page = 20

    list_filter_submit = True

    list_selected_related = [
        "author",
        "category"
    ]

    actions_row = ["toggle_publish"]

    @action(
            description = "Publish / Unpublish",
            icon = "publish"
    )

    def toggle_publish(self, request, object_id):
        post = self.get_object(request, object_id)

        if post is None:
            messages.error(request, "Post not found")
            return redirect("admin:blog_post_changelist")

        if post.status == Post.status.PUBLISHED:
            post.status = Post.status.DRAFT
            messages.success(request, "Post moved to Drafts")
        else:
            post.status = Post.status.PUBLISHED
            messages.success(request, "Post moved to PUBLISHED")

        post.save(update_fields=["status"])

        return redirect("admin:blog_post_changelist")

    actions = [
        "publish_selected",
        "move_to_drafts"
    ]

    @admin.action(description = "Publish selected")
    def publish_selected(self, request, queryset):
        updated = queryset.update(status = Post.status.PUBLISHED)
        messages.success(request, f"{updated} posts updated")

    @admin.action(description = "Move to draft")
    def move_to_draft(self, request, queryset):
        updated = queryset.update(status = Post.status.DRAFT)
        messages.success(request, f"{updated} posts move to draft")

    actions_list = ["publish_all_drafts"]

    @action(
            description = "publish all drafts.",
            icon = "publish"
    )
    def publish_all_drafts(self, request):
        updated = Post.objects.filter(
            status=Post.Status.DRAFT 
        ).update(status = Post.Status.PUBLISHED)

        messages.success(request, f"{updated} draft post published.")

        return redirect("admin:blog_post_changelist")

    def get_queryset(self, request):
        return (
            super().get_queryset(request).annotate(comments_count = Count("comments", distinct = True)).prefetch_related("tags")
        )

    actions_submit_line = ["save_and_publish"]

    @action(
            description = "Save and Publish",
            icon = "check",
            permissions = ["save_and_publish"]
    )
    def save_and_publish(self, request, obj):
        obj.status = Post.Status.PUBLISHED
        obj.save(updated_fields = ["status"])

    def has_save_and_publish_permission(self, request,object_id):
        return request.user.is_staff

    

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