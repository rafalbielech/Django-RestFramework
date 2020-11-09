from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(ThreadActivity)
admin.site.register(CameraStatus)
admin.site.register(CameraHistory)
admin.site.register(CameraDetection)
admin.site.register(Message)
