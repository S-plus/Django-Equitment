# Generated by Django 2.0.3 on 2018-08-16 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equit', '0003_auto_20180816_0906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equitstaff',
            name='phone',
            field=models.CharField(default='未填写', max_length=20, unique=True, verbose_name='联系方式'),
        ),
    ]