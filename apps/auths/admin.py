from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.forms import AdminPasswordChangeForm


from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


from apps.auths.models import User
from apps.auths.forms import (CustomerUserChangeForm, CustomUserCreationForm)

# Register your models here.
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    change_password_form = AdminPasswordChangeForm
    form = CustomerUserChangeForm
    add_form = CustomUserCreationForm

    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        ("Personal info",{
            "classes":["tab"],
            "fields":(
                "email",
                "first_name",
                "last_name",
                "password"
            )
        }),
        ("Permissions", {
            "classes": ["tab"],
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {
            "classes": ["tab"],
            "fields":(
                "last_login",
            )
        })
    )

    add_fieldsets = (
    ("Personal information", {
        "classes": ["wide"],
        "fields": (
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ),
    }),
)

    list_display = [
        "user_info",
        "is_active",
        "is_staff",
        "post_count"
    ]

    list_filter = [
        ("is_staff", BooleanRadioFilter),
        ("is_active", BooleanRadioFilter)
    ]

    actions = [
        "activate_users",
        "deactivate_users"
    ]

    @admin.action(description= "Activate selected users")
    def activate_users(self, request, queryset):
        queryset.update(is_active = True)

    @admin.action(description= "Deactivate selected users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active = False)

    search_fields = ["email", "first_name", "last_name"]

    def get_queryset(self, request):
        return(
            super().get_queryset(request).annotate(posts_count=Count("post"))
        )

    @display(description = "User", header = True)
    def user_info(self, obj):
        return [
            obj.first_name,
            obj.email
        ]

    @display(
        description = "Active",
        boolean = False,
        label ={
            True:"success",
            False:"danger"
        }
    )
    def is_active(self, obj):
        return obj.is_active

    @display(
        description = "Staff",
        label = {
            True: "info",
            False: "secondary"
        }
    )
    def is_staff(self, obj):
        return obj.is_staff

    @display(description = "Posts", ordering = "posts_count")
    def post_count(self, obj):
        return obj.posts_count

admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass