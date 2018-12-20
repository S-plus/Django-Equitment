from datetime import datetime

from django import forms

from captcha.fields import CaptchaField

from .models import Info


MONTH = {i: i for i in range(1, 13)}

YEAR = {i: i for i in range(datetime.now().year-19, datetime.now().year+1)}


class LoginForm(forms.Form):
    username = forms.CharField(label=u'用户名', required=True, error_messages={'required': u'用户名不能为空'})
    password = forms.CharField(label=u'密码', widget=forms.PasswordInput, required=True, error_messages={'required': u'密码不能为空'})
    captcha = CaptchaField(label=u'验证码', error_messages={'invalid': u'验证码错误'})


class InfoForm(forms.ModelForm):
    class Meta:
        model = Info
        exclude = ['staff_name', 'staff_phone', 'mod_date', 'deact_date', 'status']
        labels = {
            'staff': u'维护人员',
        }
        widgets = {
            # 默认启用时间为2001-1-1
            'act_date': forms.SelectDateWidget(years=YEAR, months=MONTH, empty_label=(2001, 1, 1))
        }