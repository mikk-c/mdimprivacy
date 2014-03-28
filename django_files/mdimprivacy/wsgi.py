import os, sys

import django.conf
django.conf.ENVIRONMENT_VARIABLE = "MDIM_DJANGO_SETTINGS_MODULE"

os.environ.setdefault("MDIM_DJANGO_SETTINGS_MODULE", "mdimprivacy.settings")

sys.path.append('/srv/www/mdimprivacy/django_files/')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
