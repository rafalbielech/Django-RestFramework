from rest_framework import serializers
from .models import *


class cameraDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraDetection
        fields = ["calling_process", "timestamp", "num_of_captures", "receiver_address"]


class cameraStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraStatus
        fields = "__all__"


class cameraHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraHistory
        fields = ["user", "command", "update_timestamp"]


class messageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class threadActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadActivity
        fields = "__all__"