from django.shortcuts import render, redirect
import urllib
from apscheduler.schedulers.background import BackgroundScheduler
from .models import monitorDetails, monitorCountDetails, sslCountDetails
from datetime import datetime
from django.core.mail import send_mail
from .utils import timeCalculation, getMinutesBySeconds
from urllib.request import Request, ssl, socket
from urllib.parse import urlparse
import json


# Create your views here.

def monitor(request):
    url = request.POST.get('selected_domain')
    email = request.POST.get('selected_email')

    if url and not email:
        monitorData = monitorDetails.objects.filter(domainName=url)
    elif email and not url:
        monitorData = monitorDetails.objects.filter(email=email)
    elif email and url:
        monitorData = monitorDetails.objects.filter(email=email, domainName=url)
    else:
        monitorData = monitorDetails.objects.all()

    domain_list = monitorDetails.objects.order_by().values('domainName').distinct()
    email_list = monitorDetails.objects.order_by().values('email').distinct()
    context = {
        'monitorData': monitorData,
        'domain_list': domain_list,
        'email_list': email_list,
        'selected_url': url,
        'selected_email': email,
    }
    return render(request, "sitemonitor/monitor.html", context)


def addmonitor(request):
    return render(request, "sitemonitor/index.html", {})


def removemonitor(request, pk):
    monitorRecord = monitorDetails.objects.get(pk=pk)
    monitorRecord.delete()
    return redirect('/monitor')


def editmonitor(request, pk):
    monitorRecord = monitorDetails.objects.get(pk=pk)
    context = {
        'monitorData': monitorRecord,
    }
    return render(request, "sitemonitor/index.html", context)


def startmonitor(request):
    url = request.POST.get('domainName')
    interval = int(request.POST.get('interval'))
    email = request.POST.get('email')
    notificationInterval = int(request.POST.get('notificationInterval'))
    SSLEnable = request.POST.get('SSLEnable')
    if SSLEnable == 'on':
        SSLEnable = True
    else:
        SSLEnable = False

    if SSLEnable:
        SSLInterval = int(request.POST.get('SSLInterval'))

    monitorData = monitorDetails.objects.get_or_create(domainName=url)[0]

    if monitorData:
        monitorCount_Details = monitorCountDetails()
        monitorCount_Details.monitorDetailsId = monitorData
        monitorCount_Details.startTime = monitorData.startDate
        monitorCount_Details.endTime = monitorData.endDate
        if monitorData.upTime != 0:
            monitorCount_Details.type = 'up'
        else:
            monitorCount_Details.type = 'down'
        monitorCount_Details.save()

    if not monitorData.startDate:
        monitorData.startDate = datetime.now()
    monitorData.email = email
    monitorData.interval = interval
    monitorData.notificationInterval = notificationInterval
    monitorData.upTime = 0
    monitorData.downTime = 0
    monitorData.SSLEnable = SSLEnable
    if SSLEnable:
        monitorData.SSLInterval = SSLInterval
    monitorData.save()

    scheduler = BackgroundScheduler()
    scheduler.add_job(monitoring, 'interval', seconds=interval, args=[url, interval, email])
    scheduler.start()

    if SSLEnable:
        scheduler = BackgroundScheduler()
        scheduler.add_job(SSLMonitoring, 'interval', hours=SSLInterval, args=[url, email])
        scheduler.start()

    return redirect('/monitor')


def monitoring(url, interval, email):
    monitorData = monitorDetails.objects.get_or_create(domainName=url)[0]
    try:
        status_code = urllib.request.urlopen(url).getcode()
        website_is_up = status_code == 200
        monitorData.domainName = url
        if not monitorData.startDate:
            monitorData.startDate = datetime.now()
        monitorData.endDate = datetime.now()
        if website_is_up:
            monitorData.upTime += interval
        monitorData.save()
    except Exception as e:
        if monitorData:
            monitorData.downTime += interval
            monitorData.domainName = url
            monitorData.interval = interval
            if not monitorData.startDate:
                monitorData.startDate = datetime.now()
            monitorData.endDate = datetime.now()
        lastNotificationTime = monitorData.lastNotificationTime
        notificationInterval = monitorData.notificationInterval

        if lastNotificationTime and monitorData.downTime != interval:
            date_time_obj = datetime.strptime(str(lastNotificationTime), '%Y-%m-%d %H:%M:%S.%f')
        else:
            monitorData.lastNotificationTime = datetime.now()
            date_time_obj = datetime.now()

        if monitorData.isNotification and (
                getMinutesBySeconds(datetime.now().timestamp() - date_time_obj.timestamp()) > notificationInterval):
            days, hours, minutes, seconds = timeCalculation(monitorData.downTime)
            Subject = 'Error found for {}'.format(url)
            message = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/></head><body ' \
                      'class="bg-white"><div class="d-flex flex-column flex-root"><div ' \
                      'style="font-family:Arial,Helvetica,sans-serif; line-height: 1.5; font-weight: normal; ' \
                      'font-size: 15px; color: #2F3044; ' \
                      '"><table align="left" border="0" ' \
                      'style="border-collapse:collapse;margin:0 auto; padding:0; ' \
                      '"><tbody><tr><td' \
                      '"><tr><td align="left" valign="left"><div style="text-align:left; margin: 0 ' \
                      '0; padding: 40px; background-color:#ffffff; border-radius: 6px"><div style="padding-bottom: ' \
                      '30px; font-size: 17px;"><strong>Error found for: {}</strong></div><div style="padding-bottom: ' \
                      '30px">We found {} to be down since last <strong>{} days {} hour {} minutes {} ' \
                      'seconds.</strong><br><br><br> ' \
                      '<div ' \
                      'style="padding-bottom: 10px">Kind regards,<br>Site Monitoring ' \
                      'Team.</br></div></div></td></tr></img></a></td></tr></tbody></table></div></div></body></html' \
                      '>'.format(
                url, url, days, hours, minutes, seconds)
            send_mail(
                Subject,
                message,
                'testineed@gmail.com',
                [email],
                fail_silently=False,
                html_message=message,
            )
            monitorData.lastNotificationTime = datetime.now()
        monitorData.save()


def SSLMonitoring(url, email):
    monitorData = monitorDetails.objects.get_or_create(domainName=url)[0]
    sslDetails = sslCountDetails()
    sslDetails.monitorDetailsId = monitorData
    sslDetails.SSLCheckTime = datetime.now()

    # get only host name
    parsed_uri = urlparse(url)
    host = '{uri.netloc}'.format(uri=parsed_uri)
    try:

        context = ssl.create_default_context()
        with socket.create_connection((host, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                data = json.dumps(ssock.getpeercert())

        sslDetails.isSSL = True
        sslDetails.SSLDetails = data
        sslDetails.save()

        data = json.loads(data)
        expiryDate = data.get('notAfter')
        expiryDate = datetime.strptime(expiryDate, '%b %d %H:%M:%S %Y %Z')
        currentDateTime = datetime.now()

        if expiryDate < currentDateTime:
            Subject = 'SSL Error found for {}'.format(url)
            message = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/></head><body ' \
                      'class="bg-white"><div class="d-flex flex-column flex-root"><div ' \
                      'style="font-family:Arial,Helvetica,sans-serif; line-height: 1.5; font-weight: normal; ' \
                      'font-size: 15px; color: #2F3044; ' \
                      '"><table align="left" border="0" ' \
                      'style="border-collapse:collapse;margin:0 auto; padding:0; ' \
                      '"><tbody><tr><td' \
                      '"><tr><td align="left" valign="left"><div style="text-align:left; margin: 0 ' \
                      '0; padding: 40px; background-color:#ffffff; border-radius: 6px"><div style="padding-bottom: ' \
                      '30px; font-size: 17px;"><strong>SSL Error found for: {}</strong></div><div ' \
                      'style="padding-bottom: ' \
                      '30px">We found {} not to be secure, SSL certificate is expired. ' \
                      '<div ' \
                      'style="padding-bottom: 10px">Kind regards,<br>Site Monitoring ' \
                      'Team.</br></div></div></td></tr></img></a></td></tr></tbody></table></div></div></body></html' \
                      '>'.format(url, url, url)
            send_mail(
                Subject,
                message,
                'testineed@gmail.com',
                [email],
                fail_silently=False,
                html_message=message,
            )

    except Exception as e:
        sslDetails.isSSL = False
        print(e)
        sslDetails.save()

        Subject = 'SSL Error found for {}'.format(url)
        message = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/></head><body ' \
                  'class="bg-white"><div class="d-flex flex-column flex-root"><div ' \
                  'style="font-family:Arial,Helvetica,sans-serif; line-height: 1.5; font-weight: normal; ' \
                  'font-size: 15px; color: #2F3044; ' \
                  '"><table align="left" border="0" ' \
                  'style="border-collapse:collapse;margin:0 auto; padding:0; ' \
                  '"><tbody><tr><td' \
                  '"><tr><td align="left" valign="left"><div style="text-align:left; margin: 0 ' \
                  '0; padding: 40px; background-color:#ffffff; border-radius: 6px"><div style="padding-bottom: ' \
                  '30px; font-size: 17px;"><strong>SSL Error found for: {}</strong></div><div style="padding-bottom: ' \
                  '30px">We found {} not to be secure, SSL certificate verification is failed. ' \
                  '<div ' \
                  'style="padding-bottom: 10px">Kind regards,<br>Site Monitoring ' \
                  'Team.</br></div></div></td></tr></img></a></td></tr></tbody></table></div></div></body></html' \
                  '>'.format(url, url, url)
        send_mail(
            Subject,
            message,
            'testineed@gmail.com',
            [email],
            fail_silently=False,
            html_message=message,
        )
