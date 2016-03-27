import os

CHARGEPOINT_USERNAME = os.environ.get('CP_USERNAME')
CHARGEPOINT_PASSWORD = os.environ.get('CP_PASSWORD')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')