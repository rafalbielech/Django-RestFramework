"""django_node_RF URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def redirect_to_docs(request):
    response = redirect("schema-swagger-ui")
    return response


schema_view = get_schema_view(
    openapi.Info(
        title="Home automation | Ubuntu | by Rafał Bielech",
        default_version="v1",
        description="Home Automation API for {}\n This project originated to create an API responsible for monitoring internally developed surveillance system and node parameters. \nAuthentication methods : Basic & Bearer token \n<hr>\n<a target='_blank' href='https://rafalbielech.github.io'>Learn more about developer</a>".format(
            settings.CONFIG.get("local", {}).get("alias", "EMPTY")
        ),
        contact=openapi.Contact(email="rraafaall@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticatedOrReadOnly,),
)

urlpatterns = [
    path("", redirect_to_docs),
    path("api/token/", include("jwtauth.urls")),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/camera/", include("camera.api")),
    path("api/parameter/", include("parameter_monitor.api")),
    path("console/admin/", admin.site.urls),
]


if settings.CONFIG.get("local", {}).get("django_settings", {}).get("include_fan", "False") == "True":
    urlpatterns.append(path("api/fan/", include("fan_control.api")))