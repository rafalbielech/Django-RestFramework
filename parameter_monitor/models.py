from django.db import models
from django.utils.timezone import now
from django.utils import timezone
# Create your models here.


class ParameterMonitor(models.Model):
    reading_timestamp = models.DateTimeField(default=now)

    url_upload = models.URLField(max_length=200, null=True, blank=True)
    location = models.TextField(default="")
    latency = models.FloatField(default=0.0)
    download = models.FloatField(default=0.0)
    upload = models.FloatField(default=0.0)

    cpu_percent_5_min = models.FloatField(default=0.0)
    cpu_percent_15_min = models.FloatField(default=0.0)
    cpu_temperature = models.FloatField(default=0.0)

    memory_total = models.FloatField(default=0)
    memory_used = models.FloatField(default=0)
    memory_free = models.FloatField(default=0)
    memory_free_percentage = models.FloatField(default=0.0)

    disk_total = models.FloatField(default=0)
    disk_used = models.FloatField(default=0)
    disk_free = models.FloatField(default=0)
    disk_free_percentage = models.FloatField(default=0.0)

    boot_time = models.DateTimeField(default=now)
    num_pids = models.IntegerField(default=0)

    def __str__(self):
        return '| Reading date: {}\n | Internet [ Upload: {} | Download {} ]\n | CPU [ Load: {} | Temp (C) : {} ]\n | Memory [ Percentage Free: {}% ] | Disk [ Percentage Free: {}% ]'.format(self.reading_timestamp.astimezone(tz=timezone.get_current_timezone()).strftime("%m/%d/%Y, %H:%M:%S"), self.download, self.upload, self.cpu_percent_15_min, self.cpu_temperature, self.memory_free_percentage, self.disk_free_percentage)

