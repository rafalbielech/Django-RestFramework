from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.authentication import get_authorization_header
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import psutil
import multiprocessing
import datetime
import os
from .prep import *
from .serializers import *
from jwtauth.models import *
from .models import *
from scapy.all import getmacbyip

delay_param = openapi.Parameter(
    "delay",
    openapi.IN_QUERY,
    default=15,
    description="Amount of time to delay start of camera",
    enum=[0, 15, 30, 90, 180],
    type=openapi.TYPE_STRING,
)


@api_view(["GET"])
def getRTSPcamstatus(request):
    """
    Get RTSP camera status
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
        elif "Basic" in token_list:
            originator = request.user
    except:
        raise PermissionDenied()

    rtsp_cameras_on_network = [
        item.get("id")
        for item in settings.CONFIG.get("local", {}).get("rtsp_camera", [])
        if getmacbyip(item.get("ip")) != None
    ]
    return Response(rtsp_cameras_on_network, status=status.HTTP_200_OK)


@api_view(["PUT"])
def reset_status(request):
    """
    Reset Surveillance state

    Route responsible for resetting the cameras state
    Return status of the operation
    """
    token = get_authorization_header(request).decode("utf-8")
    " token_list[0] is either Basic or Bearer token_list[1] is actual token "
    token_list = token.split(" ")

    camera_status = get_object_or_404(CameraStatus)
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
        elif "Basic" in token_list:
            originator = request.user
    except:
        raise PermissionDenied()
    camera_status.status = False
    camera_status.update_timestamp = datetime.datetime.now()
    camera_status.pid = -999
    camera_status.save()

    return Response({"detail": "Success"}, status=status.HTTP_200_OK)


class StartSurveillance(APIView):
    """
    Start camera system
    """

    @swagger_auto_schema(
        operation_summary="Start surveillance",
        operation_description="Start surveillance system \n Input : Delay (seconds) default 15 \n Returns : status",
        manual_parameters=[delay_param],
        responses={
            200: '{"success": "Boolean", "status": "String", "start_time": "Datetime object"}',
            404: "You are not authorized to see this content",
        },
    )
    def post(self, request):
        """
        If there is a delay param, delay the start of the surveillance system
        Get token to check if access token was pased, basic token is passed with login authentication
        """

        delay = int(request.GET.get("delay", 15))
        token = get_authorization_header(request).decode("utf-8")
        " token_list[0] is either Basic or Bearer token_list[1] is actual token "
        token_list = token.split(" ")

        originator = ""
        return_data = {}
        camera_status = get_object_or_404(CameraStatus)

        try:
            " If it is a JWT token, then check if this is still valid "
            if "Bearer" in token_list:
                obj = get_object_or_404(AccessToken, access_token=token_list[1])

                if not obj.valid:
                    raise PermissionDenied()
                else:
                    originator = obj.identifier
                    " Get the originator & update last_used date "
                    obj.last_used = datetime.datetime.now()
                    obj.save()
            elif "Basic" in token_list:
                originator = request.user
        except:
            raise PermissionDenied()

        if not psutil.pid_exists(int(camera_status.pid)):
            try:
                ## start the process
                process = multiprocessing.Process(
                    target=person_detector.start_system,
                    args=(delay,),
                )
                process.start()

                camera_status.status = True
                camera_status.update_timestamp = datetime.datetime.now()
                camera_status.pid = process.pid
                camera_status.save()

                history_item = CameraHistory(
                    user=originator,
                    update_timestamp=datetime.datetime.now(),
                    command="Start camera",
                )
                history_item.save()

                return_data["success"] = True
                return_data["system_running"] = True
                return_data["status"] = "System is executing {}".format(camera_status.pid)
                return_data["start_time"] = (datetime.datetime.now() + datetime.timedelta(seconds=delay)).strftime(
                    "%m/%d/%Y, %H:%M:%S"
                )

            except Exception as e:
                return_data["success"] = False
                return_data["system_running"] = False
                return_data["status"] = "ERROR while starting new process - {}".format(e)

        else:
            return_data["success"] = False
            return_data["system_running"] = True
            return_data["status"] = "System is already running"
        return Response(return_data, status=status.HTTP_200_OK)


class StopSurveillance(APIView):
    """
    Stop camera system
    """

    def kill_all_process(self, pid):
        " First kill all of the pid children "
        " Then, kill the parent process "
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()

    @swagger_auto_schema(
        operation_summary="Stop surveillance",
        operation_description="Stop surveillance system \n Input : None \n Returns : status",
        responses={
            200: '{"success": "Boolean", "status": "String", "stop_time": "Datetime object"}',
            404: "You are not authorized to see this content",
        },
    )
    def post(self, request):
        """
        Stop the surveillance system
        Get token to check if access token was passed, basic token is passed with login authentication
        """
        token = get_authorization_header(request).decode("utf-8")
        " token_list[0] is either Basic or Bearer token_list[1] is actual token "
        token_list = token.split(" ")

        originator = ""
        return_data = {}
        camera_status = get_object_or_404(CameraStatus)

        try:
            " If it is a JWT token, then check if this is still valid "
            if "Bearer" in token_list:
                obj = get_object_or_404(AccessToken, access_token=token_list[1])

                if not obj.valid:
                    raise PermissionDenied()
                else:
                    originator = obj.identifier
                    " Get the originator & update last_used date "
                    obj.last_used = datetime.datetime.now()
                    obj.save()
            elif "Basic" in token_list:
                originator = request.user
        except:
            raise PermissionDenied()

        if psutil.pid_exists(int(camera_status.pid)):
            try:
                self.kill_all_process(int(camera_status.pid))

                camera_status.status = False
                camera_status.update_timestamp = datetime.datetime.now()
                camera_status.pid = -999
                camera_status.save()

                history_item = CameraHistory(
                    user=originator,
                    update_timestamp=datetime.datetime.now(),
                    command="Stop camera",
                )
                history_item.save()

                return_data["success"] = True
                return_data["status"] = "System stopped ..."
                return_data["running"] = False
                return_data["stop_time"] = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

            except Exception as e:
                return_data["success"] = False
                return_data["running"] = True
                return_data["status"] = "ERROR while stopping system - {}".format(e)
        else:
            return_data["success"] = False
            return_data["running"] = False
            return_data["status"] = "System was off"
        return Response(return_data, status=status.HTTP_200_OK)


class StatusViewSet(viewsets.ViewSet):
    """
    Return surveillance status
    """

    @swagger_auto_schema(
        operation_summary="System status",
        operation_description="Return system status \n Input : None \n Returns : camera history",
        responses={200: cameraStatusSerializer(many=False), 404: "You are not authorized to see this content"},
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

        camera_status = get_object_or_404(CameraStatus)
        serializer = cameraStatusSerializer(camera_status, many=False)
        serializer_data = serializer.data
        serializer_data["system_running"] = psutil.pid_exists(int(serializer_data.get("pid")))
        return Response(serializer_data)


class DetectionViewSet(viewsets.ViewSet):
    """
    Return detections
    """

    @swagger_auto_schema(
        operation_summary="Surveillance system detections",
        operation_description="Return detection history \n Input : None \n Returns : camera detection history",
        responses={200: cameraDetectionSerializer(many=True), 404: "You are not authorized to see this content"},
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
        queryset = CameraDetection.objects.all().order_by("-timestamp")[:50]
        serializer = cameraDetectionSerializer(queryset, many=True)
        return Response(serializer.data)


class HistoryViewSet(viewsets.ViewSet):
    """
    Return list of commands executed
    """

    @swagger_auto_schema(
        operation_summary="Surveillance commands history",
        operation_description="Return history of called commands \n Input : None \n Returns : camera command history",
        responses={200: cameraHistorySerializer(many=True), 404: "You are not authorized to see this content"},
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
        queryset = CameraHistory.objects.all().order_by("-update_timestamp")[:50]
        serializer = cameraHistorySerializer(queryset, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ViewSet):
    """
    List internal messages passed
    """

    @swagger_auto_schema(
        operation_summary="Messsage passing activity",
        operation_description="Return messages that have been recorded \n Input : None \n Returns : list of messages",
        responses={200: messageSerializer(many=True), 404: "You are not authorized to see this content"},
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
        queryset = Message.objects.all().order_by("-timestamp")[:50]
        serializer = messageSerializer(queryset, many=True)
        return Response(serializer.data)


class ThreadActivityViewSet(viewsets.ViewSet):
    """
    List ThreadActivity
    """

    @swagger_auto_schema(
        operation_summary="Thread activity",
        operation_description="Return recorded thread activity  \n Input : None \n Returns : list of activities",
        responses={200: threadActivitySerializer(many=True), 404: "You are not authorized to see this content"},
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
        queryset = ThreadActivity.objects.all().order_by("-timestamp")[:50]
        serializer = threadActivitySerializer(queryset, many=True)
        return Response(serializer.data)
