# Voluntyr: Volunteer Management System
## FrontEnd Development Branch

A webapp for volunteer and charitable groups to connect and organize for positive action.

___
By:
- Sam Oates

Collaborators:
- Chenxu Wang
- Charles Frank
- Nikhil Mankame


>#### Disclaimer
>
>This repository is a migration from a version hosted on Indiana University's Enterprise version of Github.
>Webapp was formerly hosted on heroku (https://voluntyr.herokuapp.com/) but discontinued due to expense.

## Components

Frontend - Angular (https://github.com/oatesam/VoluntyrFrontEnd)
 
Backend - Django REST (https://github.com/oatesam/VoluntyrBackEnd)

Database - PostgreSQL (database not included in version control)

Deployment - Heroku (Formerly at https://voluntyr.herokuapp.com/)

### Volunteer Flow
___
The base url would return the landing page, describing the site's functionality and a portal to login to either the volunteer dashboard. The dashboard would allow volunteers to connect with organizations through the Search function, using any number of powerful filters. After signing up for an event, the volunteer is automatically added to an organization-moderated group-message, where orgs can administer more nuanced information and answer any volunteer questions. They are also emailed an invite link to Voluntyr page where the event is posted, allowing a volunteer to invite anyone else to participate.

After attending an event, volunteers have the option to rate both the individual event and the organization as a whole, with both a quantitative assessment and a written review. These reviews are then calculated to adjust an organization's visibility through our search, meaning the better an organization is at delivering positive change to their community, the easier it is to find them on our site.

### Organizer Flow
___
Once authorized, an organizer can create a landing page for their organization. This can include contact information for the organization and also display any past or future events the organization would be running. That same page also show volunteers an organization's description, motto, and ratings from fellow volunteers.

Organizers can post photos to past events, showing what they accomplished. This is both a great way for volunteers to feel validated about their participation and to show new volunteers what exactly they should expect when coming to an event planned by an organization. We implemented a donation button that organizations can connect their PayPal to, making it easy for volunteers who cannot physically participate to still contribute in some way.

### Authorization Flow
___
Our landing page is as simplistic as possible, only asking for an email at first. It then passes the user to registration (if the email is not in the database) or login (if the user is already registered), minimizing keystrokes by automatically passing the email through to the necessary form. Upon completion of the form, users had to complete a ReCaptcha (provided by Google OAuth), and two-factor authentication (provided by Authy).

A user's experience on the site is then dictated by their authorization role as volunteer or organization. Information is conditionally retrieved from the database only after verifying the user's role, maintaining the private connection between volunteers and organizations.


## Future Goals
___
We envision many updates if this project is ever revisited.

- Hour-By-Hour Scheduler
- Implement time-slots for volunteers to choose specific windows to participate
- Allow volunteers to exchange time-slots
- Enhance user experience
