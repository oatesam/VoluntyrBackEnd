from django.contrib import admin
from .models import Organization, Event, Volunteer, EndUser

# Register your models here.
admin.site.register(Organization)
admin.site.register(Event)
admin.site.register(Volunteer)
admin.site.register(EndUser)
