from django.db import models
from django.utils.timezone import now
from rest_framework import serializers

# Create your models here.


class AccessToken(models.Model):
    identifier = models.CharField(null=False, max_length=20, primary_key=True)
    usage = models.TextField()
    valid = models.BooleanField(default=True)
    valid_until = models.DateTimeField(default=now)
    access_token = models.TextField()
    last_used = models.DateTimeField(default=now)

    def __str__(self):
        return "Token usage |{}| - valid? |{} until {}".format(
            self.usage, self.valid, self.valid_until.strftime("%d/%m/%Y")
        )


class AccessTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessToken
        fields = ["identifier", "usage", "valid", "valid_until", "access_token"]
