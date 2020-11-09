from django.db import models
from django.utils.timezone import now
from django.utils import timezone

# Create your models here.
class CameraStatus(models.Model):
    pid = models.CharField(default="-1", max_length=10)
    status = models.BooleanField(default=False)
    update_timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return "status : {} | updated : {} | pid : {}".format(
            self.status,
            self.update_timestamp.strftime("%m/%d/%Y, %H:%M:%S"),
            self.pid,
        )


class CameraHistory(models.Model):
    user = models.TextField(blank=False, null=True, verbose_name="User initiated camera operation")
    command = models.TextField(blank=True, null=True, verbose_name="Camera operation")
    update_timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return "{} init. command {} @ {}".format(
            self.user,
            self.command,
            self.update_timestamp.strftime("%m/%d/%Y, %H:%M:%S"),
        )


class CameraDetection(models.Model):
    calling_process = models.IntegerField(default=-1)
    timestamp = models.DateTimeField(default=now)
    num_of_captures = models.IntegerField(default=1)
    receiver_address = models.EmailField(max_length=254, default="raaaaafal15@gmail.com")

    def __str__(self):
        return "{} captures sent to {} @ {}".format(
            self.num_of_captures,
            self.receiver_address,
            self.timestamp.strftime("%m/%d/%Y, %H:%M:%S"),
        )


class Message(models.Model):
    function = models.TextField(blank=True, default="NA")
    message = models.TextField(blank=True, default="NA")
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return "Function {} - msg - {} sent @ {}".format(
            self.function, self.message, self.timestamp.strftime("%m/%d/%Y, %H:%M:%S")
        )


class ThreadActivity(models.Model):
    thread_type = models.TextField(blank=True, default="NA")
    attribute_1 = models.TextField(blank=True, default="NA")
    attribute_2 = models.TextField(blank=True, default="NA")
    restart = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return "Type {} : {} @ {} restart ? {}".format(
            self.thread_type, self.attribute_1, self.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), self.restart
        )