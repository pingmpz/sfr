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
    path('curr_master/', views.curr_master, name='curr_master'),
    #-- DATA PAGE
    path('wc/<str:wcno>&<str:fmonth>', views.wc, name='wc'),
    path('emp/<str:empid>&<str:fmonth>', views.emp, name='emp'),
    #-- MONITORING
    path('working_order/', views.working_order, name='working_order'),
    path('working_wc/', views.working_wc, name='working_wc'),
    path('working_emp/', views.working_emp, name='working_emp'),
    #-- REPORT
    path('lot_traveller/<str:orderno>&<str:lotno>', views.lot_traveller, name='lot_traveller'),
    #-- SAP
    path('sap_order/<str:fdate>&<str:fhour>', views.sap_order, name='sap_order'),
    path('sap_routing/<str:fdate>&<str:fhour>', views.sap_routing, name='sap_routing'),
    path('sap_report/<str:fdate>&<str:fhour>', views.sap_report, name='sap_report'),
    path('sap_mod/<str:fdate>&<str:fhour>', views.sap_mod, name='sap_mod'),
    path('blank/', views.blank, name='blank'),
    #-- ADMIN PANEL
    path('user_control/', views.user_control, name='user_control'),
    ### REQUEST
    #-- MAIN TABLE
    path('get_workcenter_data/', views.get_workcenter_data, name='get_workcenter_data'),
    path('get_operator_data/', views.get_operator_data, name='get_operator_data'),
    #-- INNER MAIN TABLE
    path('get_operating_workcenter_list/', views.get_operating_workcenter_list, name='get_operating_workcenter_list'),
    path('get_operating_operator_list/', views.get_operating_operator_list, name='get_operating_operator_list'),
    path('add_operating_workcenter/', views.add_operating_workcenter, name='add_operating_workcenter'),
    path('delete_operating_workcenter/', views.delete_operating_workcenter, name='delete_operating_workcenter'),
    path('stop_operating_workcenter/', views.stop_operating_workcenter, name='stop_operating_workcenter'),
    path('add_operating_operator/', views.add_operating_operator, name='add_operating_operator'),
    path('start_work_operating_operator/', views.start_work_operating_operator, name='start_work_operating_operator'),
    path('stop_setup_operating_operator/', views.stop_setup_operating_operator, name='stop_setup_operating_operator'),
    path('stop_work_operating_operator/', views.stop_work_operating_operator, name='stop_work_operating_operator'),
    #-- CONFIRMATION
    path('get_data_for_confirm/', views.get_data_for_confirm, name='get_data_for_confirm'),
    path('confirm/', views.confirm, name='confirm'),
    path('manual_report/', views.manual_report, name='manual_report'),
    #-- JOIN
    path('join/', views.join, name='join'),
    path('break_join/', views.break_join, name='break_join'),
    #-- MODIFIER
    path('delete_operation/', views.delete_operation, name='delete_operation'),
    path('add_operation/', views.add_operation, name='add_operation'),
    path('change_operation/', views.change_operation, name='change_operation'),
    #-- VALIDATION
    path('validate_new_operation/', views.validate_new_operation, name='validate_new_operation'),
    path('validate_routing/', views.validate_routing, name='validate_routing'),
    path('validate_work_center/', views.validate_work_center, name='validate_work_center'),
    path('validate_operator/', views.validate_operator, name='validate_operator'),
    path('validate_password/', views.validate_password, name='validate_password'),
    path('validate_section_chief_password/', views.validate_section_chief_password, name='validate_section_chief_password'),
    path('validate_admin_password/', views.validate_admin_password, name='validate_admin_password'),
    path('validate_super_admin_password/', views.validate_super_admin_password, name='validate_super_admin_password'),
    path('validate_new_user_id/', views.validate_new_user_id, name='validate_new_user_id'),
    path('validate_new_password/', views.validate_new_password, name='validate_new_password'),
    #-- ETC
    path('increase_lot_no/', views.increase_lot_no, name='increase_lot_no'),
    ## ADMIN PANEL
    path('add_new_user/', views.add_new_user, name='add_new_user'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('change_user_password/', views.change_user_password, name='change_user_password'),
    path('reset_all/', views.reset_all, name='reset_all'),
]
