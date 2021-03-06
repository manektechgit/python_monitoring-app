# Generated by Django 3.2.4 on 2021-06-07 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitemonitor', '0002_alter_monitordetails_interval'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitordetails',
            name='isNotification',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='monitordetails',
            name='lastNotificationTime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='monitordetails',
            name='notificationInterval',
            field=models.IntegerField(default=60),
        ),
    ]
