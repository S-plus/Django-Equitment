# -*- coding: utf-8 -*-
import datetime

from django.db import models
# from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


# class UserProfile(AbstractUser):
#     department = models.CharField(u'部门', max_length=20, default=u'未填写')
#     equit_permission = models.IntegerField(u'权限等级', max_length=5, default=1)
#     phone = models.CharField('联系方式', max_length=20, default='未填写')

class Equitstaff(models.Model):  # 扩展原有的User，新增几个字段
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='equitstaff')
    # 注意：一定要修改related_name这个值和view中调用时相对应
    staff_name = models.CharField(u'姓名', max_length=20, unique=True)
    equit_permission = models.PositiveSmallIntegerField(u'设备权限等级', default=1)
    phone = models.CharField(u'联系方式', max_length=20, unique=True)

    def __str__(self):
        return self.staff_name

    # def get_absolute_url(self):
    #     return reverse('equit:equitstaff', args=(self.pk, ))


class Info(models.Model):
    ip_addr = models.GenericIPAddressField(u'IP 地址', max_length=16, null=True, blank=True)
    oper_sys = models.CharField(u'操作系统', max_length=80, default=u'未填写')
    sys_prog = models.CharField(u'系统程序', max_length=100, default=u'未填写')
    sw_ip_addr = models.GenericIPAddressField(u'交换机', max_length=16, null=True, blank=True)
    sw_port = models.CharField(u'交换机端口', max_length=3, null=True, blank=True)
    act_date = models.DateField(u'启用时间', default='2001-1-1')
    deact_date = models.DateField(u'停用时间', default='2099-12-31')
    equit_name = models.CharField(u'设备名称', max_length=90)
    cab_id = models.CharField(u'机架号', max_length=16, default=u'未填写')
    staff = models.ForeignKey(Equitstaff, on_delete=models.CASCADE, default=4)
    staff_name = models.CharField(u'维护人员', max_length=20, default=u'未认领')
    staff_phone = models.CharField(u'联系方式', max_length=20, default=u'未填写')
    mod_date = models.DateTimeField(u'修改时间', auto_now=True)
    status = models.BooleanField(u'设备状态', default=True)

    def __str__(self):
        return self.ip_addr

    def get_absolute_url(self):
        return reverse('equit:equitinfo', args=(self.pk, ))

    # 自定义唯一性校验
    # def clean(self):
    #     if self.ip_addr:
    #         if Info.objects.filter(ip_addr__exact=self.ip_addr, status=True):
    #             raise ValidationError(_(u'%s 此IP已被占用' % self.ip_addr))
    #     # else:
    #     if self.equit_name:
    #         if Info.objects.filter(equit_name__exact=self.equit_name, status=True):
    #             raise ValidationError(_(u'%s 此设备已存在' % self.equit_name))
