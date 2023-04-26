from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email')
    list_filter = ('username', 'email')
    empty_value_display = '-empty-'


admin.site.register(User, UserAdmin)
