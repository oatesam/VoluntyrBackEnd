from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import OrganizationSignupAPIView, VolunteerSignupAPIView, \
    VolunteerEventsAPIView, OrganizationEventsAPIView, ObtainTokenPairView, OrganizationAPIView, VolunteerAPIView, \
    CheckEmailAPIView, VolunteerEventSignupAPIView, SearchEventsAPIView, OrganizationEventAPIView, OrganizationEmailVolunteers

# [Done] TODO: Update frontend organization dashboard to use org/events/

urlpatterns = [
    path('token/', ObtainTokenPairView.as_view()),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/organization/', OrganizationSignupAPIView.as_view()),
    path('signup/volunteer/', VolunteerSignupAPIView.as_view()),
    path('signup/checkemail/', CheckEmailAPIView.as_view()),
    path('volunteer/', VolunteerAPIView.as_view()),
    path('volunteer/events/', VolunteerEventsAPIView.as_view()),
    path('organization/', OrganizationAPIView.as_view()),
    path('organization/events/', OrganizationEventsAPIView.as_view()),
    path('organization/event/', OrganizationEventAPIView().as_view()),
    path('events/', SearchEventsAPIView.as_view()),
    path('event/<int:event_id>/volunteer/', VolunteerEventSignupAPIView.as_view()),
    path('event/<int:event_id>/email/', OrganizationEmailVolunteers.as_view()),
]

