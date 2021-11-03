from django.shortcuts import render, redirect
import pyodbc
from django.http import JsonResponse
from datetime import datetime

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
    remainQty = -1
    isFirstPage = False
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
                remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
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
        'remainQty' : remainQty,
        'isJoined' : isJoined,
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

def get_topr_for_confirm(request):
    id = request.GET.get('id')
    topr = getTOPRbyID(id)
    operator = get_operator(topr.EmpID)
    operator_text = operator.EmpID.strip() + " | " + operator.EmpName
    machine_text = ""
    if topr.MachineNumber != None:
        machine = get_machine(topr.MachineNumber)
        machine_text = machine.MachineNumber + " | " + machine.MachineName
    start_time = topr.TOPRStartDateTime.strftime("%d-%m-%Y, %H:%M:%S")
    stop_time = topr.TOPRStopDateTime.strftime("%d-%m-%Y, %H:%M:%S")
    print(start_time, stop_time)
    data = {
        'operator_text': operator_text,
        'machine_text': machine_text,
        'start_time': start_time,
        'stop_time': stop_time,
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
    sql = "SELECT * FROM [WorkCenterGroup]"
    cursor.execute(sql)
    workCenterGroupList = cursor.fetchall()
    return workCenterGroupList

def get_workCenterList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [WorkCenter] INNER JOIN [WorkCenterGroup] ON [WorkCenter].WorkCenterGroupID = [WorkCenterGroup].WorkCenterGroupID"
    cursor.execute(sql)
    workCenterList = cursor.fetchall()
    return workCenterList

def get_machineList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [Machine] as MC INNER JOIN [WorkCenter] as WC ON MC.WorkCenterID = WC.WorkCenterID"
    sql += " INNER JOIN [WorkCenterGroup] as WCG ON WC.WorkCenterGroupID = WCG.WorkCenterGroupID"
    cursor.execute(sql)
    machineList = cursor.fetchall()
    return machineList

def get_operatorList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [User]"
    cursor.execute(sql)
    operatorList = cursor.fetchall()
    return operatorList

def get_rejectReasonList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [RejectReason]"
    cursor.execute(sql)
    rejectReasonList = cursor.fetchall()
    return rejectReasonList

def get_operationList(orderNo):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_CON] WHERE ProductionOrderNo = '" + orderNo + "'"
    cursor.execute(sql)
    operationList = cursor.fetchall()
    return operationList

def getTMCList(orderNo, operationNo):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_MC] as TMC INNER JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber"
    sql += "WHERE ProductionOrderNo = '" + orderNo + "' AND OperationNo = '" + operationNo + "' ORDER BY TMC.ID ASC"
    cursor.execute(sql)
    tmcList = cursor.fetchall()
    return tmcList

def getTOPRList(orderNo, operationNo):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_OPR] as TOPR INNER JOIN [User] as U ON TOPR.EmpID = U.EmpID"
    sql += " LEFT JOIN [T_MC] as TMC ON TOPR.T_MC_ID = TMC.ID"
    sql += " LEFT JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber"
    sql += " WHERE TOPR.ProductionOrderNo = '" + orderNo + "' AND TOPR.OperationNo = '" + operationNo + "' ORDER BY TOPR.ID ASC"
    cursor.execute(sql)
    toprList = cursor.fetchall()
    return toprList

def isExistOrder(orderNo):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [SAP_Order] WHERE ProductionOrderNo = '" + orderNo + "'"
    cursor.execute(sql)
    isExist = False
    if len(cursor.fetchall()) > 0:
        isExist = True
    return isExist

def isExistOperation(orderNo, operationNo):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_CON] WHERE ProductionOrderNo = '" + orderNo + "' AND OperationNumber = '" + operationNo + "'"
    cursor.execute(sql)
    isExist = False
    if len(cursor.fetchall()) > 0:
        isExist = True
    return isExist

def isExistOperator(EmpID):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [User] WHERE EmpID = '" + EmpID + "'"
    cursor.execute(sql)
    isExist = False
    if len(cursor.fetchall()) > 0:
        isExist = True
    return isExist

def get_order(orderNo):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [SAP_Order] WHERE ProductionOrderNo = '" + orderNo + "'"
    cursor.execute(sql)
    order = cursor.fetchall()[0]
    return order

def get_operation(orderNo, operationNo):
    cursor = get_connection().cursor()
    sql = "SELECT *"
    sql += " FROM [T_CON] as RT INNER JOIN [WorkCenter] as WC ON RT.WorkCenter = WC.WorkCenterName"
    sql += " WHERE ProductionOrderNo = '" + orderNo + "' AND OperationNumber = '" + operationNo + "'"
    cursor.execute(sql)
    operation = cursor.fetchall()[0]
    return operation

def get_machine(machine_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [Machine] WHERE MachineNumber = '" + machine_no + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        machine = None
    else:
        machine = result[0]
    return machine

def get_operator(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [User] WHERE EmpID = '" + operator_id + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        operator = None
    else:
        operator = result[0]
    return operator

def isMachineWorking(machine_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_MC] WHERE MachineNumber = '" + machine_no + "' AND Status <> 'COMPLETED'"
    cursor.execute(sql)
    isWorking = False
    if len(cursor.fetchall()) > 0:
        isWorking = True
    return isWorking

def isOperatorWorking(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_OPR] WHERE EmpID = '" + operator_id + "' AND Status <> 'COMPLETED'"
    cursor.execute(sql)
    isWorking = False
    if len(cursor.fetchall()) > 0:
        isWorking = True
    return isWorking

def hasOperatorWorking(tmc_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_OPR] WHERE T_MC_ID = " + str(tmc_id) + " AND Status <> 'COMPLETED'"
    cursor.execute(sql)
    isWorking = False
    if len(cursor.fetchall()) > 0:
        isWorking = True
    return isWorking

def getTMCbyID(id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_MC] as TMC INNER JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber WHERE TMC.ID = " + str(id)
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        tmc = None
    else:
        tmc = result[0]
    return tmc

def getTOPRbyID(id):
    cursor = get_connection().cursor()
    sql = "SELECT TOPR.ProductionOrderNo as OrderNo, TOPR.StartDateTime as TOPRStartDateTime, TOPR.StopDateTime as TOPRStopDateTime, TMC.Status as TMCStatus,*"
    sql += " FROM [T_OPR] as TOPR INNER JOIN [T_CON] as RT ON TOPR.OperationNo = RT.OperationNumber"
    sql += " LEFT JOIN [T_MC] as TMC ON TOPR.T_MC_ID = TMC.ID"
    sql += " LEFT JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber"
    sql += " WHERE TOPR.ID = " + str(id)
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        tmc = None
    else:
        tmc = result[0]
    return tmc

def getTMCbyMachineNo(machine_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_MC] as TMC INNER JOIN [Machine] as MC ON TMC.MachineNumber = MC.MachineNumber WHERE TMC.MachineNumber = '" + machine_no + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        tmc = None
    else:
        tmc = result[0]
    return tmc

def getTOPRbyEmpId(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [T_OPR] WHERE EmpID = '" + operator_id + "'"
    cursor.execute(sql)
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
    sql = "INSERT INTO [T_MC] ([ProductionOrderNo],[OperationNo],[MachineNumber],[Status])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "','" + machine_no + "','WAITING')"
    cursor.execute(sql)
    conn.commit()
    return

def insertTOPR(order_no, operation_no, operator_id, tmc_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    #-- OPERATOR : WORKING/SETUP
    sql = "INSERT INTO [T_OPR] ([ProductionOrderNo],[OperationNo],[EmpID],[T_MC_ID],[StartDateTime],[Status])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "','" + str(operator_id) + "'," + str(tmc_id) + ",CURRENT_TIMESTAMP,'" + status + "')"
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
    sql = "DELETE FROM [T_MC] WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    return

def stopMachineTMC(id):
    conn = get_connection()
    cursor = conn.cursor()
    #-- MACHINE : STOP WORKING
    sql = "UPDATE [T_MC] SET [StopDateTime]  = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    #-- LOG : MACHINE WORK TIME ???
    return

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
        #-- LOG : MACHINE SETUP TIME ???
        #-- LOG : OPERATOR SETUP TIME ???
        #-- POST SETUP DATA OF OPERATOR
        topr = getTOPRbyID(id)
        startdate = topr.TOPRStartDateTime.strftime("%Y%m%d");
        starttime = topr.TOPRStartDateTime.strftime("%H%M%S");
        stopdate = topr.TOPRStopDateTime.strftime("%Y%m%d");
        stoptime = topr.TOPRStopDateTime.strftime("%H%M%S");
        setuptime = int(((topr.TOPRStopDateTime - topr.TOPRStartDateTime).total_seconds())/60)
        insertSFR2SAP(topr.WorkCenter,topr.OrderNo,topr.OperationNumber,0,0,setuptime,0,setuptime,startdate,starttime,stopdate,stoptime,topr.EmpID,topr.MachineNumber)
        #-- MACHINE : WORKING
        sql = "UPDATE [T_MC] SET [StartDateTime] = CURRENT_TIMESTAMP, [StopDateTime] = NULL, [Status] = 'WORKING' WHERE ID = " + str(topr.T_MC_ID)
        cursor.execute(sql)
        conn.commit()
    #-- OPERATOR : WORKING
    sql = "UPDATE [T_OPR] SET [StartDateTime] = CURRENT_TIMESTAMP, [StopDateTime] = NULL, [Status] = 'WORKING' WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    return

def stopSetupTOPR(id):
    conn = get_connection()
    cursor = conn.cursor()
    #-- OPERATOR : SAVE SETUP TIME
    sql = "UPDATE [T_OPR] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    #-- MACHINE : SAVE SETUP TIME
    topr = getTOPRbyID(id)
    sql = "UPDATE [T_MC] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(topr.T_MC_ID)
    cursor.execute(sql)
    conn.commit()
    #-- LOG : MACHINE SETUP TIME ???
    #-- LOG : OPERATOR SETUP TIME ???
    #-- POST SETUP DATA OF OPERATOR
    topr = getTOPRbyID(id)
    startdate = topr.TOPRStartDateTime.strftime("%Y%m%d");
    starttime = topr.TOPRStartDateTime.strftime("%H%M%S");
    stopdate = topr.TOPRStopDateTime.strftime("%Y%m%d");
    stoptime = topr.TOPRStopDateTime.strftime("%H%M%S");
    setuptime = int(((topr.TOPRStopDateTime - topr.TOPRStartDateTime).total_seconds())/60)
    insertSFR2SAP(topr.WorkCenter,topr.OrderNo,topr.OperationNumber,0,0,setuptime,0,setuptime,startdate,starttime,stopdate,stoptime,topr.EmpID,topr.MachineNumber)
    #-- MACHINE : GO BACK TO WAITING
    sql = "UPDATE [T_MC] SET [StartDateTime] = NULL, [StopDateTime] = NULL, [Status] = 'WAITING' WHERE ID = " + str(topr.T_MC_ID)
    cursor.execute(sql)
    conn.commit()
    #-- OPERATOR : EXIT
    sql = "DELETE FROM [T_OPR] WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    return

def stopWorkTOPR(id):
    conn = get_connection()
    cursor = conn.cursor()
    #-- OPERATOR : SAVE WORKING TIME
    sql = "UPDATE [T_OPR] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    #-- LOG : OPERATOR WORKING TIME ???
    #-- POST WORKING DATA OF OPERATOR
    topr = getTOPRbyID(id)
    startdate = topr.TOPRStartDateTime.strftime("%Y%m%d")
    starttime = topr.TOPRStartDateTime.strftime("%H%M%S")
    stopdate = topr.TOPRStopDateTime.strftime("%Y%m%d")
    stoptime = topr.TOPRStopDateTime.strftime("%H%M%S")
    worktimeOperator = str(int(((topr.TOPRStopDateTime - topr.TOPRStartDateTime).total_seconds())/60))
    worktimeMachine = 0
    if topr.MachineNumber != None:
        worktimeMachine = worktimeOperator
    insertSFR2SAP(topr.WorkCenter,topr.OrderNo,topr.OperationNumber,0,0,0,worktimeMachine,worktimeOperator,startdate,starttime,stopdate,stoptime,topr.EmpID,topr.MachineNumber)
    #-- IF OPERATION IS NOT LABOR TYPE & NO OPERATOR WORKING & MACHINE IS MANUAL
    if(topr.T_MC_ID != None and hasOperatorWorking(topr.T_MC_ID) == False and topr.Auto_Manual.strip() == 'Manual'):
        #-- MACHINE : STOP WORKING
        sql = "UPDATE [T_MC] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE ID = " + str(topr.T_MC_ID)
        cursor.execute(sql)
        conn.commit()
        #-- LOG : MACHINE WORKING TIME ???
    return

def confirmQty():
    #-- POST COMFIRMATION ???
    #-- IF REMAIN QTY == 0 -> CLEAR ALL T_MC & T_OPR
    #-- LOG : CONFIRM ???
    return

def insertSFR2SAP(workcenter,orderNo,operationNo,yiled,scrap,setup,oper,labor,startdate,starttime,finishdate,finishtime,empId,machineNo):
    if machineNo == None:
        machineNo = ""
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [dbo].[SFR2SAP] ([DateTimeStamp],[WorkCenter],[ProductionOrderNo],[OperationNumber],[Yiled],[Scrap],[SetupTime],[OperTime],[LaborTime],[StartDate],[StartTime],[FinishDate],[FinishTime],[EmployeeID],[MachineNo]) VALUES "
    sql += "(CURRENT_TIMESTAMP,"
    sql += "'" + str(workcenter) + "',"
    sql += "'" + str(orderNo) + "',"
    sql += "'" + str(operationNo) + "',"
    sql += "'" + str(yiled) + "',"
    sql += "'" + str(scrap) + "',"
    sql += "'" + str(setup) + "',"
    sql += "'" + str(oper) + "',"
    sql += "'" + str(labor) + "',"
    sql += "'" + str(startdate) + "',"
    sql += "'" + str(starttime) + "',"
    sql += "'" + str(finishdate) + "',"
    sql += "'" + str(finishtime) + "',"
    sql += "'" + str(empId) + "',"
    sql += "'" + str(machineNo) + "')"
    cursor.execute(sql)
    conn.commit()

########################################################################################
########################################################################################
########################################################################################
def FourDigitOperationNo(operationNo):
    result = str(operationNo)
    while len(result) < 4:
        result = "0" + result
    return result
