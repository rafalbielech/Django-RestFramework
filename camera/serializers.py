from rest_framework import serializers
from .models import *


class cameraDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraDetection
        fields = "__all__"


class cameraStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraStatus
        fields = "__all__"


class cameraHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraHistory
        fields = "__all__"


class messageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class threadActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadActivity
        fields = "__all__"