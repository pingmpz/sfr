from django.urls import path

from . import views

urlpatterns = [
    ### PAGE
    path('index/', views.index, name='index'),
    path('transaction/<str:orderoprno>', views.transaction, name='transaction'),
    path('join_activity/<str:orderoprno>', views.join_activity, name='join_activity'),
    #-- MASTER
    path('wc_master/', views.wc_master, name='wc_master'),
    path('emp_master/', views.emp_master, name='emp_master'),
    path('rej_master/', views.rej_master, name='rej_master'),
    path('matg_master/', views.matg_master, name='matg_master'),
    path('purg_master/', views.purg_master, name='purg_master'),
    path('blank/', views.blank, name='blank'),
    ### REQUEST
    path('validate_operator/', views.validate_operator, name='validate_operator'),
    path('validate_new_operation/', views.validate_new_operation, name='validate_new_operation'),
    path('get_workcenter_data/', views.get_workcenter_data, name='get_workcenter_data'),
    path('get_operator_data/', views.get_operator_data, name='get_operator_data'),
    path('get_operating_workcenter_list/', views.get_operating_workcenter_list, name='get_operating_workcenter_list'),
    path('get_operating_operator_list/', views.get_operating_operator_list, name='get_operating_operator_list'),
    path('add_operating_workcenter/', views.add_operating_workcenter, name='add_operating_workcenter'),
    path('delete_operating_workcenter/', views.delete_operating_workcenter, name='delete_operating_workcenter'),
    path('stop_operating_workcenter/', views.stop_operating_workcenter, name='stop_operating_workcenter'),
    path('add_operating_operator/', views.add_operating_operator, name='add_operating_operator'),
    path('start_work_operating_operator/', views.start_work_operating_operator, name='start_work_operating_operator'),
    path('stop_setup_operating_operator/', views.stop_setup_operating_operator, name='stop_setup_operating_operator'),
    path('stop_work_operating_operator/', views.stop_work_operating_operator, name='stop_work_operating_operator'),
    path('get_data_for_confirm/', views.get_data_for_confirm, name='get_data_for_confirm'),
    path('confirm/', views.confirm, name='confirm'),
    ## ADMIN
    path('reset_all/', views.reset_all, name='reset_all'),
]
