from django.urls import path
from django.conf.urls import url
from django.views.static import serve
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    ### PAGE
    path('', views.first_page, name='first_page'),
    path('index/', views.index, name='index'),
    path('transaction/<str:orderoprno>', views.transaction, name='transaction'),
    path('join_activity/<str:orderoprno>', views.join_activity, name='join_activity'),
    path('lot_traveller/<str:orderno>&<str:lotno>', views.lot_traveller, name='lot_traveller'),
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
    path('delay_operation/<str:fwc>', views.delay_operation, name='delay_operation'),
    path('none_working_wc/', views.none_working_wc, name='none_working_wc'),
    path('none_start_order/', views.none_start_order, name='none_start_order'),
    #-- REPORT
    path('ot_table/<str:fmonth>', views.ot_table, name='ot_table'),
    path('mp_ot_auto_machine/<str:fmonth>', views.mp_ot_auto_machine, name='mp_ot_auto_machine'),
    path('oper_no_time/<str:fmonth>', views.oper_no_time, name='oper_no_time'),
    path('completed_order/<str:ftype>&<str:fdate>&<str:fmonth>&<str:fstartdate>&<str:fstopdate>', views.completed_order, name='completed_order'),
    path('rejected_order/<str:ftype>&<str:fdate>&<str:fmonth>&<str:fstartdate>&<str:fstopdate>', views.rejected_order, name='rejected_order'),
    path('canceled_order/<str:ftype>&<str:fdate>&<str:fmonth>&<str:fstartdate>&<str:fstopdate>', views.canceled_order, name='canceled_order'),
    path('work_records/<str:ftype>&<str:fdate>&<str:fmonth>&<str:fstartdate>&<str:fstopdate>', views.work_records, name='work_records'),
    path('ab_graph_wcg/<str:fwcg>&<str:ftype>&<str:fmonth>&<str:fyear>', views.ab_graph_wcg, name='ab_graph_wcg'),
    path('ab_graph_rt/<str:frt>&<str:ftype>&<str:fmonth>&<str:fyear>', views.ab_graph_rt, name='ab_graph_rt'),
    path('con_operation/<str:fwc>&<str:fmonth>', views.con_operation, name='con_operation'),
    path('zpp02/', views.zpp02, name='zpp02'),
    path('zpp04/', views.zpp04, name='zpp04'),
    #-- SAP
    path('sap_order/<str:fdate>&<str:fhour>', views.sap_order, name='sap_order'),
    path('sap_routing/<str:fdate>&<str:fhour>', views.sap_routing, name='sap_routing'),
    path('sap_component/<str:fdate>&<str:fhour>', views.sap_component, name='sap_component'),
    path('sap_report/<str:fdate>&<str:fhour>', views.sap_report, name='sap_report'),
    path('sap_mod/<str:fdate>&<str:fhour>', views.sap_mod, name='sap_mod'),
    path('blank/', views.blank, name='blank'),
    #-- ADMIN PANEL
    path('admin_controller/', views.admin_controller, name='admin_controller'),
    path('error_data/', views.error_data, name='error_data'),
    ### REQUEST
    path('fp_emp_search/', views.fp_emp_search, name='fp_emp_search'),
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
    #-- CONFIRM & MANUAL REPORT & FIX OVERTIME
    path('get_data_for_confirm/', views.get_data_for_confirm, name='get_data_for_confirm'),
    path('confirm/', views.confirm, name='confirm'),
    path('manual_report/', views.manual_report, name='manual_report'),
    path('fix_overtime/', views.fix_overtime, name='fix_overtime'),
    #-- JOIN
    path('join/', views.join, name='join'),
    path('break_join/', views.break_join, name='break_join'),
    #-- MODIFIER
    path('inc_qty/', views.inc_qty, name='inc_qty'),
    path('dec_qty/', views.dec_qty, name='dec_qty'),
    path('delete_operation/', views.delete_operation, name='delete_operation'),
    path('add_operation/', views.add_operation, name='add_operation'),
    path('change_operation/', views.change_operation, name='change_operation'),
    #-- JOIN
    path('save_note/', views.save_note, name='save_note'),
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
    path('fix_rm_mat_code/', views.fix_rm_mat_code, name='fix_rm_mat_code'),
    path('set_wc_target/', views.set_wc_target, name='set_wc_target'),
    path('set_wc_cap/', views.set_wc_cap, name='set_wc_cap'),
    ## ADMIN PANEL
    path('add_new_user/', views.add_new_user, name='add_new_user'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('change_user_password/', views.change_user_password, name='change_user_password'),
    path('mpa/', views.mpa, name='mpa'),
    # path('reset_all/', views.reset_all, name='reset_all'),
    path('reset_order/', views.reset_order, name='reset_order'),
    path('cancel_order/', views.cancel_order, name='cancel_order'),
    path('sqty_operation/', views.sqty_operation, name='sqty_operation'),
    path('drawing/<str:dir>&<str:fg_code>', views.drawing, name='drawing'),
    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT, }),
]+ static(settings.MEDIA_URL, serve, document_root=settings.MEDIA_ROOT)
