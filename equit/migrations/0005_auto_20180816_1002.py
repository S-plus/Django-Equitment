# Generated by Django 2.0.3 on 2018-08-16 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equit', '0004_auto_20180816_1000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equitstaff',
            name='equit_permission',
            field=models.PositiveSmallIntegerField(default=1, verbose_name='设备权限等级'),
        ),
        migrations.AlterField(
            model_name='equitstaff',
            name='phone',
            field=models.CharField(max_length=20, unique=True, verbose_name='联系方式'),
        ),
        migrations.AlterField(
            model_name='equitstaff',
            name='staff_name',
            field=models.CharField(max_length=20, unique=True, verbose_name='姓名'),
        ),
    ]