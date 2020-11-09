from django.urls import path, include
from rest_framework import routers
from .views import *

urlpatterns = [
    path("action/reset/", reset_status),
    path("action/start/", StartSurveillance.as_view()),
    path("action/stop/", StopSurveillance.as_view()),
]

router = routers.DefaultRouter()
router.register(r"detection", DetectionViewSet, basename="detection")
router.register(r"status", StatusViewSet, basename="status")
router.register(r"command_history", HistoryViewSet, basename="history")
router.register(r"message", MessageViewSet, basename="message")
router.register(r"threadactivity", ThreadActivityViewSet, basename="threads")

urlpatterns += router.urls
