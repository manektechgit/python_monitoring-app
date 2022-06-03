from django.db import models


# Create your models here.
class monitorDetails(models.Model):
    domainName = models.CharField(max_length=50)
    email = models.EmailField(max_length=254, blank=False, unique=False)
    interval = models.IntegerField(default=0)
    startDate = models.DateTimeField(blank=True, null=True)
    endDate = models.DateTimeField(blank=True, null=True)
    upTime = models.IntegerField(default=0)
    downTime = models.IntegerField(default=0)
    isNotification = models.BooleanField(default=True)
    notificationInterval = models.IntegerField(default=60)
    lastNotificationTime = models.DateTimeField(blank=True, null=True)
    SSLEnable = models.BooleanField(default=False)
    SSLInterval = models.IntegerField(default=0)


class monitorCountDetails(models.Model):
    TYPES = [("up", "UP"), ("down", "DOWN")]
    monitorDetailsId = models.ForeignKey(monitorDetails, on_delete=models.CASCADE)
    startTime = models.DateTimeField(blank=True, null=True)
    endTime = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPES, blank=False, null=False)


class sslCountDetails(models.Model):
    isSSL = models.BooleanField(default=True)
    monitorDetailsId = models.ForeignKey(monitorDetails, on_delete=models.CASCADE)
    SSLCheckTime = models.DateTimeField(blank=True, null=True)
    SSLDetails = models.TextField()
