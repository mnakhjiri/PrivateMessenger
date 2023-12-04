from django.db import models

from utils.models import BaseModel


class UserInfo(BaseModel):
    chat_id = models.IntegerField(unique=True)
    is_active = models.BooleanField(default=True)
    allow_anonymous_contact = models.BooleanField(default=False)
    last_interaction = models.DateTimeField(blank=True, null=True)
    superuser = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    silent_notifications = models.BooleanField(default=False)

    def __str__(self):
        return f"User {self.id}"

    @staticmethod
    def get_super_users():
        return UserInfo.objects.filter(superuser=True)

    @staticmethod
    def get_super_users_chat_ids():
        return UserInfo.get_super_users().values_list('chat_id', flat=True)
