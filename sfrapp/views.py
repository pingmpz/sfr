from django.shortcuts import render, redirect
import pyodbc
from django.http import JsonResponse

################################################################################
##################################### PAGES ####################################
################################################################################

def blank(request):
    context = {
    }
    return render(request, 'blank.html', context)

def index(request):
    context = {
    }
    return render(request, 'index.html', context)

#------------------------------------------------------------------------------- TRANSACTION

def transaction(request, orderoprno):
    orderNo = ""
    operationNo = ""
    order = None
    operation = None
    isFirstPage = False
    hasNoProcess = False # For Testing
    isJoined = False # For Testing
    machineList = []
    operatorList = []
    operationList = []
    lastestOperation = -1 # For Order !Operation
    operationBefore = -1
    operationAfter = -1
    #--
    if orderoprno == "0":
        isFirstPage = True
    else:
        orderNo = orderoprno[0:10]
        operationNo = orderoprno[10:14]
        if isExistOrder(orderNo):
            order = get_order(orderNo)
            operationList = get_operationList(orderNo)
            if isExistOperation(orderNo, operationNo):
                operation = get_operation(orderNo, operationNo)
                for i in range(len(operationList)):
                    if operationNo == operationList[i].OperationNumber:
                        if i != 0:
                            operationBefore = operationList[i-1].OperationNumber
                        if i != len(operationList) - 1:
                            operationAfter = operationList[i+1].OperationNumber
            else:
                if len(operationList) != 0:
                    lastestOperation = operationList[len(operationList) - 1].OperationNumber
    context = {
        'orderNo' : orderNo,
        'operationNo' : operationNo,
        'isFirstPage' : isFirstPage,
        'order' : order,
        'operation' : operation,
        'isJoined' : isJoined,
        'hasNoProcess' : hasNoProcess,
        'machineList' : machineList,
        'operatorList' : operatorList,
        'operationList' : operationList,
        'lastestOperation' : lastestOperation,
        'operationBefore' : operationBefore,
        'operationAfter' : operationAfter,
    }
    return render(request, 'transaction.html', context)

#------------------------------------------------------------------------------- MASTER

def machine_master(request):
    machineList = get_machineList()
    context = {
        'machineList' : machineList,
    }
    return render(request, 'machine_master.html', context)

def user_master(request):
    operatorList = get_operatorList()
    context = {
        'operatorList' : operatorList,
    }
    return render(request, 'user_master.html', context)

################################################################################
#################################### REQUEST ###################################
################################################################################

def get_machine_data(request):
    mc_no = request.GET.get('mc_no')
    isExist = False
    MachineNumber = None
    MachineName = None
    machine = get_machine(mc_no)
    if machine != None:
        isExist = True
        MachineNumber = machine.MachineNumber
        MachineName = machine.MachineName
    data = {
        'isExist': isExist,
        'MachineNumber': MachineNumber,
        'MachineName': MachineName,
    }
    return JsonResponse(data)

def get_operator_data(request):
    opr_id = request.GET.get('opr_id')
    isExist = False
    EmpID = None
    EmpName = None
    Department = None
    operator = get_operator(opr_id)
    if operator != None:
        isExist = True
        EmpID = operator.EmpID
        EmpName = operator.EmpName
        Department = operator.Department
    data = {
        'isExist': isExist,
        'EmpID': EmpID,
        'EmpName': EmpName,
        'Department': Department,
    }
    return JsonResponse(data)

################################################################################
################################### DATABASE ###################################
################################################################################
def get_connection():
    # conn = pyodbc.connect('Driver={SQL Server};''Server=SVSP-SQL;''Database=SFR;''UID=CCSGROUPS\sqladmin;''PWD=$ql@2019;''Trusted_Connection=yes;')
    conn = pyodbc.connect('Driver={SQL Server};''Server=SVCCS-SFR\SQLEXPRESS;''Database=SFR;''UID=sa;''PWD=$fr@2021;''Trusted_Connection=yes;')
    return conn

def get_machineList():
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [MachineList]")
    machineList = cursor.fetchall()
    return machineList

def get_operatorList():
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [User]")
    operatorList = cursor.fetchall()
    return operatorList

def get_operationList(orderNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [SE80_Routing] WHERE ProductionOrderNo = '" + orderNo + "'")
    operationList = cursor.fetchall()
    return operationList

def isExistOrder(orderNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT 1 FROM [SE80_Order] WHERE ProductionOrderNo = '" + orderNo + "'")
    isExist = False
    if len(cursor.fetchall()) > 0:
        isExist = True
    isExistOrder = len(cursor.fetchall())
    return isExist

def isExistOperation(orderNo, operationNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT 1 FROM [SE80_Routing] WHERE ProductionOrderNo = '" + orderNo + "' AND OperationNumber = '" + operationNo + "'")
    isExist = False
    if len(cursor.fetchall()) > 0:
        isExist = True
    isExistOrder = len(cursor.fetchall())
    return isExist

def get_order(orderNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [SE80_Order] WHERE ProductionOrderNo = '" + orderNo + "'")
    order = cursor.fetchall()[0]
    return order

def get_operation(orderNo, operationNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [SE80_Routing] WHERE ProductionOrderNo = '" + orderNo + "' AND OperationNumber = '" + operationNo + "'")
    operation = cursor.fetchall()[0]
    return operation

def get_machine(mc_no):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [MachineList] WHERE MachineNumber = '" + mc_no + "'")
    result = cursor.fetchall()
    if(len(result) == 0):
        machine = None
    else:
        machine = result[0]
    return machine

def get_operator(opr_id):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [User] WHERE EmpID = '" + opr_id + "'")
    result = cursor.fetchall()
    if(len(result) == 0):
        operator = None
    else:
        operator = result[0]
    return operator
########################################################################################
########################################################################################
########################################################################################
