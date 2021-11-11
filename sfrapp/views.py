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
    state = "ERROR"
    operationList = []
    operationStatusList = []
    joinList = []
    historyOperateList = []
    historyConfirmList = []
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
                #-- GET HISTORY LIST
                historyOperateList = getHistoryOperateList(orderNo, operationNo)
                historyConfirmList = getHistoryConfirmList(orderNo, operationNo)
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
        'operationList' : operationList,
        'operationStatusList' : operationStatusList,
        'joinList' : joinList,
        'historyOperateList' : historyOperateList,
        'historyConfirmList' : historyConfirmList,
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

#--------------------------------------------------------------------------- SAP

def sap_order(request):
    sapOrderList = getSAPOrderList()
    context = {
        'sapOrderList' : sapOrderList,
    }
    return render(request, 'sap_order.html', context)

def sap_routing(request):
    sapRoutingList = getSAPRoutingList()
    context = {
        'sapRoutingList' : sapRoutingList,
    }
    return render(request, 'sap_routing.html', context)

def sap_report(request):
    sapReportList = getSAPReportList()
    context = {
        'sapReportList' : sapReportList,
    }
    return render(request, 'sap_report.html', context)

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
    work_center_group = request.GET.get('work_center_group')
    canAdd = False
    invalid_text = ''
    WorkCenterNo = None
    WorkCenterName = None
    workcenter = getWorkCenter(workcenter_no)
    if workcenter != None:
        WorkCenterNo = workcenter.WorkCenterNo
        WorkCenterName = workcenter.WorkCenterName
        print(workcenter.WorkCenterGroup, work_center_group)
        if workcenter.IsRouting:
            invalid_text = WorkCenterNo + " is a rounting."
        elif workcenter.WorkCenterGroup != work_center_group:
            invalid_text = WorkCenterNo + " is in " + workcenter.WorkCenterGroup + " Group."
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
            invalid_text = operator_id + ' is working at ' + str(oopr.OperatorOrderNo) + "-" + str(oopr.OperatorOperationNo) + "."
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
    refresh = False
    #-- OPERATOR : WORKING/SETUP/EXT-WORK
    insertOperatingOperator(order_no, operation_no, operator_id, owc_id, status)
    #-- IF OPERATION IS NOT LABOR TYPE
    if owc_id != "-1":
        #-- WORKCENTER : WORKING/SETUP
        updateOperatingWorkCenter(owc_id, status)
    #-- IF NOT START OPERATION YET
    if hasNotStartOperation(order_no, operation_no):
        refresh = True
        #-- OPERATION : START
        updateOperationControl(order_no, operation_no, 0, 0, "START")
        #-- IF NOT START ORDER YET
        if hasNotStartOrder(order_no):
            #-- ORDER : START
            updateOrderControl(order_no, "START")
    data = {
        'refresh' : refresh,
    }
    return JsonResponse(data)

def start_work_operating_operator(request):
    id = request.GET.get('id')
    oopr = getOperatorOperatingByID(id)
    if oopr.WorkCenterStatus.strip() == "SETUP":
        #-- OPERATOR : SAVE SETUP TIME
        updateOperatingOperator(id, "COMPLETED")
        #-- OPERATOR : SETUP TIME LOG
        oopr = getOperatorOperatingByID(id)
        insertHistoryOperate(oopr.OrderNo,oopr.OperationNo, oopr.EmpID, oopr.WorkCenterNo, "SETUP", oopr.OperatorStartDateTime, oopr.OperatorStopDateTime)
        #-- WORKCENTER : SAVE SETUP TIME
        updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
        #-- WORKCENTER : SETUP TIME LOG ?? SETUP NO NEED KEEP DATA
        # owc = getWorkCenterOperatingByID(oopr.OperatingWorkCenterID)
        # insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "SETUP", owc.StartDateTime, owc.StopDateTime)
        #-- SAP : SETUP TIME
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
    #-- OPERATOR : SETUP TIME LOG
    oopr = getOperatorOperatingByID(id)
    insertHistoryOperate(oopr.OrderNo,oopr.OperationNo, oopr.EmpID, oopr.WorkCenterNo, "SETUP", oopr.OperatorStartDateTime, oopr.OperatorStopDateTime)
    #-- WORKCENTER : SAVE SETUP TIME
    updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
    #-- WORKCENTER : SETUP TIME LOG ?? SETUP NO NEED KEEP DATA
    # owc = getWorkCenterOperatingByID(oopr.OperatingWorkCenterID)
    # insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "SETUP", owc.StartDateTime, owc.StopDateTime)
    #-- SAP : SETUP TIME
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
    status = oopr.OperatorStatus
    type = "OPERATE"
    #-- OPERATOR : SAVE WORKING TIME
    updateOperatingOperator(id, "COMPLETED")
    #-- SAP : WORKING TIME
    oopr = getOperatorOperatingByID(id)
    workcenter = oopr.WorkCenterNo
    worktimeOperator = str(int(((oopr.OperatorStopDateTime - oopr.OperatorStartDateTime).total_seconds())/60))
    worktimeMachine = worktimeOperator
    if oopr.WorkCenterNo == None:
        workcenter = getOperation(oopr.OperatorOrderNo, oopr.OperatorOperationNo).WorkCenterNo
        worktimeMachine = 0
    if status == "EXT-WORK":
        worktimeOperator = 0
        type = "EXT-WORK"
    insertSFR2SAP_Report(workcenter,oopr.OperatorOrderNo,oopr.OperatorOperationNo,0,0,0,worktimeMachine,worktimeOperator,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
    #-- OPERATOR : OPERATING TIME LOG
    insertHistoryOperate(oopr.OperatorOrderNo,oopr.OperatorOperationNo, oopr.EmpID, workcenter, type, oopr.OperatorStartDateTime, oopr.OperatorStopDateTime)
    #-- IF OPERATION IS NOT LABOR TYPE & NO OPERATOR WORKING & WORKCENTER IS MANUAL
    if(oopr.OperatingWorkCenterID != None and hasOperatorOperating(oopr.OperatingWorkCenterID) == False and oopr.MachineType.strip() == 'Manual'):
        #-- WORKCENTER : STOP
        updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
        #-- WORKCENTER : OPERATING TIME LOG ?? MANUAL NO NEED KEEP DATA
        # owc = getWorkCenterOperatingByID(oopr.OperatingWorkCenterID)
        # insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "OPERATE", owc.StartDateTime, owc.StopDateTime)
    data = {
    }
    return JsonResponse(data)

def stop_operating_workcenter(request):
    id = request.GET.get('id')
    #-- WORKCENTER : STOP
    updateOperatingWorkCenter(id, "COMPLETED")
    #-- WORKCENTER : OPERATING TIME LOG
    owc = getWorkCenterOperatingByID(id)
    insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "OPERATE", owc.StartDateTime, owc.StopDateTime)
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
    #-- SAP : CONFIRM
    oopr = getOperatorOperatingByID(confirm_id)
    workcenter = oopr.WorkCenterNo
    if oopr.WorkCenterNo == None:
        workcenter = getOperation(oopr.OperatorOrderNo, oopr.OperatorOperationNo).WorkCenterNo
    insertSFR2SAP_Report(workcenter,oopr.OperatorOrderNo,oopr.OperatorOperationNo,good_qty,reject_qty,0,0,0,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
    #-- CONFIRM : LOG
    insertHistoryConfirm(oopr.OperatorOrderNo,oopr.OperatorOperationNo, oopr.EmpID, workcenter, good_qty, reject_qty, reject_reason)
    #-- UPDATE QTY OF CURRENT OPERATION
    updateOperationControl(oopr.OperatorOrderNo,oopr.OperatorOperationNo, good_qty, reject_qty, "UPDATEQTY")
    #-- UPDATE PROCESS QTY OF NEXT OPERATION
    nextOperation = getNextOperation(oopr.OperatorOrderNo,oopr.OperatorOperationNo)
    if nextOperation != None:
        updateOperationControl(nextOperation.OrderNo,nextOperation.OperationNo, good_qty, 0, "PROCESSQTY")
    #-- NO MORE REMAINING QTY
    operation = getOperation(oopr.OperatorOrderNo, oopr.OperatorOperationNo)
    remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
    if remainQty == 0:
        #-- CLEAR ALL CONTROL DATA
        deleteAllControlData(oopr.OperatorOrderNo, oopr.OperatorOperationNo)
        #-- STOP OPERATION
        updateOperationControl(oopr.OperatorOrderNo, oopr.OperatorOperationNo, 0, 0, "STOP")
        #-- IF LAST OPERATION IN ORDER
        if isLastOperation(oopr.OperatorOrderNo, oopr.OperatorOperationNo):
            print('YES')
            #-- ORDER : STOP
            updateOrderControl(oopr.OperatorOrderNo, "STOP")
    data = {
    }
    return JsonResponse(data)

def reset_all(request):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
            DELETE FROM OperatingOperator
            DELETE FROM OperatingWorkCenter
            DELETE FROM SFR2SAP_Report
            DELETE FROM HistoryConfirm
            DELETE FROM HistoryOperate
            DELETE FROM OrderControl
            DELETE FROM OperationControl
            """
    cursor.execute(sql)
    conn.commit()
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

def getSAPOrderList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [SAP_Order] ORDER BY ProductionOrderNo ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getSAPRoutingList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [SAP_Routing] ORDER BY ProductionOrderNo ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getSAPReportList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [SFR2SAP_Report] ORDER BY ProductionOrderNo ASC"
    cursor.execute(sql)
    return cursor.fetchall()

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
    sql = "SELECT * FROM [OperationControl] as OC INNER JOIN [WorkCenter] as WC ON OC.WorkCenterNo = WC.WorkCenterNo WHERE OrderNo = '" + order_no + "' ORDER BY OperationNo ASC"
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

def getHistoryOperateList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryOperate] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    return cursor.fetchall()

def getHistoryConfirmList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryConfirm] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
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
    sql = "SELECT OOPR.OrderNo as OperatorOrderNo, OOPR.OperationNo as OperatorOperationNo, OOPR.StartDateTime as OperatorStartDateTime, OOPR.StopDateTime as OperatorStopDateTime, OWC.Status as WorkCenterStatus, *"
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
    sql = "SELECT OOPR.OrderNo as OperatorOrderNo, OOPR.OperationNo as OperatorOperationNo, OOPR.StartDateTime as OperatorStartDateTime, OOPR.StopDateTime as OperatorStopDateTime, OOPR.Status as OperatorStatus, OWC.Status as WorkCenterStatus, *"
    sql += " FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.OperatingOperatorID = " + str(id)
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0]

def getNextOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE OrderNo = '" + order_no + "' AND OperationNo > '" + operation_no + "' ORDER BY OperationNo ASC"
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

def hasNotStartOrder(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OrderControl] WHERE OrderNo = '" + order_no + "' AND ProcessStart IS NULL"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def hasNotStartOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' AND ProcessStart IS NULL"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def isLastOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE OrderNo = '" + order_no + "' ORDER BY OperationNo DESC"
    cursor.execute(sql)
    result = cursor.fetchall()
    return (result[0].OperationNo.strip() == operation_no)

#--------------------------------------------------------------------------- SET

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

#------------------------------------------------------------------------ INSERT

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

def insertHistoryOperate(order_no, operation_no, operator_id, workcenter_no, type, start_date_time, stop_date_time):
    startDateTime = start_date_time.strftime("%Y-%m-%d %H:%M:%S")
    stopDateTime = stop_date_time.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [HistoryOperate] ([OrderNo],[OperationNo],[EmpID],[WorkCenterNo],[Type],[StartDateTime],[StopDateTime])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "'," + str(operator_id) + ",'" + workcenter_no + "','" + type + "','" + startDateTime + "','" + stopDateTime + "')"
    cursor.execute(sql)
    conn.commit()
    return

def insertHistoryConfirm(order_no, operation_no, operator_id, workcenter_no, accept, reject, reason):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [HistoryConfirm] ([OrderNo],[OperationNo],[EmpID],[WorkCenterNo],[AcceptedQty],[RejectedQty],[RejectReason],[ConfirmDateTime])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "','" + str(operator_id) + "','" + workcenter_no + "','" + str(accept) + "','" + str(reject) + "','" + reason + "',CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    conn.commit()
    return

#------------------------------------------------------------------------ UPDATE

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
    return

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

def updateOrderControl(order_no, status):
    conn = get_connection()
    cursor = conn.cursor()
    sql = ""
    if status == "START":
        sql = "UPDATE [OrderControl] SET [ProcessStart] = CURRENT_TIMESTAMP WHERE OrderNo = '" + order_no + "'"
    if status == "STOP":
        sql = "UPDATE [OrderControl] SET [ProcessStop] = CURRENT_TIMESTAMP WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    conn.commit()
    return

def updateOperationControl(order_no, operation_no, accept, reject, status):
    conn = get_connection()
    cursor = conn.cursor()
    sql = ""
    if status == "START":
        sql = "UPDATE [OperationControl] SET [ProcessStart] = CURRENT_TIMESTAMP WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    if status == "STOP":
        sql = "UPDATE [OperationControl] SET [ProcessStop] = CURRENT_TIMESTAMP WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    if status == "UPDATEQTY":
        sql = "UPDATE [OperationControl] SET [AcceptedQty] += " + str(accept) + ", [RejectedQty] += " + str(reject) + " WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no  + "'"
    if status == "PROCESSQTY":
        sql = "UPDATE [OperationControl] SET [ProcessQty] += " + str(accept) + " WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    conn.commit()
    return

#------------------------------------------------------------------------ DELETE

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

def deleteAllControlData(order_no, operation_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM [OperatingOperator] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    conn.commit()
    cursor = conn.cursor()
    sql = "DELETE FROM [OperatingWorkCenter] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
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
