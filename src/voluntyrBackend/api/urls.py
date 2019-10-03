from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import EventsAPIView, ObtainTokenPairView, OrganizationInfoAPIView

urlpatterns = [
    path('events/', EventsAPIView.as_view()),
    path('token/', ObtainTokenPairView.as_view()),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('organization_info', OrganizationInfoAPIView.as_view())
]

