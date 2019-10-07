from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import EventsAPIView, ObtainTokenPairView, VolunteerAPIView, VolunteerEventsAPIView

urlpatterns = [
    path('events/', EventsAPIView.as_view()),
    path('token/', ObtainTokenPairView.as_view()),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('volunteer/', VolunteerAPIView.as_view()),
    path('volunteer/events/', VolunteerEventsAPIView.as_view()),
]
