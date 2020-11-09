from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.authentication import get_authorization_header
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from .serializers import *
from jwtauth.models import *
from .models import *


class FanStateViewSet(viewsets.ViewSet):
    """
    List Fan States
    """

    @swagger_auto_schema(
        operation_summary="Fan State",
        operation_description="Return fan state history  \n Input : None \n Returns : list of fan states",
    )
    def list(self, request):
        token = get_authorization_header(request).decode("utf-8")
        " token_list[0] is either Basic or Bearer token_list[1] is actual token "
        token_list = token.split(" ")

        try:
            " If it is a JWT token, then check if this is still valid "
            if "Bearer" in token_list:
                obj = get_object_or_404(AccessToken, access_token=token_list[1])

                if not obj.valid:
                    raise PermissionDenied()
                else:
                    " Get the originator & update last_used date "
                    obj.last_used = datetime.datetime.now()
                    obj.save()
        except:
            raise PermissionDenied()
        queryset = FanState.objects.all().order_by("-timestamp")[:50]
        serializer = FanStateSerializer(queryset, many=True)
        return Response(serializer.data)