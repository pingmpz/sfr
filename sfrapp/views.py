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

#------------------------------------------------------------------- TRANSACTION

def transaction(request, orderoprno):
    orderNo = ""
    operationNo = ""
    order = None
    operation = None
    remainQty = -1
    joinList = []
    state = "ERROR"
    operationList = []
    operationStatusList = []
    rejectReasonList = []
    materialGroupList = []
    purchaseGroupList = []
    currentOperation = -1 # For Order !Operation
    operationBefore = -1
    operationAfter = -1
    #--
    if orderoprno == "0":
        state = "FIRSTPAGE"
    else:
        orderNo = orderoprno[0:10]
        operationNo = orderoprno[10:14]
        if isExistOrder(orderNo) == False and isExistSAPOrder(orderNo) == False:
            state = "NODATAFOUND"
        else:
            if isExistOrder(orderNo) == False:
                setDataFromSAP(orderNo)
            order = getOrder(orderNo)
            operationList = getOperationList(orderNo)
            if isExistOperation(orderNo, operationNo):
                state = "DATAFOUND"
                operation = getOperation(orderNo, operationNo)
                remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
                for i in range(len(operationList)):
                    #-- GET STATUS OF OPERATION LIST
                    tempRemainQty = operationList[i].ProcessQty - (operationList[i].AcceptedQty + operationList[i].RejectedQty)
                    if operationList[i].ProcessQty == 0:
                        operationStatusList.append("WAITING")
                    elif tempRemainQty == 0:
                        operationStatusList.append("COMPLETED")
                    elif tempRemainQty > 0 and operationList[i].ProcessStart != None:
                        operationStatusList.append("WORKING")
                    elif tempRemainQty > 0:
                        operationStatusList.append("READY")
                    else:
                        operationStatusList.append("ERROR")
                    #-- GET PREV & NEXT OPERATION
                    if operationNo == operationList[i].OperationNo.strip():
                        if i != 0:
                            operationBefore = operationList[i-1].OperationNo
                        if i != len(operationList) - 1:
                            operationAfter = operationList[i+1].OperationNo
                #-- GET JOIN LIST
                if operation.JoinToOrderNo == None and operation.JoinToOperationNo == None:
                    joinList = getJoinList(orderNo, operationNo)
                #-- GET ETC LIST
                rejectReasonList = getRejectReasonList()
                materialGroupList = getMaterialGroupList()
                purchaseGroupList = getPurchaseGroupList()
            #-- GET OPERATION WITH REMAINING QTY > 0
            else:
                state = "NOOPERATIONFOUND"
                if len(operationList) > 0:
                    currentOperation = operationList[0].OperationNo
                    for i in range(len(operationList)):
                        tempRemainQty = operationList[i].ProcessQty - (operationList[i].AcceptedQty + operationList[i].RejectedQty)
                        if tempRemainQty > 0:
                            currentOperation = operationList[i].OperationNo
                            break
    context = {
        'orderNo' : orderNo,
        'operationNo' : operationNo,
        'state' : state,
        'order' : order,
        'operation' : operation,
        'remainQty' : remainQty,
        'joinList' : joinList,
        'operationList' : operationList,
        'operationStatusList' : operationStatusList,
        'rejectReasonList' : rejectReasonList,
        'materialGroupList' : materialGroupList,
        'purchaseGroupList' : purchaseGroupList,
        'currentOperation' : currentOperation,
        'operationBefore' : operationBefore,
        'operationAfter' : operationAfter,
    }
    return render(request, 'transaction.html', context)

def join_activity(request, orderoprno):
    orderNo = orderoprno[0:10]
    operationNo = orderoprno[10:14]
    order = getOrder(orderNo)
    operation = getOperation(orderNo, operationNo)
    context = {
        'orderNo' : orderNo,
        'operationNo' : operationNo,
    }
    return render(request, 'join_activity.html', context)

#------------------------------------------------------------------------ MASTER

def wc_master(request):
    workCenterList = getWorkCenterList()
    context = {
        'workCenterList' : workCenterList,
    }
    return render(request, 'wc_master.html', context)

def user_master(request):
    operatorList = getOperatorList()
    context = {
        'operatorList' : operatorList,
    }
    return render(request, 'user_master.html', context)

def rej_master(request):
    rejectReasonList = getRejectReasonList()
    context = {
        'rejectReasonList' : rejectReasonList,
    }
    return render(request, 'rej_master.html', context)

def matg_master(request):
    materialGroupList = getMaterialGroupList()
    context = {
        'materialGroupList' : materialGroupList,
    }
    return render(request, 'matg_master.html', context)

def purg_master(request):
    purchaseGroupList = getPurchaseGroupList()
    context = {
        'purchaseGroupList' : purchaseGroupList,
    }
    return render(request, 'purg_master.html', context)

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
    machine = getMachine(machine_no)
    if machine != None:
        MachineNumber = machine.MachineNumber
        MachineName = machine.MachineName
        if isMachineWorking(machine_no):
            tmc = getWorkingMachineNo(machine_no)
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
    operator = getOperator(operator_id)
    if operator != None:
        EmpID = (operator.EmpID).strip()
        EmpName = operator.EmpName
        Department = operator.Remarks
        if isOperatorWorking(operator_id):
            topr = getWorkingEmpId(operator_id)
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
    #-- MACHINE : ADD
    insertTMC(order_no, operation_no, machine_no)
    data = {
    }
    return JsonResponse(data)

def delete_tmc(request):
    id = request.GET.get('id')
    #-- MACHINE : DELETE
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
    #-- OPERATION : UPDATE PROCESS STOP
    tcon = getTCON(order_no, operation_no)
    if tcon.ProcessStart == None:
        updateQtyTCON(order_no, operation_no, 0, 0, 0, "START")
    #-- OPERATOR : WORKING/SETUP
    insertTOPR(order_no, operation_no, operator_id, tmc_id, status)
    #-- IF OPERATION IS NOT LABOR TYPE
    if tmc_id != "NULL":
        #-- MACHINE : WORKING/SETUP
        updateTMC(tmc_id, status)
    data = {
    }
    return JsonResponse(data)

def start_work_topr(request):
    id = request.GET.get('id')
    topr = getTOPR(id)
    if topr.TMCStatus.strip() == "SETUP":
        #-- OPERATOR : SAVE SETUP TIME
        updateTOPR(id, "COMPLETED")
        #-- LOG OPERATOR SETUP TIME ?????
        #-- MACHINE : SAVE SETUP TIME
        updateTMC(topr.T_MC_ID, "COMPLETED")
        #-- LOG MACHINE SETUP TIME ?????
        #-- POST SETUP TIME
        topr = getTOPR(id)
        setuptime = int(((topr.TOPRStopDateTime - topr.TOPRStartDateTime).total_seconds())/60)
        insertSFR2SAP(topr.MachineNumber,topr.OrderNo,topr.OperationNumber,0,0,setuptime,0,setuptime,topr.TOPRStartDateTime,topr.TOPRStopDateTime,topr.EmpID)
        #-- POST SETUP TIME FOR JOINING LIST ?????
        #-- MACHINE : WORKING
        updateTMC(topr.T_MC_ID, "WORKING")
    #-- OPERATOR : WORKING
    updateTOPR(id, "WORKING")
    data = {
    }
    return JsonResponse(data)

def stop_setup_topr(request):
    id = request.GET.get('id')
    #-- OPERATOR : SAVE SETUP TIME
    updateTOPR(id, "COMPLETED")
    #-- LOG OPERATOR SETUP TIME ?????
    #-- MACHINE : SAVE SETUP TIME
    topr = getTOPR(id)
    updateTMC(topr.T_MC_ID, "COMPLETED")
    #-- LOG MACHINE SETUP TIME ?????
    #-- POST SETUP TIME
    setuptime = int(((topr.TOPRStopDateTime - topr.TOPRStartDateTime).total_seconds())/60)
    insertSFR2SAP(topr.MachineNumber,topr.OrderNo,topr.OperationNumber,0,0,setuptime,0,setuptime,topr.TOPRStartDateTime,topr.TOPRStopDateTime,topr.EmpID)
    #-- POST SETUP TIME FOR JOINING LIST ?????
    #-- MACHINE : WAITING
    updateTMC(topr.T_MC_ID, "WAITING")
    #-- OPERATOR : EXIT
    deleteTOPR(id)
    data = {
    }
    return JsonResponse(data)

def stop_work_topr(request):
    id = request.GET.get('id')
    topr = getTOPR(id)
    status = topr.Status
    #-- OPERATOR : SAVE WORKING TIME
    updateTOPR(id, "COMPLETED")
    #-- LOG OPERATOR WORKING TIME ?????
    #-- POST WORKING TIME
    topr = getTOPR(id)
    workcenter = topr.WorkCenter
    worktimeOperator = str(int(((topr.TOPRStopDateTime - topr.TOPRStartDateTime).total_seconds())/60))
    worktimeMachine = 0
    if topr.MachineNumber != None:
        worktimeMachine = worktimeOperator
        workcenter = topr.MachineNumber
    if status == "EXT-WORK":
        worktimeOperator = 0
    insertSFR2SAP(workcenter,topr.OrderNo,topr.OperationNumber,0,0,0,worktimeMachine,worktimeOperator,topr.TOPRStartDateTime,topr.TOPRStopDateTime,topr.EmpID)
    #-- POST WORKING TIME FOR JOINING LIST ?????
    #-- IF OPERATION IS NOT LABOR TYPE & NO OPERATOR WORKING & MACHINE IS MANUAL
    if(topr.T_MC_ID != None and hasOperatorWorking(topr.T_MC_ID) == False and topr.Auto_Manual.strip() == 'Manual'):
        #-- MACHINE : STOP
        updateTMC(topr.T_MC_ID, "COMPLETED")
        #-- LOG MACHINE WORKING TIME ?????
    data = {
    }
    return JsonResponse(data)

def stop_mc_tmc(request):
    id = request.GET.get('id')
    #-- MACHINE : STOP
    updateTMC(id, "COMPLETED")
    #-- LOG MACHINE WORKING TIME ?????
    data = {
    }
    return JsonResponse(data)

def get_topr_for_confirm(request):
    id = request.GET.get('id')
    topr = getTOPR(id)
    operator = getOperator(topr.EmpID)
    operator_text = operator.EmpID.strip() + " | " + operator.EmpName
    machine_text = ""
    if topr.MachineNumber != None:
        machine = getMachine(topr.MachineNumber)
        machine_text = machine.MachineNumber + " | " + machine.MachineName
    start_time = topr.TOPRStartDateTime.strftime("%d-%m-%Y, %H:%M:%S")
    stop_time = topr.TOPRStopDateTime.strftime("%d-%m-%Y, %H:%M:%S")
    data = {
        'operator_text': operator_text,
        'machine_text': machine_text,
        'start_time': start_time,
        'stop_time': stop_time,
    }
    return JsonResponse(data)

def confirm(request):
    confirm_id = request.GET.get('confirm_id')
    good_qty = request.GET.get('good_qty')
    reject_qty = request.GET.get('reject_qty')
    reject_reason = request.GET.get('reject_reason')
    other_reason = request.GET.get('other_reason')
    if reject_reason == "-1":
        reject_reason = ""
    elif reject_reason == "OTHER":
        reject_reason = other_reason
    #-- POST CONFIRMATION
    topr = getTOPR(confirm_id)
    workcenter = topr.WorkCenter
    if topr.MachineNumber != None:
        workcenter = topr.MachineNumber
    insertSFR2SAP(workcenter,topr.OrderNo,topr.OperationNumber,good_qty,reject_qty,0,0,0,"","",topr.EmpID)
    #-- UPDATE QTY OF CURRECT OPERATION
    updateQtyTCON(topr.OrderNo,topr.OperationNumber, 0, good_qty, reject_qty, "STOP")
    #-- UPDATE PROCESS QTY OF NEXT OPERATION
    nextOperation = getNextOperation(topr.OrderNo,topr.OperationNumber)
    if nextOperation != None:
        updateQtyTCON(nextOperation.ProductionOrderNo,nextOperation.OperationNumber, good_qty, 0, 0)
    data = {
    }
    return JsonResponse(data)


################################################################################
################################### DATABASE ###################################
################################################################################

def get_connection():
    # conn = pyodbc.connect('Driver={SQL Server};''Server=SVSP-SQL;''Database=SFR;''UID=CCSGROUPS\sqladmin;''PWD=$ql@2019;''Trusted_Connection=yes;')
    # conn = pyodbc.connect('Driver={SQL Server};''Server=SVCCS-SFR\SQLEXPRESS;''Database=SFR;''UID=sa;''PWD=$fr@2021;''Trusted_Connection=yes;')
    conn = pyodbc.connect('Driver={SQL Server};''Server=SVCCS-SFR\SQLEXPRESS01;''Database=SFR;''UID=sa;''PWD=$fr@2021;''Trusted_Connection=yes;')
    return conn

#-------------------------------------------------------------------------- LIST

def getWorkCenterList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [WorkCenter]"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperatorList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [Employee]"
    cursor.execute(sql)
    return cursor.fetchall()

def getRejectReasonList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [RejectReason]"
    cursor.execute(sql)
    return cursor.fetchall()

def getMaterialGroupList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [MaterialGroup]"
    cursor.execute(sql)
    return cursor.fetchall()

def getPurchaseGroupList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [PurchaseGroup]"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperationList(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperatingWorkCenterList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingWorkCenter] as OWC INNER JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' ORDER BY OWC.OperatingWorCenterID ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperatingOperatorList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingOperator] as OOPR INNER JOIN [User] as U ON OOPR.EmpID = U.EmpID"
    sql += " INNER JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorCenterID = OWC.OperatingWorCenterID"
    sql += " INNER JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.OrderNo = '" + order_no + "' AND OOPR.OperationNo = '" + operation_no + "' ORDER BY OOPR.OperatingOperatorID ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getJoinList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE JoinToOrderNo = '" + order_no + "' AND JoinToOperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    return cursor.fetchall()

#-------------------------------------------------------------------------- ITEM

def getOrder(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OrderControl] as ORD"
    sql += " INNER JOIN [SAP_Order] as SAPORD ON ORD.OrderNo = SAPORD.ProductionOrderNo"
    sql += " WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] as OPT"
    sql += " INNER JOIN [SAP_Routing] as SAPRT ON OPT.OperationNo = SAPRT.OperationNumber"
    sql += " INNER JOIN [WorkCenter] as WC ON OPT.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getWorkCenter(workcenter_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [WorkCenter] WHERE WorkCenterNo = '" + workcenter_no + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getOperator(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [Employee] WHERE EmpID = '" + operator_id + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

#----------------------------------------------------------------------- BOOLEAN

def isExistSAPOrder(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [SAP_Order] WHERE ProductionOrderNo = '" + order_no + "'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def isExistSAPOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [SAP_Routing] WHERE ProductionOrderNo = '" + order_no + "' AND OperationNumber = '" + operation_no + "'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def isExistOrder(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OrderControl] WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def isExistOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def isExistOperator(emp_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [Employee] WHERE EmpID = '" + emp_id + "'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

#--------------------------------------------------------------------------- EXC

def setDataFromSAP(order_no):
    setOrderControlFromSAP(order_no)
    setOperationControlFromSAP(order_no)
    return

def setOrderControlFromSAP(order_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OrderControl] ([OrderNo]) VALUES ('" + order_no + "')"
    cursor.execute(sql)
    conn.commit()
    return

def setOperationControlFromSAP(order_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM [SAP_Order] WHERE ProductionOrderNo = '" + order_no + "'"
    cursor.execute(sql)
    order = cursor.fetchall()[0]
    sql = "SELECT * FROM [SAP_Routing] WHERE ProductionOrderNo = '" + order_no + "' ORDER BY OperationNumber ASC"
    cursor.execute(sql)
    operations = cursor.fetchall()
    isFirstOperation = True
    for i in range(len(operations)):
        sql = "INSERT INTO [OperationControl] ([OrderNo],[OperationNo],[WorkCenterNo],[ProcessQty],[AcceptedQty],[RejectedQty])"
        if isFirstOperation:
            sql += " VALUES ('" + order_no + "', '" + operations[i].OperationNumber + "', '" + operations[i].WorkCenter + "', " + str(order.ProductionOrderQuatity) + ", 0, 0)"
            isFirstOperation = False
        else:
            sql += " VALUES ('" + order_no + "', '" + operations[i].OperationNumber + "', '" + operations[i].WorkCenter + "', 0, 0, 0)"
        cursor.execute(sql)
        conn.commit()
    return

def insertSFR2SAP_Report(workcenter, order_no, operation_no, yiled, scrap, setup_time, oper_time, labor_time, start_date_time, stop_date_time, emp_id):
    start_date = start_date_time.strftime("%Y%m%d")
    start_time = start_date_time.strftime("%H%M%S")
    stop_date = stop_date_time.strftime("%Y%m%d")
    stop_time = stop_date_time.strftime("%H%M%S")
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [SFR2SAP_Report] ([DateTimeStamp],[WorkCenter],[ProductionOrderNo],[OperationNumber],[Yiled],[Scrap],[SetupTime],[OperTime],[LaborTime],[StartDate],[StartTime],[FinishDate],[FinishTime],[EmployeeID])"
    sql += " VALUES (CURRENT_TIMESTAMP,"
    sql += "'" + str(workcenter) + "',"
    sql += "'" + str(order_no) + "',"
    sql += "'" + str(operation_no) + "',"
    sql += "'" + str(yiled) + "',"
    sql += "'" + str(scrap) + "',"
    sql += "'" + str(setup_time) + "',"
    sql += "'" + str(oper_time) + "',"
    sql += "'" + str(labor_time) + "',"
    sql += "'" + str(start_date) + "',"
    sql += "'" + str(start_time) + "',"
    sql += "'" + str(stop_date) + "',"
    sql += "'" + str(stop_time) + "',"
    sql += "'" + str(emp_id) + "')"
    cursor.execute(sql)
    conn.commit()
    return

################################################################################
################################################################################
################################################################################
def FourDigitOperationNo(operationNo):
    result = str(operationNo)
    while len(result) < 4:
        result = "0" + result
    return result
