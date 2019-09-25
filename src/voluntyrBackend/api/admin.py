from django.contrib import admin
from .models import Organization, Event

# Register your models here.
admin.site.register(Organization)
admin.site.register(Event)
