import os

CHARGEPOINT_USERNAME = os.environ.get('CP_USERNAME')
CHARGEPOINT_PASSWORD = os.environ.get('CP_PASSWORD')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
REDIS_CHANNEL = 'alert'
GOOGLE_ANALYTICS_SITE_ID = os.environ.get('GOOGLE_ANALYTICS_SITE_ID')

SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
SENDGRID_EMAIL_FROM = os.environ.get('SENDGRID_EMAIL_FROM', 'VMware ChargePoint <vmwarechargepoint@gmail.com>')
