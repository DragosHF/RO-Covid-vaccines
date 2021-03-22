python_home = '/home/ubuntu/RO-Covid-vaccines/CovidDash/venv'

activate_this = python_home + '/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys
sys.path.insert(0, '/var/www/html/dashboard')
from dashboard import app as application