import sys
import os
# set the environment variables to be used by the wsgi app
os.environ['ENVIRONMENT'] = ''
os.environ['S3_ROLE'] = ''
os.environ['S3_BUCKET'] = ''
os.environ['AWS_ACCESS_KEY_ID'] = ''
os.environ['AWS_SECRET_ACCESS_KEY'] = ''
# the venv Python interpreter
sys.path.insert(0, '/home/ubuntu/RO-Covid-vaccines/CovidDash/venv/lib/python3.8/site-packages')
sys.path.insert(0, '/var/www/html/dashboard')
from dashboard import server as application