from rest_framework import permissions, status, viewsets
from .models import *
from .serializers import *


class ParameterViewSet(viewsets.ModelViewSet):
    """
    Parameter Monitor can be retrieved or updated using this functionality
    Allowed functions are GET and POST
    """

    queryset = ParameterMonitor.objects.all().order_by("-reading_timestamp")[:20]
    serializer_class = ParameterSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get"]
