from django.urls import path, include
from rest_framework import routers
from django.conf import settings
from .views import *

urlpatterns = [
    path("action/reset/", reset_status),
    path("action/start/", StartSurveillance.as_view()),
    path("action/stop/", StopSurveillance.as_view()),
]

if len(settings.CONFIG.get("local", {}).get("rtsp_camera", [])) >= 1:
    urlpatterns += path("action/rtsp/status", getRTSPcamstatus)

router = routers.DefaultRouter()
router.register(r"detection", DetectionViewSet, basename="detection")
router.register(r"status", StatusViewSet, basename="status")
router.register(r"command_history", HistoryViewSet, basename="history")
router.register(r"message", MessageViewSet, basename="message")
router.register(r"threadactivity", ThreadActivityViewSet, basename="threads")

urlpatterns += router.urls
