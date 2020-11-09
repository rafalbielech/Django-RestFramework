from rest_framework import serializers
from .models import *


class FanStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FanState
        fields = "__all__"
