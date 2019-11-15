from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import OrganizationSignupAPIView, VolunteerSignupAPIView, \
    VolunteerEventsAPIView, OrganizationEventsAPIView, ObtainTokenPairView, OrganizationAPIView, VolunteerAPIView, \
    CheckEmailAPIView, VolunteerEventSignupAPIView, SearchEventsAPIView, OrganizationEventAPIView, \
    OrganizationEmailVolunteers, CheckSignupAPIView, EventVolunteers, EventDetailAPIView, \
    OrganizationEventUpdateAPIView, VolunteerOrganizationAPIView, VolunteerEventAPIView, InviteVolunteersAPIView, \
    InviteAPIView


urlpatterns = [
    path('token/', ObtainTokenPairView.as_view()),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/organization/', OrganizationSignupAPIView.as_view()),
    path('signup/volunteer/', VolunteerSignupAPIView.as_view()),
    path('signup/checkemail/', CheckEmailAPIView.as_view()),
    path('volunteer/', VolunteerAPIView.as_view()),
    path('volunteer/events/', VolunteerEventsAPIView.as_view()),
    path('volunteer/event/<int:event_id>/', VolunteerEventAPIView.as_view()),
    path('organization/', OrganizationAPIView.as_view()),
    path('organization/<int:org_id>/', VolunteerOrganizationAPIView.as_view()),
    path('organization/events/', OrganizationEventsAPIView.as_view()),
    path('organization/event/', OrganizationEventAPIView().as_view()),
    path('events/', SearchEventsAPIView.as_view()),
    path('event/<int:event_id>/volunteer/', VolunteerEventSignupAPIView.as_view()),
    path('event/<int:event_id>/email/', OrganizationEmailVolunteers.as_view()),
    path('event/<int:event_id>/check/', CheckSignupAPIView.as_view()),
    path('event/<int:event_id>/volunteers/', EventVolunteers.as_view()),
    path('event/<int:event_id>/invite/', InviteVolunteersAPIView.as_view()),
    # path('invite/<url_key:invite_code>/', InviteAPIView.as_view()),  # TODO: Story-59; use URLToken Converter
    path('organization/event/<int:event_id>/', EventDetailAPIView.as_view()),
    path('organization/updateEvent/', OrganizationEventUpdateAPIView.as_view()),
]

