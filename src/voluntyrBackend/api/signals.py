from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mass_mail
from django.core.mail import send_mail
import django.dispatch
from django.utils import timezone
from .urlTokens.token import URLToken

from api.models import Event
# create custom signal for when volunteer sign up for event
signal_volunteer_signed_up_event = django.dispatch.Signal(providing_args=["vol_id", "event_id"])


@receiver(signal_volunteer_signed_up_event)
def volunteer_signed_up_event_handler(sender, **kwargs):
    vol_id = kwargs["vol_id"]
    event_id = kwargs["event_id"]
    event = Event.objects.get(id=event_id)
    volunteer = kwargs["volunteer"]
    suggesting_events = _make_suggest_events_list(vol_id, event_id, volunteer)
    email = [volunteer.end_user.email]
    subject = "Thank you for registering to volunteer with " + event.organization.name
    message = generate_suggestion_email_message(suggesting_events, email, event_id)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, email)


@receiver(post_save, sender=Event)
def edit_handler(sender, **kwargs):
    if not kwargs['created'] and 'volunteers' not in kwargs['update_fields']:
        event = kwargs['instance']

        volunteer_emails = _get_volunteer_emails(event=event)
        subject = event.organization.name + " update their " + event.title + " event."
        message = "You are receiving this message because you are registered for this event and the organizer has " \
                  "updated some details about the event. \nPlease find a link to the updated event below.\n\n" \
                  "\nYour event: https://voluntyr.herokuapp.com/Event/" + str(event.id)

        emails = _make_emails(volunteer_emails, settings.DEFAULT_FROM_EMAIL, subject, message)
        send_mass_mail(emails)


def _get_volunteer_emails(event):
    volunteers = event.volunteers.all()
    emails = []
    for volunteer in volunteers:
        emails.append(volunteer.end_user.email)
    return emails


def _make_emails(to_emails, from_email, subject, message):
    """
    Builds a tuple of the emails to send
    :param to_emails: List of volunteer emails
    :param from_email: From email address
    :param subject: Subject of the emails
    :param message: Message of the emails
    :return: Tuple of the emails to send
    """
    emails = []
    for volunteer in to_emails:
        emails.append((subject, message, from_email, [volunteer]))
    return tuple(emails)


def _make_suggest_events_list(vol_id, event_id, volunteer):
    event_lst = []
    current_event = Event.objects.get(id=event_id)
    events = Event.objects.all().filter(start_time__gte=timezone.now())
    for event in events:
        if event.organization == current_event.organization and volunteer not in event.volunteers.all():
            event_lst.append(event)
    if len(event_lst) < 3:
        for event in events:
            if volunteer not in event.volunteers.all():
                event_lst.append(event)
    if len(event_lst) > 3:
        event_lst = event_lst[:3]
    return event_lst


def generate_suggestion_email_message(suggesting_events, email, event_id):
    current_event = Event.objects.get(id=event_id)
    message = "Thank you for registering for " + str(current_event.title) +\
              " organized by " + str(current_event.organization)
    if len(suggesting_events) > 0:
        message += "\n\nWe have found " + str(len(suggesting_events)) + " other volunteer opportunities that you may " \
                                                                        "be interested in: "
        for event in suggesting_events:
            token = _generate_invite_code(event_id=event.id)
            message += "\n" +\
                       str(event.title) + " at " + str(event.location) + " organized by " + str(event.organization) \
                       + ".\n"\
                       "The event starts on " + event.start_time.strftime("%m/%d/%Y %I:%M %p") + " and end on "\
                       + event.end_time.strftime("%m/%d/%Y %I:%M %p") + "\n" \
                       "Here is the description of the event: " + str(event.description) + "\n" \
                       "If you are interested, you can register by clicking"\
                       " the invitation link below: \n" + settings.FRONTEND_HOST+"/Invite/"+token
    return message


def _generate_invite_code(event_id):
    token = URLToken(data={"event_id": event_id})
    return token.get_token()



