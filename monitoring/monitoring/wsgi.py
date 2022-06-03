"""
WSGI config for monitoring project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.wsgi import get_wsgi_application
from sitemonitor.models import monitorDetails, monitorCountDetails
from sitemonitor.views import monitoring, SSLMonitoring
from datetime import datetime
import sentry_sdk

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitoring.settings')

# When application starts need to auto start the existing monitoring domain.

sentry_sdk.init(
    "https://6900ff8afc294beaa7fd840397356dd1@o848569.ingest.sentry.io/5815686",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

monitorData = monitorDetails.objects.all()

for data in monitorData:

    monitorCount_Details = monitorCountDetails()
    monitorCount_Details.monitorDetailsId = data
    monitorCount_Details.startTime = data.startDate
    monitorCount_Details.endTime = data.endDate
    if data.upTime != 0:
        monitorCount_Details.type = 'up'
    else:
        monitorCount_Details.type = 'down'
    monitorCount_Details.save()

    # Reset te monitor details for next monitoring.
    data.startDate = datetime.now()
    data.endDate = None
    data.upTime = 0
    data.downTime = 0
    data.save()

    scheduler = BackgroundScheduler()
    scheduler.add_job(monitoring, 'interval', seconds=data.interval, args=[data.domainName, data.interval, data.email])
    scheduler.start()

    if data.SSLEnable:
        scheduler = BackgroundScheduler()
        scheduler.add_job(SSLMonitoring, 'interval', hours=data.SSLInterval, args=[data.domainName, data.email])
        scheduler.start()

application = get_wsgi_application()
