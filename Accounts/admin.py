from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile,Referral,Profession
from django.utils.html import format_html

class AccountAdmin(UserAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "date_of_birth",
        "gender",
        "username",
        "referral",
        "profession",
        "last_login",
        "date_joined",
        "is_active",
    )
    list_display_links = ("email", "first_name", "last_name","date_of_birth","gender",)
    readonly_fields = ("last_login", "date_joined")
    ordering = ("-date_joined",)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class UserProfileAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        if object.profile_picture:
            return format_html('<img src="{}" width="30" style="border-radius:50%;">', object.profile_picture.url)
        return "No Image"
    
    thumbnail.short_description = "Profile Picture"
    list_display = ("thumbnail", "user", "city", "state", "country")


admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Referral)
admin.site.register(Profession)