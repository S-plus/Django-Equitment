# Generated by Django 2.0.3 on 2018-08-16 08:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('equit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equitstaff',
            name='equit_permission',
            field=models.IntegerField(default=0, verbose_name='设备权限等级'),
        ),
        migrations.AlterField(
            model_name='equitstaff',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='equitstaff', to=settings.AUTH_USER_MODEL),
        ),
    ]
