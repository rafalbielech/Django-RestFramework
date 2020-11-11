from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authentication import get_authorization_header
from rest_framework import permissions, status, viewsets
from django.core.exceptions import PermissionDenied
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .models import *
import datetime

identifier_param = openapi.Parameter(
    "identifier",
    openapi.IN_QUERY,
    default="",
    description="Identifier",
    type=openapi.TYPE_STRING,
)

usage_param = openapi.Parameter(
    "usage",
    openapi.IN_QUERY,
    default="",
    description="usage",
    type=openapi.TYPE_STRING,
)


@swagger_auto_schema(
    method="POST",
    manual_parameters=[identifier_param, usage_param],
    responses={
        200: AccessTokenSerializer,
        400: "Error generating token",
    },
)
@api_view(["POST"])
def generateToken(request):
    """
    Generate new token

    Route responsible for generating new token and storing it in the database
    """
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
    identifier = request.GET.get("identifier", None)
    usage = request.GET.get("usage", None)
    if identifier is None or usage is None or AccessToken.objects.filter(identifier=identifier).exists():
        return Response(
            {"detail": "Identifier and usage are required or may not be created"}, status=status.HTTP_400_BAD_REQUEST
        )
    else:
        refresh = RefreshToken.for_user(request.user)
        access_token = refresh.access_token
        access_token.set_exp(lifetime=datetime.timedelta(days=365))
        new_entry = AccessToken(
            identifier=identifier,
            usage=usage,
            valid_until=datetime.datetime.fromtimestamp(access_token["exp"]),
            access_token=str(access_token),
        )
        new_entry.save()
        serializer = AccessTokenSerializer(new_entry)
        return Response(serializer.data)
