from django.db import models
from django.utils.timezone import now
from django.utils import timezone

# Create your models here.


class FanState(models.Model):
    cpu_temperature = models.FloatField(default=0.0)
    reading_timestamp = models.DateTimeField(default=now)
    fan_state = models.BooleanField(default=False)

    def __str__(self):
        return "Fan status: {} | Reading date: {} | CPU temp (C): {}".format(
            self.fan_state, self.reading_timestamp.strftime("%m/%d/%Y, %H:%M:%S"), self.cpu_temperature
        )
