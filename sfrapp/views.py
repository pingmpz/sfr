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

def emp_master(request):
    operatorList = getOperatorList()
    context = {
        'operatorList' : operatorList,
    }
    return render(request, 'emp_master.html', context)

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

#-- NEED FIX
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

def get_workcenter_data(request):
    workcenter_no = request.GET.get('workcenter_no')
    canAdd = False
    invalid_text = ''
    WorkCenterNo = None
    WorkCenterName = None
    workcenter = getWorkCenter(workcenter_no)
    if workcenter != None:
        WorkCenterNo = workcenter.WorkCenterNo
        WorkCenterName = workcenter.WorkCenterName
        if workcenter.IsRouting:
            invalid_text = WorkCenterNo + " is a rounting."
        elif isWorkCenterOperating(workcenter_no):
            owc = getWorkCenterOperatingByWorkCenterNo(workcenter_no)
            invalid_text = WorkCenterNo + " is working at " + owc.OrderNo + "-" + owc.OperationNo + "."
        else:
            canAdd = True
    else:
        canAdd = False
        invalid_text = 'Work Center Not Found'
    data = {
        'canAdd': canAdd,
        'invalid_text' : invalid_text,
        'WorkCenterNo': WorkCenterNo,
        'WorkCenterName': WorkCenterName,
    }
    return JsonResponse(data)

def get_operator_data(request):
    operator_id = request.GET.get('operator_id')
    canAdd = False
    invalid_text = ''
    EmpID = None
    EmpName = None
    Section = None
    operator = getOperator(operator_id)
    if operator != None:
        EmpID = (operator.EmpID).strip()
        EmpName = operator.EmpName
        Section = operator.Section
        if isOperatorOperating(operator_id):
            oopr = getOperatorOperatingByEmpID(operator_id)
            invalid_text = operator_id + ' is working at ' + oopr.OrderNo + "-" + oopr.OperationNo + "."
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
        'Section': Section,
    }
    return JsonResponse(data)

def get_operating_workcenter_list(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    OWCList = [list(i) for i in getOperatingWorkCenterList(order_no, operation_no)]
    hasOperatorOperatingList = []
    for owc in OWCList:
        hasOperatorOperatingList.append(hasOperatorOperating(owc[0]))
    data = {
        'OWCList': OWCList,
        'hasOperatorOperatingList': hasOperatorOperatingList,
    }
    return JsonResponse(data)

def get_operating_operator_list(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    OOPRList = [list(i) for i in getOperatingOperatorList(order_no, operation_no)]
    data = {
        'OOPRList': OOPRList,
    }
    return JsonResponse(data)

def add_operating_workcenter(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    workcenter_no = request.GET.get('workcenter_no')
    #-- WORKCENTER : ADD
    insertOperatingWorkCenter(order_no, operation_no, workcenter_no)
    data = {
    }
    return JsonResponse(data)

def delete_operating_workcenter(request):
    id = request.GET.get('id')
    #-- WORKCENTER : DELETE
    deleteOperatingWorkCenter(id)
    data = {
    }
    return JsonResponse(data)

def add_operating_operator(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    operator_id = request.GET.get('operator_id')
    owc_id = request.GET.get('owc_id')
    status = request.GET.get('status')
    #-- OPERATOR : WORKING/SETUP
    insertOperatingOperator(order_no, operation_no, operator_id, owc_id, status)
    #-- IF OPERATION IS NOT LABOR TYPE
    if owc_id != "-1":
        #-- WORKCENTER : WORKING/SETUP
        updateOperatingWorkCenter(owc_id, status)
    data = {
    }
    return JsonResponse(data)

def start_work_operating_operator(request):
    id = request.GET.get('id')
    oopr = getOperatorOperatingByID(id)
    if oopr.WorkCenterStatus.strip() == "SETUP":
        #-- OPERATOR : SAVE SETUP TIME
        updateOperatingOperator(id, "COMPLETED")
        #-- WORKCENTER : SAVE SETUP TIME
        updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
        #-- POST SETUP TIME
        oopr = getOperatorOperatingByID(id)
        setuptime = int(((oopr.OperatorStopDateTime - oopr.OperatorStartDateTime).total_seconds())/60)
        insertSFR2SAP_Report(oopr.WorkCenterNo,oopr.OrderNo,oopr.OperationNo,0,0,setuptime,0,setuptime,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
        #-- WORKCENTER : WORKING
        updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "WORKING")
    #-- OPERATOR : WORKING
    updateOperatingOperator(id, "WORKING")
    data = {
    }
    return JsonResponse(data)

def stop_setup_operating_operator(request):
    id = request.GET.get('id')
    #-- OPERATOR : SAVE SETUP TIME
    updateOperatingOperator(id, "COMPLETED")
    #-- WORKCENTER : SAVE SETUP TIME
    oopr = getOperatorOperatingByID(id)
    updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
    #-- POST SETUP TIME
    setuptime = int(((oopr.OperatorStopDateTime - oopr.OperatorStartDateTime).total_seconds())/60)
    insertSFR2SAP_Report(oopr.WorkCenterNo,oopr.OrderNo,oopr.OperationNo,0,0,setuptime,0,setuptime,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
    #-- WORKCENTER : WAITING
    updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "WAITING")
    #-- OPERATOR : EXIT
    deleteOperatingOperator(id)
    data = {
    }
    return JsonResponse(data)

def stop_work_operating_operator(request):
    id = request.GET.get('id')
    oopr = getOperatorOperatingByID(id)
    status = oopr.Status
    #-- OPERATOR : SAVE WORKING TIME
    updateOperatingOperator(id, "COMPLETED")
    #-- POST WORKING TIME
    oopr = getOperatorOperatingByID(id)
    workcenter = oopr.WorkCenterNo
    worktimeOperator = str(int(((oopr.OperatorStopDateTime - oopr.OperatorStartDateTime).total_seconds())/60))
    worktimeMachine = 0
    if oopr.WorkCenterNo != None:
        worktimeMachine = worktimeOperator
        workcenter = oopr.WorkCenterNo
    if status == "EXT-WORK":
        worktimeOperator = 0
    insertSFR2SAP_Report(workcenter,oopr.OrderNo,oopr.OperationNo,0,0,0,worktimeMachine,worktimeOperator,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
    #-- IF OPERATION IS NOT LABOR TYPE & NO OPERATOR WORKING & WORKCENTER IS MANUAL
    if(oopr.OperatingWorkCenterID != None and hasOperatorOperating(oopr.OperatingWorkCenterID) == False and oopr.MachineType.strip() == 'Manual'):
        #-- WORKCENTER : STOP
        updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
    data = {
    }
    return JsonResponse(data)

def stop_operating_workcenter(request):
    id = request.GET.get('id')
    #-- WORKCENTER : STOP
    updateOperatingWorkCenter(id, "COMPLETED")
    data = {
    }
    return JsonResponse(data)

def get_data_for_confirm(request):
    id = request.GET.get('id')
    oopr = getOperatorOperatingByID(id)
    operator_text = oopr.EmpID.strip() + " | " + oopr.EmpName
    workcenter_text = ""
    if oopr.WorkCenterNo != None:
        workcenter = getWorkCenter(oopr.WorkCenterNo)
        workcenter_text = workcenter.WorkCenterNo + " | " + workcenter.WorkCenterName
    start_time = oopr.OperatorStartDateTime.strftime("%d-%m-%Y, %H:%M:%S")
    stop_time = oopr.OperatorStopDateTime.strftime("%d-%m-%Y, %H:%M:%S")
    data = {
        'operator_text': operator_text,
        'workcenter_text': workcenter_text,
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
    oopr = getOperatorOperating(confirm_id)
    workcenter = oopr.WorkCenter
    if oopr.MachineNumber != None:
        workcenter = oopr.MachineNumber
    insertSFR2SAP_Report(workcenter,oopr.OrderNo,oopr.OperationNumber,good_qty,reject_qty,0,0,0,"","",oopr.EmpID)
    #-- UPDATE QTY OF CURRECT OPERATION
    updateQtyTCON(oopr.OrderNo,oopr.OperationNumber, 0, good_qty, reject_qty, "STOP")
    #-- UPDATE PROCESS QTY OF NEXT OPERATION
    nextOperation = getNextOperation(oopr.OrderNo,oopr.OperationNumber)
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
    sql += " WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' ORDER BY OWC.OperatingWorkCenterID ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperatingOperatorList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
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
    sql = "SELECT * FROM [WorkCenter] WHERE WorkCenterNo = '" + str(workcenter_no) + "'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getOperator(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [Employee] WHERE EmpID = " + str(operator_id)
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getWorkCenterOperatingByWorkCenterNo(workcenter_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingWorkCenter] WHERE WorkCenterNo = '" + workcenter_no + "' AND Status <> 'COMPLETED'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getOperatorOperatingByEmpID(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT *"
    sql += " FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.EmpID = " + str(operator_id) + " AND OOPR.Status <> 'COMPLETED' AND OOPR.Status <> 'EXT-WORK'"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getWorkCenterOperatingByID(id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingWorkCenter] WHERE OperatingWorkCenterID = " + str(id)
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getOperatorOperatingByID(id):
    cursor = get_connection().cursor()
    sql = "SELECT OOPR.StartDateTime as OperatorStartDateTime, OOPR.StopDateTime as OperatorStopDateTime, OWC.Status as WorkCenterStatus, *"
    sql += " FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.OperatingOperatorID = " + str(id)
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

def isWorkCenterOperating(workcenter_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingWorkCenter] WHERE WorkCenterNo = '" + workcenter_no + "' AND Status <> 'COMPLETED'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def isOperatorOperating(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingOperator] WHERE EmpID = " + str(operator_id) + " AND Status <> 'COMPLETED' AND Status <> 'EXT-WORK'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def hasOperatorOperating(owc_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingOperator] WHERE OperatingWorkCenterID = " + str(owc_id) + " AND Status <> 'COMPLETED'"
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

def insertOperatingWorkCenter(order_no, operation_no, workcenter_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OperatingWorkCenter] ([OrderNo],[OperationNo],[WorkCenterNo],[Status])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "','" + workcenter_no + "','WAITING')"
    cursor.execute(sql)
    conn.commit()
    return

def insertOperatingOperator(order_no, operation_no, operator_id, owc_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OperatingOperator] ([OrderNo],[OperationNo],[EmpID],[OperatingWorkCenterID],[Status],[StartDateTime])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "','" + str(operator_id) + "','" + str(owc_id) + "','" + status + "',CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    conn.commit()
    return

def deleteOperatingWorkCenter(id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM [OperatingWorkCenter] WHERE OperatingWorkCenterID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    return

def deleteOperatingOperator(id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM [OperatingOperator] WHERE OperatingOperatorID = " + str(id)
    cursor.execute(sql)
    conn.commit()
    return

def updateOperatingWorkCenter(id, status):
    conn = get_connection()
    cursor = conn.cursor()
    sql = ""
    if status == "WAITING":
        sql = "UPDATE [OperatingWorkCenter] SET [StartDateTime] = NULL, [StopDateTime] = NULL, [Status] = 'WAITING' WHERE OperatingWorkCenterID = " + str(id)
    if status == "WORKING":
        sql = "UPDATE [OperatingWorkCenter] SET [StartDateTime] = CURRENT_TIMESTAMP, [StopDateTime] = NULL, [Status] = 'WORKING' WHERE OperatingWorkCenterID = " + str(id)
    if status == "SETUP":
        sql = "UPDATE [OperatingWorkCenter] SET [StartDateTime] = CURRENT_TIMESTAMP, [StopDateTime] = NULL, [Status] = 'SETUP' WHERE OperatingWorkCenterID = " + str(id)
    if status == "COMPLETED":
        sql = "UPDATE [OperatingWorkCenter] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE OperatingWorkCenterID = " + str(id)
    cursor.execute(sql)
    conn.commit()

def updateOperatingOperator(id, status):
    conn = get_connection()
    cursor = conn.cursor()
    sql = ""
    if status == "WAITING":
        sql = "UPDATE [OperatingOperator] SET [StartDateTime] = NULL, [StopDateTime] = NULL, [Status] = 'WAITING' WHERE OperatingOperatorID = " + str(id)
    if status == "WORKING":
        sql = "UPDATE [OperatingOperator] SET [StartDateTime] = CURRENT_TIMESTAMP, [StopDateTime] = NULL, [Status] = 'WORKING' WHERE OperatingOperatorID = " + str(id)
    if status == "SETUP":
        sql = "UPDATE [OperatingOperator] SET [StartDateTime] = CURRENT_TIMESTAMP, [StopDateTime] = NULL, [Status] = 'SETUP' WHERE OperatingOperatorID = " + str(id)
    if status == "COMPLETED":
        sql = "UPDATE [OperatingOperator] SET [StopDateTime] = CURRENT_TIMESTAMP, [Status] = 'COMPLETED' WHERE OperatingOperatorID = " + str(id)
    cursor.execute(sql)
    conn.commit()

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
