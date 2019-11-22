from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mass_mail


from .models import Event


@receiver(post_save, sender=Event)
def edit_handler(sender, **kwargs):
    if not kwargs['created']:
        # TODO: Story-60; Detect and pass updated fields to .save() in update event view, add event to email message
        event = kwargs['instance']
        volunteer_emails = _get_volunteer_emails(event=event)
        subject = event.organization.name + " update their " + event.title + " event."
        message = "You are receiving this message because you are registered for this event and the organizer has " \
                  "updated some details about the event. \nPlease fine the updated event below.\n\n"

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

# post_save.connect(edit_handler, weak=False, dispatch_uid="event_post_save")
