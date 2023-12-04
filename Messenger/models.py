from django.db import models
import account.models as account_models


class Message(models.Model):
    message_id = models.CharField(max_length=50)
    sender = models.ForeignKey(account_models.UserInfo, on_delete=models.CASCADE, related_name="messages_sent")
    recipient = models.ForeignKey(account_models.UserInfo, on_delete=models.CASCADE, related_name="messages_received")
    expires_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)

    @staticmethod
    def get_inbox(user):
        return Message.objects.filter(recipient=user, is_read=False)


