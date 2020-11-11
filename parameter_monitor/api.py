from django.urls import include, path
from rest_framework import routers
from .views import *


router = routers.DefaultRouter()
router.register(r"parameter", GeneralParameterViewSet, basename="stat")
router.register(r"network", NetworkViewSet, basename="network")

urlpatterns = router.urls