from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import EventsAPIView, ObtainTokenPairView, OrganizationAPIView, VolunteerAPIView, CheckEmailAPIView, OrganizationInfoAPIView

urlpatterns = [
    path('events/', EventsAPIView.as_view()),
    path('token/', ObtainTokenPairView.as_view()),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/organization/', OrganizationAPIView.as_view()),
    path('signup/volunteer/', VolunteerAPIView.as_view()),
    path('signup/checkemail/', CheckEmailAPIView.as_view()),
    path('organization_info', OrganizationInfoAPIView.as_view())
]

