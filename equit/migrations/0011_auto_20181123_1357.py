# Generated by Django 2.0.3 on 2018-11-23 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equit', '0010_info_deact_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='info',
            name='ip_addr',
            field=models.GenericIPAddressField(verbose_name='IP 地址'),
        ),
    ]
