# -*- coding: utf-8 -*-
# @Time     : 2018-07-28 16:41
# @Author   : liujiuhao
# @Site     : 
# @File     : urls.py
# @Software : PyCharm


# app_name = 'equitinfo'
# urlpatterns = [
#     # path('', views.index, name='index'),
#     # path('<int:question_id>/', views.detail, name='detail'),
#     # path('<int:question_id>/results/', views.results, name='results'),
#
#     # 代码重构
#     path('', views.IndexView.as_view(), name='index'),
#     path('<int:pk>/', views.DetailView.as_view(), name='detail'),
#     path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
#     path('<int:question_id>/vote/', views.vote, name='vote'),
# ]

from django.urls import path, include

from . import views


app_name = 'equit'
urlpatterns = [
    path('', views.loginView, name='login'),
    path('logout_view/', views.logout_view, name='logout'),
    path('index/', views.index_view, name='index'),  # 首页v0.1
    # path('<int:pk>/', views.IndexView.as_view(), name='index'),  # 首页v0.2
    path('<int:pk>/equitstaff/', views.EquitstaffUpdate.as_view(), name='equitstaff'),
    # path('<int:pk>/equitinfo/', views.Equitinfo.as_view(), name='equitinfo'),
    path('<int:equit_info_id>/equitinfo/', views.equitinfo_view, name='equitinfo'),
    # path('<int:pk>/equitinfoupdate/', views.Equitinfoupdate.as_view(), name='equitinfoupdate'),
    # path('<int:equit_staff_id>/equitinfocreate/', views.equitinfo_create_view, name='equitinfocreate'),
    # path('<int:pk>/equitinfodelete/', views.Equitinfodelete.as_view(), name='equitinfodelete'),
    # path('excelupload/', views.excel_upload, name='excelupload'),
    path('excelexport/', views.excel_export, name='excelexport'),
    path('ajax_captcha/', views.ajax_captcha, name='ajax_captcha'),
]
