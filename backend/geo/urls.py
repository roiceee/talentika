from django.urls import path
from . import views

urlpatterns = [
    path("geo/countries/", views.countries, name="geo-countries"),
    path(
        "geo/countries/<str:country_code>/states/",
        views.states,
        name="geo-states",
    ),
    path(
        "geo/countries/<str:country_code>/states/<str:state_code>/cities/",
        views.cities,
        name="geo-cities",
    ),
]
