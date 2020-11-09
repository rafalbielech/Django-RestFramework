from django.urls import include, path 
from rest_framework import routers 
from .views import *


router = routers.DefaultRouter()
router.register(r'fan_state', FanStateViewSet, basename='fan_control')

urlpatterns = router.urls