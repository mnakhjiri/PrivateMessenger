from django.contrib import admin
from Messenger.models import *


# Register your models here.
class MessageAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Message._meta.fields]


admin.site.register(Message, MessageAdmin)
