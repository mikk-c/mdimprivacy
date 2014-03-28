mdimprivacy
===========

To use this repository:

1. Install Django
2. Install Mysql
3. Set up a mysql database
4. Clone the GIT
5. Create your settings_local.py in the django_files/mdimprivacy/ folder. Instructions about what to include in it are inside the settings.py file.
6. From the django_files directory, run "python manage.py syncdb"
7. Good to go

For now, the templates refer to an incorrect URL on the server where the framework was hosted.
We will fix it, but for now the issue is to host this somewhere accessible to external visitors which can actually mantain the session (in my localhost it works, likely, it's that server/domain which has a messed up cookie system).
To verify it, create an account, login and then refresh the page. If it asks for the login again, it doesn't work!
