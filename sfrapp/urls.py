from django.urls import path

from . import views

urlpatterns = [
    ### PAGE
    path('index/', views.index, name='index'),
    path('transaction/<str:orderoprno>', views.transaction, name='transaction'),
    #-- MASTER
    path('machine_master/', views.machine_master, name='machine_master'),
    path('user_master/', views.user_master, name='user_master'),
    path('blank/', views.blank, name='blank'),
    ### REQUEST
    path('get_machine_data/', views.get_machine_data, name='get_machine_data'),
    path('get_operator_data/', views.get_operator_data, name='get_operator_data'),
]
