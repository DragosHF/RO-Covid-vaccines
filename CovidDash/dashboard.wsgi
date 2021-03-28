#! /usr/bin/python3
import sys
import os
os.environ['ENVIRONMENT'] = ''
sys.path.insert(0, '/home/ubuntu/RO-Covid-vaccines/CovidDash/venv/lib/python3.8/site-packages')
sys.path.insert(0, '/var/www/html/dashboard')
from dashboard import server as application