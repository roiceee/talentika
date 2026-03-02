from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import countrystatecity_countries as csc


@swagger_auto_schema(
    method="get",
    tags=["Geo"],
    operation_summary="List all countries",
    responses={
        200: openapi.Response(
            description="List of countries",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "iso2": openapi.Schema(type=openapi.TYPE_STRING),
                        "name": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        )
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def countries(request):
    data = [
        {"iso2": c.iso2, "name": c.name, "phone_code": c.phone_code, "emoji": c.emoji}
        for c in csc.get_countries()
    ]
    return JsonResponse(data, safe=False)


@swagger_auto_schema(
    method="get",
    tags=["Geo"],
    operation_summary="List states/provinces for a country",
    manual_parameters=[
        openapi.Parameter(
            "country_code",
            openapi.IN_PATH,
            description="ISO-2 country code (e.g. US)",
            type=openapi.TYPE_STRING,
        )
    ],
    responses={
        200: openapi.Response(
            description="List of states",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "iso2": openapi.Schema(type=openapi.TYPE_STRING),
                        "name": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        )
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def states(request, country_code):
    data = [
        {"iso2": s.state_code, "name": s.name}
        for s in csc.get_states_of_country(country_code.upper())
    ]
    return JsonResponse(data, safe=False)


@swagger_auto_schema(
    method="get",
    tags=["Geo"],
    operation_summary="List cities for a state/province",
    manual_parameters=[
        openapi.Parameter(
            "country_code",
            openapi.IN_PATH,
            description="ISO-2 country code (e.g. US)",
            type=openapi.TYPE_STRING,
        ),
        openapi.Parameter(
            "state_code",
            openapi.IN_PATH,
            description="State/province code (e.g. CA)",
            type=openapi.TYPE_STRING,
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of cities",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "name": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        )
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def cities(request, country_code, state_code):
    data = [
        {"name": c.name}
        for c in csc.get_cities_of_state(country_code.upper(), state_code.upper())
    ]
    return JsonResponse(data, safe=False)
