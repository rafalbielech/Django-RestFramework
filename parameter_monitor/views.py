from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.authentication import get_authorization_header
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from jwtauth.models import *
from .models import *
from .serializers import *


class GeneralParameterViewSet(viewsets.ViewSet):
    """
    Return general computer parameter
    """

    @swagger_auto_schema(
        operation_summary="System parameters",
        operation_description="Return general node parameters \n Input : None \n Returns : general parameters history",
        responses={200: ParameterSerializer(many=True), 404: "You are not authorized to see this content"},
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
        queryset = GeneralSystemParameter.objects.all().order_by("-reading_timestamp")[:50]
        serializer = ParameterSerializer(queryset, many=True)
        return Response(serializer.data)


class NetworkViewSet(viewsets.ViewSet):
    """
    Return network data parameter
    """

    @swagger_auto_schema(
        operation_summary="Network parameters",
        operation_description="Return network parameters \n Input : None \n Returns : network parameters",
        responses={200: NetworkSerializer(many=True), 404: "You are not authorized to see this content"},
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
        queryset = NetworkStat.objects.all().order_by("-reading_timestamp")[:50]
        serializer = NetworkSerializer(queryset, many=True)
        return Response(serializer.data)