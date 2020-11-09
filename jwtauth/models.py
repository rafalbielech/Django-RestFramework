from django.db import models
from django.utils.timezone import now
from rest_framework import serializers

# Create your models here.


class AccessToken(models.Model):
    identifier = models.CharField(null=False, max_length=20, primary_key=True)
    usage = models.TextField()
    valid = models.BooleanField(default=True)
    access_token = models.TextField()
    last_used = models.DateTimeField(default=now)

    def __str__(self):
        return "Token usage |{}| - valid? |{}|".format(
            self.usage,
            self.valid,
        )


class AccessTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessToken
        fields = ["identifier", "usage", "valid", "access_token"]