from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(method='get', 
                     operation_description="Health check endpoint that returns the status of the application.",
                     responses={200: openapi.Response('OK', schema=openapi.Schema(
                         type=openapi.TYPE_OBJECT,
                         properties={
                             'status': openapi.Schema(type=openapi.TYPE_STRING, description='Status of the application')
                         }
                     ))})
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    # You can add DB checks or other services here
    return Response({"status": "ok"})

