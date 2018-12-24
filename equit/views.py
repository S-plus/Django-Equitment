# -*- coding: utf-8 -*-

import xlrd
import IPy
import time
import json
from datetime import datetime
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin import widgets
from django.urls import reverse, reverse_lazy
from django.views.generic.base import View
from django.views.generic.edit import UpdateView, DeleteView
from django.forms import ModelForm, inlineformset_factory
from django import forms
from django.utils import timezone
from django.db.models import F, Q
from django.db import transaction
from django.utils.encoding import escape_uri_path
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


from captcha.models import CaptchaStore

from .models import Info, Equitstaff
from .form import LoginForm, InfoForm


# ajax验证码校验
def ajax_captcha(request):
    print(request.is_ajax())
    if request.is_ajax():
        print(request.GET['response'])
        print(request.GET['hashkey'])
        if CaptchaStore.objects.filter(response=request.GET['response'], hashkey=request.GET['hashkey']).exists():
            json_data = {'status': 1}
        else:
            json_data = {'status': 0}
        return JsonResponse(json_data)
    else:
        json_data = {'status': 0}
        return JsonResponse(json_data)


# 登录 v0.2
def login_view(request):
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            user = authenticate(request, username=username, password=password)  # 验证用户是否存在
            if user and user.is_active:
                try:
                    equit_staff_id = user.equitstaff.id  # 验证用户是否有设备管理系统权限
                except (KeyError, Equitstaff.DoesNotExist):
                    return HttpResponse('无设备管理系统权限')
                else:
                    login(request, user)
                    print(request.user.id)
                    request.session.set_expiry(0)  # 浏览器关闭后session立即失效
                    # return HttpResponseRedirect('/equit/index/')  # 登录v0.1
                    return HttpResponseRedirect('/equit/index/')
                    # return HttpResponseRedirect(reverse('equit:index', args=(equit_staff_id, )))  # 登录v0.2
            else:
                login_form = LoginForm()
                return render(request, 'equit/login.html', {'login_form': login_form, 'loginError': json.dumps(u'用户名或密码错误')})
        else:
            login_form = LoginForm()
            return render(request, 'equit/login.html', {'login_form': login_form, 'loginError': json.dumps(u'验证码错误')})
    elif request.method == 'GET':
        login_form = LoginForm()
        return render(request, 'equit/login.html', {'login_form': login_form})


# 登录 v0.3
class LoginView(View):
    def get(self, request):
        login_form = LoginForm()
        return render(request, 'equit/login.html', {'login_form': login_form})


# 登出
def logout_view(request):
    logout(request)
    return redirect(reverse('equit:login'))


# 首页 v3
@login_required(login_url='equit:login')
def index_view(request):
    if request.method == 'GET':
        form = InfoForm()
        keywords = request.GET.get('keywords', '')
        # error_msg = ''
        # 模糊查询
        if keywords:
            equitinfo_list = Info.objects.filter(
                Q(ip_addr__icontains=keywords) |
                Q(sw_ip_addr__icontains=keywords) |
                Q(oper_sys__icontains=keywords) |
                Q(sys_prog__icontains=keywords) |
                Q(cab_id__icontains=keywords) |
                Q(staff_name__icontains=keywords) |
                Q(equit_name__icontains=keywords)
            )
            paginator = Paginator(equitinfo_list, 13)
            page = request.GET.get('page')
            equitinfo = paginator.get_page(page)
            return render(request, 'equit/index.html', {'form': form, 'equitinfo': equitinfo, 'keywords': keywords})
        else:
            equitinfo_list = Info.objects.all()
            # 分页
            paginator = Paginator(equitinfo_list, 13)
            page = request.GET.get('page')
            equitinfo = paginator.get_page(page)
            return render(request, 'equit/index.html', {'form': form, 'equitinfo': equitinfo})
    elif request.method == 'POST':
        equitinfo_list = Info.objects.all()
        if 'upload' in request.POST:
            form = InfoForm()
            # print(request.user.equitstaff.id)
            # form = UploadFileForm(request.POST, request.FILES)
            # print(form)
            # print(forms.is_valid())
            # if form.is_valid():
            equitstaff = get_object_or_404(Equitstaff, pk=request.user.equitstaff.id)
            if request.FILES.get('excel_file', ''):
                f = request.FILES.get('excel_file', '')
                type_excel = f.name.split('.')[-1]  # 只判断最后一个.即文件后缀
                if type_excel == 'xlsx':
                    # 解析excel
                    wb = xlrd.open_workbook(filename=None, file_contents=f.read())
                    table = wb.sheets()[0]

                    nrows = table.nrows  # 行数
                    # ncole = table.ncols  #
                    if nrows > 1:
                        try:
                            with transaction.atomic():
                                excelError = ""
                                for i in range(1, nrows):
                                    row_values = table.row_values(i)
                                    # print(rowvalues)
                                    # 校验IP地址及唯一ip地址在用状态校验
                                    print(row_values)
                                    if IPy.IP(row_values[0]) and Info.objects.filter(ip_addr__exact=row_values[0], status=True).exists():
                                        raise ValidationError(_(u'第 %(value)d 行IP地址已存在'), params={'value': i})
                                    if Info.objects.filter(equit_name__exact=row_values[5], status=True).exists():
                                        raise ValidationError(_(u'第 %(value)d 行该设备名已存在'), params={'value': i})
                                    else:
                                        if row_values[1]:
                                            oper_sys = row_values[1]
                                        else:
                                            oper_sys = u'未填写'
                                        if row_values[2]:
                                            sys_prog = row_values[2]
                                        else:
                                            sys_prog = u'未填写'
                                        if row_values[4]:
                                            act_date = row_values[4]
                                        else:
                                            act_date = datetime.strptime('2000-1-1', '%Y-%m-%d')
                                        equitinfo = Info(
                                            ip_addr=row_values[0],
                                            oper_sys=oper_sys,
                                            sys_prog=sys_prog,
                                            sw_ip_addr=row_values[3],
                                            act_date=act_date,
                                            equit_name=row_values[5],
                                            cab_id=row_values[6],
                                            staff=equitstaff,
                                            staff_name=equitstaff.staff_name,
                                            staff_phone=equitstaff.phone,
                                            status=True
                                        )
                                        equitinfo.full_clean()
                                        equitinfo.save()

                        except ValidationError as e:
                            print(json.dumps(e.message_dict))
                            # if not isinstance(e, dict):
                            #     e = json.dumps(e)
                            equitinfo_list = Info.objects.all()
                            paginator = Paginator(equitinfo_list, 13)
                            page = request.GET.get('page')
                            equitinfo = paginator.get_page(page)
                            return render(request, 'equit/index.html', {
                                 'equitinfo': equitinfo, 'form': form, 'excelError': json.dumps(u'数据错误，请调整后重试')
                            })
                        else:
                            return HttpResponseRedirect(reverse('equit:index', args=()))

                    else:
                        excelError = u"excel文件不能为空"
                        paginator = Paginator(equitinfo_list, 13)
                        page = request.GET.get('page')
                        equitinfo = paginator.get_page(page)
                        return render(request, 'equit/index.html', {
                            'equitinfo': equitinfo, 'form': form, 'excelError': json.dumps(excelError)
                        })
                else:
                    excelError = u"上传文件格式不是xlsx"
                    paginator = Paginator(equitinfo_list, 13)
                    page = request.GET.get('page')
                    equitinfo = paginator.get_page(page)
                    return render(request, 'equit/index.html', {
                        'equitinfo': equitinfo, 'form': form, 'excelError': json.dumps(excelError)
                    })
            else:
                excelError = u"文件不能为空."
                paginator = Paginator(equitinfo_list, 13)
                page = request.GET.get('page')
                equitinfo = paginator.get_page(page)
                return render(request, 'equit/index.html', {
                    'equitinfo': equitinfo, 'form': form, 'excelError': json.dumps(excelError)
                })
        elif 'create' in request.POST:
            # equitstaff = get_object_or_404(Equitstaff, pk=request.user.equitstaff.id)
            form = InfoForm(request.POST)
            print(form)
            print(request)
            createError = ''
            if form.is_valid():
                if request.POST.get('ip_addr', ''):
                    if Info.objects.filter(ip_addr__exact=request.POST.get('ip_addr', ''), status=True).exists():
                        createError = u'IP地址已存在'
                if Info.objects.filter(equit_name__exact=request.POST.get('equit_name', ''), status=True).exists():
                    createError = u'该设备名已存在'
                # 判断端口是否占用
                if request.POST.get('sw_port', '') and Info.objects.filter(
                        sw_ip_addr__exact=request.POST.get('sw_ip_addr', ''),
                        sw_port__exact=request.POST.get('sw_port', ''),
                        status=True).exists():
                    createError = u'该端口已被占用'
                if createError:
                    paginator = Paginator(equitinfo_list, 13)
                    page = request.GET.get('page')
                    equitinfo = paginator.get_page(page)
                    return render(request, 'equit/index.html',
                                  {'form': form, 'equitinfo': equitinfo, 'createError': json.dumps(createError)})
                else:
                    info = form.save(commit=False)
                    equitstaff = get_object_or_404(Equitstaff, pk=request.POST.get('staff', ''))
                    # info.staff = equitstaff
                    info.staff_phone = equitstaff.phone
                    info.staff_name = equitstaff.staff_name
                    info.save()
                    form = InfoForm()
                    paginator = Paginator(equitinfo_list, 13)
                    page = request.GET.get('page')
                    equitinfo = paginator.get_page(page)
                    return render(request, 'equit/index.html', {'form': form, 'equitinfo': equitinfo})
            else:
                createError = u"设备信息不正确或输入的信息不规范"
                paginator = Paginator(equitinfo_list, 13)
                page = request.GET.get('page')
                equitinfo = paginator.get_page(page)
                return render(request, 'equit/index.html', {
                    'form': form,
                    'equitinfo': equitinfo,
                    'createError': json.dumps(createError)})


# 查询
# @login_required(login_url='equit:login')
# def search_view(request):
#     equitstaff = get_object_or_404(Equitstaff, pk=request.user.equitstaff.id)
#     if request.method == 'GET':
#         keywords = request.GET.get('keywords', '')
#         # error_msg = ''
#         if keywords:
#             equitinfo = Info.objects.get(Q(ip_addr__exact=keywords) | Q(sw_ip_addr__exact=keywords))
#             return render(request, 'equit/index.html', {'equitinfo': equitinfo})


# def equitinfo_create_view(request, equit_staff_id):
#     equit_staff = get_object_or_404(Equitstaff, pk=equit_staff_id)
#     if request.method == 'POST':
#         form = InfoForm(request.POST)
#         if form.is_valid():
#             info = form.save(commit=False)
#             info.staff = equit_staff
#             info.staff_phone = equit_staff.phone
#             info.staff_name = equit_staff.staff_name
#             info.save()
#             return HttpResponseRedirect(reverse('equit:index', args=(equit_staff_id,)))
#
#     else:
#         form = InfoForm()
#     return render(request, 'equit/equitinfocreate.html', {'form': form, 'equit_staff_id': equit_staff_id})


# 首页 V0.2
# class IndexView(LoginRequiredMixin, generic.DetailView):
#     model = Equitstaff
#     template_name = 'equit/index.html'


# @login_required(login_url='equit:login')
# def index_view(request, equitstaff_id):
#     equitStaff = get_object_or_404(Equitstaff, pk=equitstaff_id)

# 用户页
class EquitstaffUpdate(LoginRequiredMixin, UpdateView):
    model = Equitstaff
    fields = ['phone']
    template_name = 'equit/equitstaff.html'

    def get_success_url(self):
        # print(self.object.id)
        # print(self.object.phone)

        # 维护人员联系方式修改成功后修改对应的设备维护人员联系方式
        Info.objects.filter(staff__exact=self.object.id).update(staff_phone=self.object.phone)
        return reverse('equit:index', args=())
        # return reverse('equit:index', args=(self.object.id, ))


# 设备详情
# class Equitinfo(LoginRequiredMixin, generic.DetailView):
#     model = Info
#     template_name = 'equit/equitinfo.html'


@login_required(login_url='equit:login')
def equitinfo_view(request, equit_info_id):
    if request.method == 'GET':
        equitinfo = get_object_or_404(Info, pk=equit_info_id)
        form = InfoForm(instance=equitinfo)
        return render(request, 'equit/equitinfo.html', {'info': equitinfo, 'form': form})
    elif request.method == 'POST':
        equitinfo = get_object_or_404(Info, pk=equit_info_id)
        equitstaff = get_object_or_404(Equitstaff, pk=request.user.equitstaff.id)
        if (equitinfo.staff_id == request.user.equitstaff.id) or (equitstaff.equit_permission == 9):
            if 'update' in request.POST:
                updateError = ''
                form = InfoForm(request.POST)
                if form.is_valid():
                    if equitinfo.ip_addr != request.POST.get('ip_addr', ''):
                        if request.POST.get('ip_addr', ''):
                            if Info.objects.filter(
                                    ip_addr__exact=request.POST.get('ip_addr', ''),
                                    status=True
                            ) and equitinfo.status:
                                updateError = u'IP地址已存在'
                    if equitinfo.equit_name != request.POST.get('equit_name', ''):
                        if Info.objects.filter(
                                equit_name__exact=request.POST.get('equit_name', ''),
                                status=True
                        ) and equitinfo.status:
                            updateError = u'该设备名已存在'

                    print(request.POST.get('sw_port', ''))
                    print(Info.objects.filter(
                        sw_ip_addr__exact=request.POST.get('sw_ip_addr', ''),
                        sw_port__exact=request.POST.get('sw_port', ''),
                        status=True
                    ))
                    print(request.POST.get('status', ''))
                    if request.POST.get('sw_port', '') and Info.objects.filter(
                            sw_ip_addr__exact=request.POST.get('sw_ip_addr', ''),
                            sw_port__exact=request.POST.get('sw_port', ''),
                            status=True
                    ) and equitinfo.status:
                        updateError = u'该端口已占用'
                    if updateError:
                        return render(request, 'equit/equitinfo.html', {
                            'info': equitinfo, 'form': form, 'updateError': json.dumps(updateError)
                        })
                    else:
                        data = form.cleaned_data
                        equitinfo.ip_addr = data['ip_addr']
                        equitinfo.oper_sys = data['oper_sys']
                        equitinfo.sys_prog = data['sys_prog']
                        equitinfo.sw_ip_addr = data['sw_ip_addr']
                        equitinfo.act_date = data['act_date']
                        equitinfo.equit_name = data['equit_name']
                        equitinfo.cab_id = data['cab_id']
                        equitinfo.sw_port = data['sw_port']
                        equitinfo.staff_id = data['staff']
                        equitstaff = get_object_or_404(Equitstaff, pk=request.POST.get('staff', ''))
                        # info.staff = equitstaff
                        equitinfo.staff_phone = equitstaff.phone
                        equitinfo.staff_name = equitstaff.staff_name
                        equitinfo.save()
                        equitinfo = get_object_or_404(Info, pk=equit_info_id)
                        form = InfoForm(instance=equitinfo)
                        return render(request, 'equit/equitinfo.html', {
                            'info': equitinfo, 'form': form
                        })
                else:
                    updateError = u"设备信息不正确或输入的信息不规范"
                    return render(request, 'equit/equitinfo.html', {
                        'info': equitinfo, 'form': form, 'updateError': json.dumps(updateError)
                    })

            elif 'disable' in request.POST:  # 停用
                if equitinfo.status is True:
                    equitinfo.status = False
                    equitinfo.deact_date = datetime.now().strftime('%Y-%m-%d')
                    equitinfo.save()
                equitinfo = get_object_or_404(Info, pk=equit_info_id)
                form = InfoForm(instance=equitinfo)
                return render(request, 'equit/equitinfo.html', {
                    'info': equitinfo, 'form': form
                })
            elif 'delete' in request.POST:  # 删除
                if equitstaff.equit_permission == 9:
                    equitinfo.delete()
                    return HttpResponseRedirect(reverse('equit:index', args=()))
                else:
                    deleteError = u'无删除设备权限'
                    form = InfoForm(instance=equitinfo)
                    return render(request, 'equit/equitinfo.html', {
                        'info': equitinfo, 'form': form, 'permissionError': json.dumps(deleteError)
                    })
        else:
            permissionError = u"无修改此设备权限"
            form = InfoForm(instance=equitinfo)
            return render(request, 'equit/equitinfo.html', {
                'info': equitinfo, 'form': form, 'permissionError': json.dumps(permissionError)
            })


    # elif request.method == 'POST':
    #     equitInfo = get_object_or_404(Info, pk=equitInfoId)
    #     if 'delete' in request.POST:
    #         try:
    #             equitStaff = get_object_or_404(Equitstaff, pk=request.equitstaff.id)
    #             if equitStaff.equit_permission == 9:
    #
    #                 with transaction.atomic():
    #                     equitInfo.delete()
    #                     return reverse('equit:index', args=())
    #         except Exception as e:
    #             print(e)
    #             deleteError = u"删除失败"
    #             return render(request, 'equit/equitinfo.html', {
    #                 'equitinfo': equitInfo, 'deleteError': json.dumps(deleteError)
    #             })


# 修改
# class Equitinfoupdate(LoginRequiredMixin, UpdateView):
#     model = Info
#     fields = [
#         'ip_addr',
#         'oper_sys',
#         'sys_prog',
#         'sw_ip_addr',
#         'act_date',
#         'equit_name',
#         'cab_id'
#     ]
#     template_name = 'equit/equitinfoupdate.html'


# @login_required(login_url='equit:login')
# def equitinfo_update_view(request, equitInfoId):
#     if request.method == 'POST':
#         try:
#             equitStaff = get_object_or_404(Equitstaff, pk=request.user.equitstaff)
#             equitInfo = get_object_or_404(Info, pk=equitInfoId)
#         except Exception as e:


# 新增视图
# @login_required(login_url='equit:login')
# def equitinfo_create_view(request, equit_staff_id):
#     equit_staff = get_object_or_404(Equitstaff, pk=equit_staff_id)
#     if request.method == 'POST':
#         form = InfoForm(request.POST)
#         if form.is_valid():
#             info = form.save(commit=False)
#             info.staff = equit_staff
#             info.staff_phone = equit_staff.phone
#             info.staff_name = equit_staff.staff_name
#             info.save()
#             return HttpResponseRedirect(reverse('equit:index', args=(equit_staff_id,)))
#     else:
#         form = InfoForm()
#     return render(request, 'equit/equitinfocreate.html', {'form': form, 'equit_staff_id': equit_staff_id})
#
#
# # 删除
# class Equitinfodelete(LoginRequiredMixin, DeleteView):
#     model = Info
#     template_name = 'equit/equitinfodelete.html'
#
#     def get_success_url(self):
#         # print(self.object.id)
#         # print(self.object.staff_id)
#
#         return reverse('equit:index', args=(self.object.staff_id, ))


# 批量导入
# @login_required(login_url='equit:login')
# def excel_upload(request):
#     equitinfo = Info.objects.all()
#     form = InfoForm()
#     # print(request.user.equitstaff.id)
#     # form = UploadFileForm(request.POST, request.FILES)
#     # print(form)
#     # print(forms.is_valid())
#     # if form.is_valid():
#     equit_staff = get_object_or_404(Equitstaff, pk=request.user.equitstaff.id)
#     if request.FILES.get('excel_file', ''):
#         f = request.FILES.get('excel_file', '')
#         type_excel = f.name.split('.')[-1]  # 只判断最后一个.即文件后缀
#         if type_excel == 'xlsx':
#             # 解析excel
#             wb = xlrd.open_workbook(filename=None, file_contents=f.read())
#             table = wb.sheets()[0]
#
#             nrows = table.nrows  # 行数
#             # ncole = table.ncols  #
#             if nrows > 1:
#                 try:
#                     with transaction.atomic():
#                         for i in range(1, nrows):
#                             row_values = table.row_values(i)
#                             # print(rowvalues)
#                             # 校验IP地址及唯一ip地址在用状态校验
#                             if IPy.IP(row_values[0]) and not (
#                             Info.objects.filter(ip_addr__exact=row_values[0], status=True)):
#                                 equitinfo = Info.objects.create(
#                                     ip_addr=row_values[0],
#                                     oper_sys=row_values[1],
#                                     sys_prog=row_values[2],
#                                     sw_ip_addr=row_values[3],
#                                     act_date=row_values[4],
#                                     equit_name=row_values[5],
#                                     cab_id=row_values[6],
#                                     staff=equit_staff,
#                                     staff_name=equit_staff.staff_name,
#                                     staff_phone=equit_staff.phone,
#                                     status=True
#                                 )
#                                 # equitinfo.clean_fields(exclude=None) 官方文档上有提到在save前要进行数据校验，如果没有成功应该是提交到数据库时数据库报错后返回
#                                 equitinfo.save()
#                         return HttpResponseRedirect(reverse('equit:index', args=()))
#                 except Exception as e:
#                     print(e)
#                     excelError = u"导入失败，请检查导入的数据是否正确"
#                     return render(request, 'equit/index.html', {
#                         'equitinfo': equitinfo, 'form': form, 'excelError': json.dumps(excelError)
#                     })
#             else:
#                 excelError = u"excel文件不能为空"
#                 return render(request, 'equit/index.html', {
#                     'equitinfo': equitinfo, 'form': form, 'excelError': json.dumps(excelError)
#                 })
#         else:
#             excelError = u"上传文件格式不是xlsx"
#             return render(request, 'equit/index.html', {
#                 'equitinfo': equitinfo, 'form': form, 'excelError': json.dumps(excelError)
#             })
#     else:
#         excelError = u"文件不能为空."
#         return render(request, 'equit/index.html', {
#             'equitinfo': equitinfo, 'form': form, 'excelError': json.dumps(excelError)
#         })
#

@login_required(login_url='equit:login')
def excel_export(request):
    print(request.META.get('HTTP_USER_AGENT', ''))
    header = request.META.get('HTTP_USER_AGENT', '')
    # equit_staff = get_object_or_404(Equitstaff, pk=equit_staff_id)
    equit_info_list = Info.objects.all()
    # if request.method == "GET":
    wb = Workbook()
    sheet = wb.worksheets[0]
    row0 = [u'IP地址', u'操作系统', u'系统程序', u'上级IP地址', u'上级IP端口', u'启用时间', u'设备名称', u'机架号', u'维护人员', u'联系方式']
    sheet.append(row0)
    for equit_info in equit_info_list:
        row = [
            equit_info.ip_addr,
            equit_info.oper_sys,
            equit_info.sys_prog,
            equit_info.sw_ip_addr,
            equit_info.sw_port,
            equit_info.act_date,
            equit_info.equit_name,
            equit_info.cab_id,
            equit_info.staff_name,
            equit_info.staff_phone
        ]
        sheet.append(row)
        print(sheet)
    # response = HttpResponse(content_type='application/vnd.ms-excel')
    dest_filename = '设备信息_' + time.strftime('%Y-%m-%d', time.localtime()) + '.xlsx'
    print(dest_filename)
    response = HttpResponse(content=save_virtual_workbook(wb), content_type='application/vnd.ms-excel')

    if (header.find('Chrome') != -1) or (header.find('Firefox') != -1):  # 浏览器适配
        response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(dest_filename))
    else:
        response['Content-Disposition'] = 'attachment; filename=' + escape_uri_path(dest_filename)
    # wb.save(response)
    return response
