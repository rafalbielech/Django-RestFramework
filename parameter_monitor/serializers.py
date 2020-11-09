from rest_framework import serializers
from django.utils import timezone
from .models import *

class ParameterSerializer(serializers.ModelSerializer):
    timestamp_format = serializers.SerializerMethodField()
    
    class Meta:
        model = ParameterMonitor
        fields = ['timestamp_format', 'url_upload', 'location', 'latency','download','upload', 'cpu_percent_5_min','cpu_percent_15_min','cpu_temperature', 'memory_total','memory_used','memory_free','memory_free_percentage','disk_total','disk_used','disk_free','disk_free_percentage','boot_time','num_pids']

    def get_timestamp_format(self, obj):
        return obj.reading_timestamp.astimezone(tz=timezone.get_current_timezone()).strftime("%m/%d/%Y %H:%M:%S")