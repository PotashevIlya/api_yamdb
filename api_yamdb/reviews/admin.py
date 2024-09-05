from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, Comment, Genre, Review, Title, YaMDBUser


class YaMDBUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Разграничение прав', {'fields': ('role',)}),
        ('Дополнительная инофрмация', {'fields': ('bio',)}),
    )


admin.site.register(YaMDBUser, YaMDBUserAdmin)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Genre)
admin.site.register(Review)
admin.site.register(Title)
