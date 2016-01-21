Subproject
============

Subproject is a Django web application for tracking projects. It supports
logging work and work duration, individual tasks (which can be converted to
projects), user profiles, nested projects, and assigning of work and projects.
Within that, it also provides several different means of viewing and navigating
projects.

Requirements
============
* Python 3
* Django 1.8
* python-dateutil

Usage (Non-Production)
============
* Install the requirements through pip or another means.
* Clone the repository to a local location
* Edit subproject/settings.py to configure your database backend and database
* Run the commands `python manage.py collectstatic` and `python manage.py
syncdb`. Say yes to their prompts and fill out the information they request.
* Run `python manage.py runserver [0.0.0.0:8000]` (the bracketed section is
optional and allows access from outside the local system)

Subproject should be available in browser at localhost:8000.

Usage (Production)
=============
* Follow the same setup steps as non-production, UNTIL you reach the final
command.
* Subproject should be run through a production webserver, using mod_wsgi or
equivalent. Configuration is dependent on your webserver.

License
=============
Subproject is licensed under the GPLv3. The user profile module is licensed
under the BSD license, with source code at
[https://github.com/thenaterhood/django-user](https://github.com/thenaterhood/django-user).

If you find Subproject useful, please consider contributing, providing feedback
or simply dropping a line to say that it  was useful to you.
If you've done something cool, let me know!
