from django.urls import path

from . import views

urlpatterns = [
    ### PAGE
    path('index/', views.index, name='index'),
    path('transaction/<str:orderoprno>', views.transaction, name='transaction'),
    #-- MASTER
    path('wcg_master/', views.wcg_master, name='wcg_master'),
    path('wc_master/', views.wc_master, name='wc_master'),
    path('mc_master/', views.mc_master, name='mc_master'),
    path('user_master/', views.user_master, name='user_master'),
    path('rej_master/', views.rej_master, name='rej_master'),
    path('blank/', views.blank, name='blank'),
    ### REQUEST
    path('validate_operator/', views.validate_operator, name='validate_operator'),
    path('validate_new_operation/', views.validate_new_operation, name='validate_new_operation'),
    path('get_machine_data/', views.get_machine_data, name='get_machine_data'),
    path('get_operator_data/', views.get_operator_data, name='get_operator_data'),
    path('get_all_tmc/', views.get_all_tmc, name='get_all_tmc'),
    path('get_all_topr/', views.get_all_topr, name='get_all_topr'),
    path('add_tmc/', views.add_tmc, name='add_tmc'),
    path('delete_tmc/', views.delete_tmc, name='delete_tmc'),
    path('add_topr/', views.add_topr, name='add_topr'),
    path('start_work_topr/', views.start_work_topr, name='start_work_topr'),
    path('stop_setup_topr/', views.stop_setup_topr, name='stop_setup_topr'),
]
