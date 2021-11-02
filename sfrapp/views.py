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
    operationList = []
    rejectReasonList = []
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
                #-- GET PREV & NEXT OPERATION
                for i in range(len(operationList)):
                    if operationNo.strip() == operationList[i].OperationNumber.strip():
                        if i != 0:
                            operationBefore = operationList[i-1].OperationNumber
                        if i != len(operationList) - 1:
                            operationAfter = operationList[i+1].OperationNumber
                #-- GET REJECT REASON LIST
                rejectReasonList = get_rejectReasonList()
            #-- GET LAST OPERATION
            else:
                if len(operationList) != 0:
                    lastestOperation = operationList[len(operationList) - 1].OperationNumber
            #--
    context = {
        'orderNo' : orderNo,
        'operationNo' : operationNo,
        'isFirstPage' : isFirstPage,
        'order' : order,
        'operation' : operation,
        'isJoined' : isJoined,
        'hasNoProcess' : hasNoProcess,
        'operationList' : operationList,
        'rejectReasonList' : rejectReasonList,
        'lastestOperation' : lastestOperation,
        'operationBefore' : operationBefore,
        'operationAfter' : operationAfter,
    }
    return render(request, 'transaction.html', context)

#------------------------------------------------------------------------------- MASTER

def wcg_master(request):
    workCenterGroupList = get_workCenterGroupList()
    context = {
        'workCenterGroupList' : workCenterGroupList,
    }
    return render(request, 'wcg_master.html', context)

def wc_master(request):
    workCenterList = get_workCenterList()
    context = {
        'workCenterList' : workCenterList,
    }
    return render(request, 'wc_master.html', context)

def mc_master(request):
    machineList = get_machineList()
    context = {
        'machineList' : machineList,
    }
    return render(request, 'mc_master.html', context)

def user_master(request):
    operatorList = get_operatorList()
    context = {
        'operatorList' : operatorList,
    }
    return render(request, 'user_master.html', context)

def rej_master(request):
    rejectReasonList = get_rejectReasonList()
    context = {
        'rejectReasonList' : rejectReasonList,
    }
    return render(request, 'rej_master.html', context)

################################################################################
#################################### REQUEST ###################################
################################################################################

def validate_operator(request):
    emp_id = request.GET.get('emp_id')
    isExist = isExistOperator(emp_id)
    data = {
        'isExist': isExist,
    }
    return JsonResponse(data)

def validate_new_operation(request):
    order_no = request.GET.get('order_no')
    current_operation_no = request.GET.get('current_operation_no')
    new_operation_no = request.GET.get('new_operation_no')
    canAdd = False
    isExist = isExistOperation(order_no, new_operation_no)
    if isExist == False:
        canAdd = True
    data = {
        'canAdd': canAdd,
    }
    return JsonResponse(data)

def get_machine_data(request):
    machine_no = request.GET.get('machine_no')
    canAdd = False
    invalid_text = ''
    MachineNumber = None
    MachineName = None
    machine = get_machine(machine_no)
    if machine != None:
        MachineNumber = machine.MachineNumber
        MachineName = machine.MachineName
        if isMachineWorking(machine_no):
            tmc = getTMCbyMachineNo(machine_no)
            invalid_text = MachineNumber + ' is working at ' + tmc.ProductionOrderNo + "-" + tmc.OperationNo
        else:
            canAdd = True
    else:
        canAdd = False
        invalid_text = 'Machine Not Found'
    data = {
        'canAdd': canAdd,
        'invalid_text' : invalid_text,
        'MachineNumber': MachineNumber,
        'MachineName': MachineName,
    }
    return JsonResponse(data)

def get_operator_data(request):
    operator_id = request.GET.get('operator_id')
    canAdd = False
    invalid_text = ''
    EmpID = None
    EmpName = None
    Department = None
    operator = get_operator(operator_id)
    if operator != None:
        EmpID = (operator.EmpID).strip()
        EmpName = operator.EmpName
        Department = operator.Remarks
        if isOperatorWorking(operator_id):
            topr = getTOPRbyEmpId(operator_id)
            invalid_text = operator_id + ' is working at ' + topr.ProductionOrderNo + "-" + topr.OperationNo
        else:
            canAdd = True
    else:
        canAdd = False
        invalid_text = 'Operator Not Found'
    data = {
        'canAdd': canAdd,
        'invalid_text' : invalid_text,
        'EmpID': EmpID,
        'EmpName': EmpName,
        'Department': Department,
    }
    return JsonResponse(data)

def get_all_tmc(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    tmcList = [list(i) for i in getTMCList(order_no, operation_no)]
    hasOperatorWorkingList = []
    for tmc in tmcList:
        hasOperatorWorkingList.append(hasOperatorWorking(tmc[0]))
    data = {
        'tmcList': tmcList,
        'hasOperatorWorkingList': hasOperatorWorkingList,
    }
    return JsonResponse(data)

def get_all_topr(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    toprList = [list(i) for i in getTOPRList(order_no, operation_no)]
    data = {
        'toprList': toprList,
    }
    return JsonResponse(data)

def add_tmc(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    machine_no = request.GET.get('machine_no')
    insertTMC(order_no, operation_no, machine_no)
    data = {
    }
    return JsonResponse(data)

def delete_tmc(request):
    id = request.GET.get('id')
    deleteTMC(id)
    data = {
    }
    return JsonResponse(data)

def add_topr(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    operator_id = request.GET.get('operator_id')
    tmc_id = request.GET.get('tmc_id')
    status = request.GET.get('status')
    insertTOPR(order_no, operation_no, operator_id, tmc_id, status)
    data = {
    }
    return JsonResponse(data)

def start_work_topr(request):
    id = request.GET.get('id')
    startWorkTOPR(id)
    data = {
    }
    return JsonResponse(data)

def stop_setup_topr(request):
    id = request.GET.get('id')
    stopSetupTOPR(id)
    data = {
    }
    return JsonResponse(data)

def stop_work_topr(request):
    id = request.GET.get('id')
    stopWorkTOPR(id)
    data = {
    }
    return JsonResponse(data)

def stop_mc_tmc(request):
    id = request.GET.get('id')
    stopMachineTMC(id)
    data = {
    }
    return JsonResponse(data)

################################################################################
################################### DATABASE ###################################
################################################################################
def get_connection():
    # conn = pyodbc.connect('Driver={SQL Server};''Server=SVSP-SQL;''Database=SFR;''UID=CCSGROUPS\sqladmin;''PWD=$ql@2019;''Trusted_Connection=yes;')
    conn = pyodbc.connect('Driver={SQL Server};''Server=SVCCS-SFR\SQLEXPRESS;''Database=SFR;''UID=sa;''PWD=$fr@2021;''Trusted_Connection=yes;')
    return conn

def get_workCenterGroupList():
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [WorkCenterGroup]")
    workCenterGroupList = cursor.fetchall()
    return workCenterGroupList

def get_workCenterList():
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [WorkCenter] INNER JOIN [WorkCenterGroup] ON [WorkCenter].WorkCenterGroupID = [WorkCenterGroup].WorkCenterGroupID")
    workCenterList = cursor.fetchall()
    return workCenterList

def get_machineList():
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [Machine] as MC INNER JOIN [WorkCenter] as WC ON MC.WorkCenterID = WC.WorkCenterID INNER JOIN [WorkCenterGroup] as WCG ON WC.WorkCenterGroupID = WCG.WorkCenterGroupID")
    machineList = cursor.fetchall()
    return machineList

def get_operatorList():
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [User]")
    operatorList = cursor.fetchall()
    return operatorList

def get_rejectReasonList():
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [RejectReason]")
    rejectReasonList = cursor.fetchall()
    return rejectReasonList

def get_operationList(orderNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [SAP_Routing] WHERE ProductionOrderNo = '" + orderNo + "'")
    operationList = cursor.fetchall()
    return operationList

def getTMCList(orderNo, operationNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [T_MC] as TMC INNER JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber WHERE ProductionOrderNo = '" + orderNo + "' AND OperationNo = '" + operationNo + "' ORDER BY TMC.ID ASC")
    tmcList = cursor.fetchall()
    return tmcList

def getTOPRList(orderNo, operationNo):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_OPR] as TOPR INNER JOIN [User] as U ON TOPR.EmpID = U.EmpID LEFT JOIN [T_MC] as TMC ON TOPR.T_MC_ID = TMC.ID LEFT JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber WHERE TOPR.ProductionOrderNo = '" + orderNo + "' AND TOPR.OperationNo = '" + operationNo + "' ORDER BY TOPR.ID ASC"
    cursor.execute(sql)
    toprList = cursor.fetchall()
    return toprList

def isExistOrder(orderNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [SAP_Order] WHERE ProductionOrderNo = '" + orderNo + "'")
    isExist = False
    if len(cursor.fetchall()) > 0:
        isExist = True
    return isExist

def isExistOperation(orderNo, operationNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [SAP_Routing] WHERE ProductionOrderNo = '" + orderNo + "' AND OperationNumber = '" + operationNo + "'")
    isExist = False
    if len(cursor.fetchall()) > 0:
        isExist = True
    return isExist

def isExistOperator(EmpID):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [User] WHERE EmpID = '" + EmpID + "'")
    isExist = False
    if len(cursor.fetchall()) > 0:
        isExist = True
    return isExist

def get_order(orderNo):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [SAP_Order] WHERE ProductionOrderNo = '" + orderNo + "'")
    order = cursor.fetchall()[0]
    return order

def get_operation(orderNo, operationNo):
    cursor = get_connection().cursor()
    sql = "SELECT *"
    sql += " FROM [SAP_Routing] as RT INNER JOIN [WorkCenter] as WC ON RT.WorkCenter = WC.WorkCenterName"
    sql += " WHERE ProductionOrderNo = '" + orderNo + "' AND OperationNumber = '" + operationNo + "'"
    cursor.execute(sql)
    operation = cursor.fetchall()[0]
    return operation

def get_machine(machine_no):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [Machine] WHERE MachineNumber = '" + machine_no + "'")
    result = cursor.fetchall()
    if(len(result) == 0):
        machine = None
    else:
        machine = result[0]
    return machine

def get_operator(operator_id):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [User] WHERE EmpID = '" + operator_id + "'")
    result = cursor.fetchall()
    if(len(result) == 0):
        operator = None
    else:
        operator = result[0]
    return operator

def isMachineWorking(machine_no):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [T_MC] WHERE MachineNumber = '" + machine_no + "' AND Status <> 'COMPLETED'")
    isWorking = False
    if len(cursor.fetchall()) > 0:
        isWorking = True
    return isWorking

def isOperatorWorking(operator_id):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [T_OPR] WHERE EmpID = '" + operator_id + "' AND Status <> 'COMPLETED'")
    isWorking = False
    if len(cursor.fetchall()) > 0:
        isWorking = True
    return isWorking

def hasOperatorWorking(tmc_id):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [T_OPR] WHERE T_MC_ID = " + str(tmc_id) + " AND Status <> 'COMPLETED'")
    isWorking = False
    if len(cursor.fetchall()) > 0:
        isWorking = True
    return isWorking

def getTMCbyID(id):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [T_MC] as TMC INNER JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber WHERE TMC.ID = " + str(id))
    result = cursor.fetchall()
    if(len(result) == 0):
        tmc = None
    else:
        tmc = result[0]
    return tmc

def getTOPRbyID(id):
    cursor = get_connection().cursor()
    cursor.execute("SELECT TMC.Status as TMCStatus,* FROM [T_OPR] as TOPR INNER JOIN [SAP_Routing] as RT ON TOPR.OperationNo = RT.OperationNumber LEFT JOIN [T_MC] as TMC ON TOPR.T_MC_ID = TMC.ID LEFT JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber WHERE TOPR.ID = " + str(id))
    result = cursor.fetchall()
    if(len(result) == 0):
        tmc = None
    else:
        tmc = result[0]
    return tmc

def getTMCbyMachineNo(machine_no):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [T_MC] as TMC INNER JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber WHERE TMC.MachineNumber = '" + machine_no + "'")
    result = cursor.fetchall()
    if(len(result) == 0):
        tmc = None
    else:
        tmc = result[0]
    return tmc

def getTOPRbyEmpId(operator_id):
    cursor = get_connection().cursor()
    cursor.execute("SELECT * FROM [T_OPR] WHERE EmpID = '" + operator_id + "'")
    result = cursor.fetchall()
    if(len(result) == 0):
        topr = None
    else:
        topr = result[0]
    return topr

def insertTMC(order_no, operation_no, machine_no):
    conn = get_connection()
    cursor = conn.cursor()
    #-- MACHINE : ADD
    sql = "INSERT INTO [T_MC] ([ProductionOrderNo],[OperationNo],[MachineNumber],[Status]) VALUES ('" + order_no + "','" + operation_no + "','" + machine_no + "','WAITING');"
    cursor.execute(sql)
    conn.commit()
    return

def insertTOPR(order_no, operation_no, operator_id, tmc_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    #-- OPERATOR : WORKING/SETUP
    sql = "INSERT INTO [T_OPR] ([ProductionOrderNo],[OperationNo],[EmpID],[T_MC_ID],[StartDateTime],[Status]) VALUES ('" + order_no + "','" + operation_no + "','" + str(operator_id) + "'," + str(tmc_id) + ",CURRENT_TIMESTAMP,'" + status + "');"
    cursor.execute(sql)
    conn.commit()
    #-- IF OPERATION IS NOT LABOR TYPE
    if tmc_id != "NULL":
        #-- MACHINE : WORKING/SETUP
        sql = "UPDATE [T_MC] SET [StartDateTime] = CURRENT_TIMESTAMP, [Status] = '" + status + "' WHERE ID = " + tmc_id
        cursor.execute(sql)
        conn.commit()
    return

def deleteTMC(id):
    conn = get_connection()
    cursor = conn.cursor()
    #-- MACHINE : DELETE
    cursor.execute("DELETE FROM [T_MC] WHERE ID = " + str(id))
    conn.commit()
    return

def stopMachineTMC(id):
    conn = get_connection()
    cursor = conn.cursor()
    #-- MACHINE : STOP WORKING
    sql = "UPDATE [T_MC] SET [StopDateTime]  = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    return

#-- NEED FIX !!
def startWorkTOPR(id):
    conn = get_connection()
    cursor = conn.cursor()
    topr = getTOPRbyID(id)
    if topr.TMCStatus.strip() == "SETUP":
        #-- OPERATOR : SAVE SETUP TIME
        sql = "UPDATE [T_OPR] SET [StopDateTime] = CURRENT_TIMESTAMP WHERE ID = " + str(id)
        cursor.execute(sql)
        conn.commit()
        #-- MACHINE : SAVE SETUP TIME
        sql = "UPDATE [T_MC] SET [StopDateTime] = CURRENT_TIMESTAMP WHERE ID = " + str(topr.T_MC_ID)
        cursor.execute(sql)
        conn.commit()
        #-- POST SETUP DATA OF OPERATOR #-- NEED FIX !!!
        sql = """INSERT INTO [dbo].[SFR2SAP]
           ([DateTimeStamp],[WorkCenter],[ProductionOrderNo],[OperationNumber],[Yiled],[Scrap],[SetupTime],[OperTime],[LaborTime],[StartDate],[StartTime],[FinishDate],[FinishTime],[EmployeeID],[MachineNo])
           VALUES """
        sql += "(CURRENT_TIMESTAMP,'"+topr.WorkCenter+"','"+topr.ProductionOrderNo+"','"+topr.OperationNumber+"',0,0,0,0,0,NULL,NULL,NULL,NULL,"+topr.EmpID+",'"+topr.MachineNumber+"')"
        print(sql)
        cursor.execute(sql)
        conn.commit()
        #-- POST SETUP DATA OF MACHINE #-- NEED FIX !!!

        #-- MACHINE : WORKING
        sql = "UPDATE [T_MC] SET [StartDateTime] = CURRENT_TIMESTAMP, [StopDateTime] = NULL, [Status] = 'WORKING' WHERE ID = " + str(topr.T_MC_ID)
        cursor.execute(sql)
        conn.commit()
    #-- OPERATOR : WORKING
    sql = "UPDATE [T_OPR] SET [StartDateTime] = CURRENT_TIMESTAMP, [StopDateTime] = NULL, [Status] = 'WORKING' WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    return

#-- NEED FIX !!
def stopSetupTOPR(id):
    conn = get_connection()
    cursor = conn.cursor()
    topr = getTOPRbyID(id)
    #-- OPERATOR : SAVE SETUP TIME
    sql = "UPDATE [T_OPR] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    #-- MACHINE : SAVE SETUP TIME
    sql = "UPDATE [T_MC] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(topr.T_MC_ID)
    cursor.execute(sql)
    conn.commit()
    #-- POST SETUP DATA OF OPERATOR #-- NEED FIX !!!

    #-- POST SETUP DATA OF MACHINE #-- NEED FIX !!!

    #-- MACHINE : GO BACK TO WAITING
    sql = "UPDATE [T_MC] SET [StartDateTime] = NULL, [StopDateTime] = NULL, [Status] = 'WAITING' WHERE ID = " + str(topr.T_MC_ID)
    cursor.execute(sql)
    conn.commit()
    #-- OPERATOR : EXIT
    sql = "DELETE FROM [T_OPR] WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    return

#-- NEED FIX !!
def stopWorkTOPR(id):
    conn = get_connection()
    cursor = conn.cursor()
    topr = getTOPRbyID(id)
    #-- OPERATOR : SAVE WORKING TIME
    sql = "UPDATE [T_OPR] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    #-- POST WORKING DATA OF OPERATOR #-- NEED FIX !!!

    #-- IF OPERATION IS NOT LABOR TYPE & NO OPERATOR WORKING & MACHINE IS MANUAL
    if(topr.T_MC_ID != None and hasOperatorWorking(topr.T_MC_ID) == False and topr.Auto_Manual.strip() == 'Manual'):
        #-- MACHINE : STOP WORKING
        sql = "UPDATE [T_MC] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(topr.T_MC_ID)
        cursor.execute(sql)
        conn.commit()
    return

########################################################################################
########################################################################################
########################################################################################
def FourDigitOperationNo(operationNo):
    result = str(operationNo)
    while len(result) < 4:
        result = "0" + result
    return result
