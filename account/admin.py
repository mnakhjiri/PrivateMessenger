from django.contrib import admin
from account.models import *


# Register your models here.
class UserInfoAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserInfo._meta.fields]


admin.site.register(UserInfo, UserInfoAdmin)
