from rest_framework import serializers
from .models import *


class ParameterSerializer(serializers.ModelSerializer):
    timestamp_format = serializers.SerializerMethodField()

    class Meta:
        model = GeneralSystemParameter
        fields = "__all__"

    def get_timestamp_format(self, obj):
        return obj.reading_timestamp.strftime("%m/%d/%Y %H:%M:%S")


class NetworkSerializer(serializers.ModelSerializer):
    timestamp_format = serializers.SerializerMethodField()

    class Meta:
        model = NetworkStat
        fields = "__all__"

    def get_timestamp_format(self, obj):
        return obj.reading_timestamp.strftime("%m/%d/%Y %H:%M:%S")