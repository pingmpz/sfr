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
    IsOperating = False
    remainQty = -1
    state = "ERROR" #-- FIRSTPAGE / NODATAFOUND / NOOPERATIONFOUND / DATAFOUND
    operationList = []
    operationStatusList = []
    joinList = []
    historyOperateList = []
    historyConfirmList = []
    historyJoinList = []
    rejectReasonList = []
    materialGroupList = []
    purchaseGroupList = []
    currencyList = []
    currentOperation = -1
    operationBefore = -1 #-- For Prev Operation Button
    operationAfter = -1 #-- For Next Operation Button
    #--
    if orderoprno == "0":
        state = "FIRSTPAGE"
    else:
        orderNo = orderoprno[0:len(orderoprno) - 4]
        operationNo = orderoprno[len(orderoprno) - 4:len(orderoprno)]
        if isExistOrder(orderNo) == False and isExistSAPOrder(orderNo) == False:
            state = "NODATAFOUND"
        else:
            state = "NOOPERATIONFOUND"
            if isExistOrder(orderNo) == False:
                setDataFromSAP(orderNo)
            order = getOrder(orderNo)
            operationList = getOperationList(orderNo)
            if isExistOperation(orderNo, operationNo):
                state = "DATAFOUND"
                operation = getOperation(orderNo, operationNo)
                print(operation)
                IsOperating = isOperatingOperation(orderNo, operationNo)
                remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
                for i in range(len(operationList)):
                    #-- GET STATUS OF OPERATION LIST
                    tempRemainQty = operationList[i].ProcessQty - (operationList[i].AcceptedQty + operationList[i].RejectedQty)
                    if operationList[i].ProcessQty == 0:
                        operationStatusList.append("WAITING")
                    elif tempRemainQty == 0:
                        operationStatusList.append("COMPLETED")
                    elif operationList[i].JoinToOrderNo != None and operationList[i].JoinToOperationNo != None:
                        operationStatusList.append("JOINING")
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
                historyJoinList = getHistoryJoinList(orderNo, operationNo)
                #-- GET ETC LIST
                rejectReasonList = getRejectReasonList()
                materialGroupList = getMaterialGroupList()
                purchaseGroupList = getPurchaseGroupList()
                currencyList = getCurrencyList()
            #-- GET OPERATION WITH REMAINING QTY > 0
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
        'IsOperating' : IsOperating,
        'remainQty' : remainQty,
        'operationList' : operationList,
        'operationStatusList' : operationStatusList,
        'joinList' : joinList,
        'historyOperateList' : historyOperateList,
        'historyConfirmList' : historyConfirmList,
        'historyJoinList' : historyJoinList,
        'rejectReasonList' : rejectReasonList,
        'materialGroupList' : materialGroupList,
        'purchaseGroupList' : purchaseGroupList,
        'currencyList' : currencyList,
        'currentOperation' : currentOperation,
        'operationBefore' : operationBefore,
        'operationAfter' : operationAfter,
    }
    return render(request, 'transaction.html', context)

def join_activity(request, orderoprno):
    orderNo = orderoprno[0:len(orderoprno) - 4]
    operationNo = orderoprno[len(orderoprno) - 4:len(orderoprno)]
    order = getOrder(orderNo)
    operation = getOperation(orderNo, operationNo)
    joinableList = getJoinableList(orderNo, operation.WorkCenterGroup)
    context = {
        'orderNo' : orderNo,
        'operationNo' : operationNo,
        'operation' : operation,
        'joinableList' : joinableList,
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

def curr_master(request):
    currencyList = getCurrencyList()
    context = {
        'currencyList' : currencyList,
    }
    return render(request, 'curr_master.html', context)

#--------------------------------------------------------------------------- SAP

def sap_order(request, fdate, fhour):
    if fdate == "TODAY":
        fdate = datetime.today().strftime('%Y-%m-%d')
    if fhour == "NOW":
        fhour = datetime.today().strftime('%H')
    sapOrderList = getSAPOrderList(fdate, fhour)
    context = {
        'fdate' : fdate,
        'fhour' : fhour,
        'sapOrderList' : sapOrderList,
    }
    return render(request, 'sap_order.html', context)

def sap_routing(request, fdate, fhour):
    if fdate == "TODAY":
        fdate = datetime.today().strftime('%Y-%m-%d')
    if fhour == "NOW":
        fhour = datetime.today().strftime('%H')
    sapRoutingList = getSAPRoutingList(fdate, fhour)
    context = {
        'fdate' : fdate,
        'fhour' : fhour,
        'sapRoutingList' : sapRoutingList,
    }
    return render(request, 'sap_routing.html', context)

def sap_report(request, fdate, fhour):
    if fdate == "TODAY":
        fdate = datetime.today().strftime('%Y-%m-%d')
    if fhour == "NOW":
        fhour = datetime.today().strftime('%H')
    sapReportList = getSAPReportList(fdate, fhour)
    context = {
        'fdate' : fdate,
        'fhour' : fhour,
        'sapReportList' : sapReportList,
    }
    return render(request, 'sap_report.html', context)

def sap_mod(request, fdate, fhour):
    if fdate == "TODAY":
        fdate = datetime.today().strftime('%Y-%m-%d')
    if fhour == "NOW":
        fhour = datetime.today().strftime('%H')
    sapModifierList = getSAPModifierList(fdate, fhour)
    context = {
        'fdate' : fdate,
        'fhour' : fhour,
        'sapModifierList' : sapModifierList,
    }
    return render(request, 'sap_mod.html', context)

################################################################################
#################################### REQUEST ###################################
################################################################################

#-------------------------------------------------------------------- MAIN TABLE

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

#-------------------------------------------------------------- INNER MAIN TABLE

def add_operating_workcenter(request):
    #-- *** ONLY MACHINE TYPE ***
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    workcenter_no = request.GET.get('workcenter_no')
    #-- WORKCENTER : ADD
    insertOperatingWorkCenter(order_no, operation_no, workcenter_no)
    data = {
    }
    return JsonResponse(data)

def delete_operating_workcenter(request):
    #-- *** ONLY MACHINE TYPE ***
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
    #-- IF JOINING
    joinList = getJoinList(order_no, operation_no)
    for join in joinList:
        if hasNotStartOperation(join.OrderNo, join.OperationNo):
            #-- OPERATION : START
            updateOperationControl(join.OrderNo, join.OperationNo, 0, 0, "START")
            #-- IF NOT START ORDER YET
            if hasNotStartOrder(join.OrderNo):
                #-- ORDER : START
                updateOrderControl(join.OrderNo, "START")
    data = {
        'refresh' : refresh,
    }
    return JsonResponse(data)

def start_work_operating_operator(request):
    #-- *** ONLY MACHINE TYPE ***
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
        #-- SAP : SETUP TIME
        oopr = getOperatorOperatingByID(id)
        setuptime = int(((oopr.OperatorStopDateTime - oopr.OperatorStartDateTime).total_seconds())/60)
        insertSFR2SAP_Report(oopr.WorkCenterNo,oopr.OrderNo,oopr.OperationNo,0,0,setuptime,0,0,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
        #-- WORKCENTER : WORKING
        updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "WORKING")
    #-- OPERATOR : WORKING
    updateOperatingOperator(id, "WORKING")
    data = {
    }
    return JsonResponse(data)

def stop_setup_operating_operator(request):
    #-- *** ONLY MACHINE TYPE ***
    id = request.GET.get('id')
    #-- OPERATOR : SAVE SETUP TIME
    updateOperatingOperator(id, "COMPLETED")
    #-- OPERATOR : SETUP TIME LOG
    oopr = getOperatorOperatingByID(id)
    insertHistoryOperate(oopr.OrderNo,oopr.OperationNo, oopr.EmpID, oopr.WorkCenterNo, "SETUP", oopr.OperatorStartDateTime, oopr.OperatorStopDateTime)
    #-- WORKCENTER : SAVE SETUP TIME
    updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
    #-- SAP : SETUP TIME
    setuptime = int(((oopr.OperatorStopDateTime - oopr.OperatorStartDateTime).total_seconds())/60)
    #-- IF SETUP TIME IS LESS THAN 1 MIN DON'T SEND DATA TOP SAP
    if True: # if setuptime != 0:
        insertSFR2SAP_Report(oopr.WorkCenterNo,oopr.OrderNo,oopr.OperationNo,0,0,setuptime,0,0,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
    #-- WORKCENTER : WAITING
    updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "WAITING")
    #-- OPERATOR : EXIT
    deleteOperatingOperator(id)
    #-- CHECK REMAINING IS OPERATING
    IsOperating = isOperatingOperation(oopr.OrderNo, oopr.OperationNo)
    data = {
        'IsOperating' : IsOperating,
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
    elif oopr.MachineType.strip() == 'Auto':
        worktimeMachine = 0
    #-- IF EXTERNAL PROCESS NEED TO SEND
    # if status == "EXT-WORK":
    #     worktimeOperator = 0
    #     type = "EXT-WORK"
    #-- IF EXTERNAL PROCESS DONT SEND DATA TO SAP (COMFIRMATION WILL HAVE ALL THIS INFO)
    #-- IF WORK TIME IS LESS THAN 1 MIN DON'T SEND DATA TOP SAP
    if status != "EXT-WORK": # if status != "EXT-WORK" or worktimeMachine != 0 or worktimeOperator != 0:
        insertSFR2SAP_Report(workcenter,oopr.OperatorOrderNo,oopr.OperatorOperationNo,0,0,0,worktimeMachine,worktimeOperator,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
    #-- OPERATOR : OPERATING TIME LOG
    insertHistoryOperate(oopr.OperatorOrderNo,oopr.OperatorOperationNo, oopr.EmpID, workcenter, type, oopr.OperatorStartDateTime, oopr.OperatorStopDateTime)
    #-- IF OPERATION IS NOT LABOR TYPE & NO OPERATOR WORKING & WORKCENTER IS MANUAL
    if oopr.OperatingWorkCenterID != None and hasOperatorOperating(oopr.OperatingWorkCenterID) == False and oopr.MachineType.strip() == 'Manual':
        #-- WORKCENTER : STOP
        updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
    #-- CHECK REMAINING IS OPERATING
    IsOperating = isOperatingOperation(oopr.OperatorOrderNo, oopr.OperatorOperationNo)
    data = {
        'IsOperating' : IsOperating,
    }
    return JsonResponse(data)

def stop_operating_workcenter(request):
    #-- *** ONLY AUTO MACHINE TYPE ***
    id = request.GET.get('id')
    #-- WORKCENTER : STOP
    updateOperatingWorkCenter(id, "COMPLETED")
    #-- SAP : WORKING TIME
    owc = getWorkCenterOperatingByID(id)
    worktimeMachine = str(int(((owc.StopDateTime - owc.StartDateTime).total_seconds())/60))
    #-- IF WORK TIME IS LESS THAN 1 MIN DON'T SEND DATA TOP SAP
    if True: # if worktimeMachine != 0:
        insertSFR2SAP_Report(owc.WorkCenterNo,owc.OrderNo,owc.OperationNo,0,0,0,worktimeMachine,0,owc.StartDateTime,owc.StopDateTime,'9999')
    #-- WORKCENTER : OPERATING TIME LOG
    insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "OPERATE", owc.StartDateTime, owc.StopDateTime)
    #-- CHECK REMAINING IS OPERATING
    IsOperating = isOperatingOperation(owc.OrderNo, owc.OperationNo)
    data = {
        'IsOperating' : IsOperating,
    }
    return JsonResponse(data)

#------------------------------------------------------------------ CONFIRMATION

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
    #-- RECHECK QTY
    oopr = getOperatorOperatingByID(confirm_id)
    orderNo = oopr.OperatorOrderNo
    operationNo = oopr.OperatorOperationNo
    workcenter = oopr.WorkCenterNo
    operation = getOperation(orderNo, operationNo)
    remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
    if remainQty >= (int(good_qty) + int(reject_qty)):
        #-- SAP : CONFIRM
        if oopr.WorkCenterNo == None:
            workcenter = getOperation(orderNo, operationNo).WorkCenterNo
        #-- SPECIAL CASE **
        sap_reject_qty = reject_qty
        if reject_reason == "MATERIAL DEFECT":
            sap_reject_qty = 0
        insertSFR2SAP_Report(workcenter,orderNo,operationNo,good_qty,sap_reject_qty,0,0,0,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
        #-- CONFIRM : LOG
        insertHistoryConfirm(orderNo,operationNo, oopr.EmpID, workcenter, good_qty, reject_qty, reject_reason)
        #-- UPDATE QTY OF CURRENT OPERATION
        updateOperationControl(orderNo,operationNo, good_qty, reject_qty, "UPDATEQTY")
        #-- UPDATE PROCESS QTY OF NEXT OPERATION
        nextOperation = getNextOperation(orderNo,operationNo)
        if nextOperation != None:
            updateOperationControl(nextOperation.OrderNo,nextOperation.OperationNo, good_qty, 0, "PROCESSQTY")
        #-- NO MORE REMAINING QTY
        operation = getOperation(orderNo, operationNo)
        remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
        if remainQty == 0:
            #-- IF AUTO MACHINE(S) STILL WORKING
            owcList = getOperatingWorkCenterList(orderNo, operationNo)
            for owc in owcList:
                if owc.Status == 'WORKING':
                    #-- WORKCENTER : STOP
                    updateOperatingWorkCenter(owc.OperatingWorkCenterID, "COMPLETED")
                    #-- SAP : WORKING TIME
                    owc = getWorkCenterOperatingByID(owc.OperatingWorkCenterID)
                    worktimeMachine = str(int(((owc.StopDateTime - owc.StartDateTime).total_seconds())/60))
                    insertSFR2SAP_Report(owc.WorkCenterNo,owc.OrderNo,owc.OperationNo,0,0,0,worktimeMachine,0,owc.StartDateTime,owc.StopDateTime,'9999')
                    #-- WORKCENTER : OPERATING TIME LOG
                    insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "OPERATE", owc.StartDateTime, owc.StopDateTime)
            #-- CLEAR ALL CONTROL DATA
            deleteAllOperatingData(orderNo, operationNo)
            #-- STOP OPERATION
            updateOperationControl(orderNo, operationNo, 0, 0, "STOP")
            #-- IF LAST OPERATION IN ORDER
            if isLastOperation(orderNo, operationNo):
                #-- ORDER : STOP
                updateOrderControl(orderNo, "STOP")
    data = {
    }
    return JsonResponse(data)

#-------------------------------------------------------------------------- JOIN

def join(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    join_list = request.GET.getlist('join_list[]')
    #-- CLEAR ALL CONTROL DATA OF JOIN PROCESS (MAIN)
    deleteAllOperatingData(order_no, operation_no)
    for join_item in join_list:
        join_order_no = join_item[0:10]
        join_operation_no = join_item[10:14]
        #-- JOIN PROCESS
        joinProcess(order_no, operation_no, join_order_no, join_operation_no)
        #-- CLEAR ALL CONTROL DATA OF JOIN PROCESS
        deleteAllOperatingData(join_order_no, join_operation_no)
    data = {
    }
    return JsonResponse(data)

def break_join(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    operation = getOperation(order_no, operation_no)
    joinList = getJoinList(order_no, operation_no)
    operating_workcenter_list = getOperatingWorkCenterList(order_no, operation_no)
    operating_operator_list = getOperatingOperatorList(order_no, operation_no)
    for join in joinList:
        #-- COPY COMPLETE OPERATING OPERATION TO JOINING OPERATION
        for owc in operating_workcenter_list:
            owc_id = getInsertJoinOperatingWorkCenter(join.OrderNo, join.OperationNo, owc.WorkCenterNo, owc.StartDateTime, owc.StopDateTime)
            for oopr in operating_operator_list:
                if oopr.OperatingWorkCenterID == owc.OperatingWorkCenterID:
                    insertJoinOperatingOperator(join.OrderNo, join.OperationNo, oopr.EmpID, owc_id, oopr.StartDateTime, oopr.StopDateTime)
        #-- REMOVE JOIN
        joinProcessRemove(join.OrderNo, join.OperationNo)
        #-- HISTORY : JOIN
        insertHistoryJoin(order_no, operation_no, join.OrderNo, join.OperationNo, join.JoinStartDateTime)
    data = {
    }
    return JsonResponse(data)

#---------------------------------------------------------------------- MODIFIER

def delete_operation(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    operation = getOperation(order_no, operation_no)
    nextlink = "0"
    #-- CLEAR DATA MIGHT LEFT (LIKE WAITING WORKCENTER)
    deleteAllOperatingData(order_no, operation_no)
    #-- TRANSFER PROCESS QTY TO NEXT OPERATION
    nextOperation = getNextOperation(order_no, operation_no)
    if nextOperation != None:
        nextlink = nextOperation.OrderNo + nextOperation.OperationNo
        updateOperationControl(nextOperation.OrderNo,nextOperation.OperationNo, operation.ProcessQty, 0, "PROCESSQTY")
    else:
        #-- ORDER : STOP
        updateOrderControl(orderNo, "STOP")
    #-- SAP MODIFIER : DELETE OPERATION
    insertSFR2SAP_Modifier_Delete(order_no, operation_no)
    #-- HISTORY : DELETE OPERATION
    insertHistoryDelete(order_no, operation_no, getClientIP(request))
    #-- DELETE THIS OPERATION
    deleteOperationControl(order_no, operation_no)
    data = {
        'nextlink' : nextlink,
    }
    return JsonResponse(data)

def validate_new_operation(request):
    order_no = request.GET.get('order_no')
    new_operation_no = request.GET.get('new_operation_no')
    canAdd = True
    #1
    if isExistOperation(order_no, new_operation_no):
        canAdd = False
    #2
    operationList = getOperationList(order_no)
    for i in range(len(operationList)):
        if operationList[i].ProcessStart != None and new_operation_no < operationList[i].OperationNo:
            canAdd = False
            break
    #3
    if isExistDeletedOperation(order_no, new_operation_no):
        canAdd = False
    data = {
        'canAdd': canAdd,
    }
    return JsonResponse(data)

def validate_routing(request):
    work_center_no = request.GET.get('work_center_no')
    canUse = True
    work_center = getWorkCenter(work_center_no)
    if work_center == None:
        canUse = False
    elif work_center.IsRouting == False:
        canUse = False
    data = {
        'canUse': canUse,
    }
    return JsonResponse(data)

def add_operation(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('new_operation_no')
    work_center_no = request.GET.get('work_center_no')
    control_key = request.GET.get('control_key')
    est_setup_time = request.GET.get('est_setup_time')
    est_operate_time = request.GET.get('est_operate_time')
    est_labor_time = request.GET.get('est_labor_time')
    pdt = request.GET.get('pdt')
    purchasing_org = request.GET.get('purchasing_org')
    cost_element = request.GET.get('cost_element')
    mat_group = request.GET.get('mat_group')
    purchasing_group = request.GET.get('purchasing_group')
    price_unit = request.GET.get('price_unit')
    price = request.GET.get('price')
    currency = request.GET.get('currency')
    #-- ADD OPERATION CONTROL
    insertOperationControl(order_no, operation_no, work_center_no)
    #-- SAP : ADD OPERATION
    insertSFR2SAP_Modifier_Add(order_no, operation_no, control_key, work_center_no, pdt, cost_element, price_unit, price, currency, mat_group, purchasing_group, purchasing_org, est_setup_time, est_operate_time, est_labor_time)
    #-- HISTORY : ADD OPERATION @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    #-- IF NEXT OPERATION HAS PROCESS QTY TRANSFER TO NEW OPERATION
    nextOperation = getNextOperation(order_no, operation_no)
    if nextOperation != None:
        updateOperationControl(order_no, operation_no, nextOperation.ProcessQty, 0, "PROCESSQTY")
        updateOperationControl(order_no,nextOperation.OperationNo, (nextOperation.ProcessQty * -1), 0, "PROCESSQTY")
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
            DELETE FROM SFR2SAP_Modifier
            DELETE FROM HistoryConfirm
            DELETE FROM HistoryOperate
            DELETE FROM HistoryJoin
            DELETE FROM HistoryDelete
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

def getSAPOrderList(fdate, fhour):
    cursor = get_connection().cursor()
    sql = ""
    if fhour == "ALLDAY":
        sql = "SELECT * FROM [SAP_Order] WHERE DateGetFromSAP >= '" + fdate + " 00:00:00' AND DateGetFromSAP <= '" + fdate + " 23:59:59' ORDER BY DateGetFromSAP DESC"
    else:
        sql = "SELECT * FROM [SAP_Order] WHERE DateGetFromSAP >= '" + fdate + " " + fhour + ":00:00' AND DateGetFromSAP <= '" + fdate + " " + fhour + ":59:59' ORDER BY DateGetFromSAP DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getSAPRoutingList(fdate, fhour):
    cursor = get_connection().cursor()
    sql = ""
    if fhour == "ALLDAY":
        sql = "SELECT * FROM [SAP_Routing] WHERE DateGetFromSAP >= '" + fdate + " 00:00:00' AND DateGetFromSAP <= '" + fdate + " 23:59:59' ORDER BY DateGetFromSAP DESC"
    else:
        sql = "SELECT * FROM [SAP_Routing] WHERE DateGetFromSAP >= '" + fdate + " " + fhour + ":00:00' AND DateGetFromSAP <= '" + fdate + " " + fhour + ":59:59' ORDER BY DateGetFromSAP DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getSAPReportList(fdate, fhour):
    cursor = get_connection().cursor()
    sql = ""
    if fhour == "ALLDAY":
        sql = "SELECT * FROM [SFR2SAP_Report] WHERE DateTimeStamp >= '" + fdate + " 00:00:00' AND DateTimeStamp <= '" + fdate + " 23:59:59' ORDER BY DateTimeStamp DESC"
    else:
        sql = "SELECT * FROM [SFR2SAP_Report] WHERE DateTimeStamp >= '" + fdate + " " + fhour + ":00:00' AND DateTimeStamp <= '" + fdate + " " + fhour + ":59:59' ORDER BY DateTimeStamp DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getSAPModifierList(fdate, fhour):
    cursor = get_connection().cursor()
    if fhour == "ALLDAY":
        sql = "SELECT * FROM [SFR2SAP_Modifier] WHERE DateTimeStamp >= '" + fdate + " 00:00:00' AND DateTimeStamp <= '" + fdate + " 23:59:59' ORDER BY DateTimeStamp DESC"
    else:
        sql = "SELECT * FROM [SFR2SAP_Modifier] WHERE DateTimeStamp >= '" + fdate + " " + fhour + ":00:00' AND DateTimeStamp <= '" + fdate + " " + fhour + ":59:59' ORDER BY DateTimeStamp DESC"
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

def getCurrencyList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [Currency]"
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

def getJoinableList(order_no, work_center_group):
    cursor = get_connection().cursor()
    sql = "SELECT OC.OrderNo as OCOrderNo, OC.OperationNo as OCOperationNo, OC.WorkCenterNo as OCWorkCenterNo, *"
    sql += " FROM [OperationControl] as OC INNER JOIN [WorkCenter] as WC ON OC.WorkCenterNo = WC.WorkCenterNo"
    sql += " LEFT JOIN [OperatingOperator] as OOPR ON OC.OrderNo = OOPR.OrderNo AND OC.OperationNo = OOPR.OperationNo"
    sql += " WHERE "
    #1
    sql += " ProcessQty - (AcceptedQty + RejectedQty) <> 0"
    #2
    sql += " AND (EmpID IS NULL OR STATUS = 'COMPLETED')"
    #3
    sql += " AND WorkCenterType = 'Machine'"
    #4
    sql += " AND WC.WorkCenterGroup = '" + work_center_group + "'"
    #5
    sql += " AND OC.OrderNo <> '" + order_no + "'"
    #6
    sql += " AND JoinToOrderNo IS NULL AND JoinToOperationNo IS NULL"
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

def getHistoryJoinList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryJoin] "
    sql += " WHERE (JoinToOrderNo = '" + order_no + "' AND JoinToOperationNo = '" + operation_no + "')"
    sql += " OR (JoinByOrderNo = '" + order_no + "' AND JoinByOperationNo = '" + operation_no + "')"
    cursor.execute(sql)
    return cursor.fetchall()

#-------------------------------------------------------------------------- ITEM

def getOrder(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OrderControl] as ORD"
    sql += " INNER JOIN [SAP_Order] as SAPORD ON ORD.OrderNo = SAPORD.ProductionOrderNo"
    sql += " WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    return cursor.fetchone()

def getOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] as OPT"
    sql += " INNER JOIN [WorkCenter] as WC ON OPT.WorkCenterNo = WC.WorkCenterNo"
    sql += " LEFT JOIN [SAP_Routing] as SAPRT ON OPT.OrderNo = SAPRT.ProductionOrderNo AND OPT.OperationNo = SAPRT.OperationNumber"
    sql += " WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    return cursor.fetchone()

def getWorkCenter(workcenter_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [WorkCenter] WHERE WorkCenterNo = '" + str(workcenter_no) + "'"
    cursor.execute(sql)
    return cursor.fetchone()

def getOperator(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [Employee] WHERE EmpID = " + str(operator_id)
    cursor.execute(sql)
    return cursor.fetchone()

def getWorkCenterOperatingByWorkCenterNo(workcenter_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingWorkCenter] WHERE WorkCenterNo = '" + workcenter_no + "' AND Status <> 'COMPLETED'"
    cursor.execute(sql)
    return cursor.fetchone()

def getOperatorOperatingByEmpID(operator_id):
    cursor = get_connection().cursor()
    sql = "SELECT OOPR.OrderNo as OperatorOrderNo, OOPR.OperationNo as OperatorOperationNo, OOPR.StartDateTime as OperatorStartDateTime, OOPR.StopDateTime as OperatorStopDateTime, OWC.Status as WorkCenterStatus, *"
    sql += " FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.EmpID = " + str(operator_id) + " AND OOPR.Status <> 'COMPLETED' AND OOPR.Status <> 'EXT-WORK'"
    cursor.execute(sql)
    return cursor.fetchone()

def getWorkCenterOperatingByID(id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingWorkCenter] WHERE OperatingWorkCenterID = " + str(id)
    cursor.execute(sql)
    return cursor.fetchone()

def getOperatorOperatingByID(id):
    cursor = get_connection().cursor()
    sql = "SELECT OOPR.OrderNo as OperatorOrderNo, OOPR.OperationNo as OperatorOperationNo, OOPR.StartDateTime as OperatorStartDateTime, OOPR.StopDateTime as OperatorStopDateTime, OOPR.Status as OperatorStatus, OWC.Status as WorkCenterStatus, *"
    sql += " FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.OperatingOperatorID = " + str(id)
    cursor.execute(sql)
    return cursor.fetchone()

def getNextOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE OrderNo = '" + order_no + "' AND OperationNo > '" + operation_no + "' ORDER BY OperationNo ASC"
    cursor.execute(sql)
    return cursor.fetchone()

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

def isOperatingOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingOperator] WHERE OrderNo = '" + order_no + "' and OperationNo = '" + operation_no + "' AND Status <> 'COMPLETED'"
    cursor.execute(sql)
    if len(cursor.fetchall()) > 0:
        return True
    sql = "SELECT * FROM [OperatingWorkCenter] WHERE OrderNo = '" + order_no + "' and OperationNo = '" + operation_no + "' AND Status <> 'COMPLETED'"
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

def isExistDeletedOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryDelete] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

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

def getInsertJoinOperatingWorkCenter(order_no, operation_no, workcenter_no, start_date_time, stop_date_time):
    startDateTime = start_date_time.strftime("%Y-%m-%d %H:%M:%S")
    stopDateTime = stop_date_time.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OperatingWorkCenter] ([OrderNo],[OperationNo],[WorkCenterNo],[StartDateTime],[StopDateTime],[Status])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "','" + workcenter_no + "','" + startDateTime + "','" + stopDateTime + "','COMPLETED')"
    cursor.execute(sql)
    conn.commit()
    sql = "SELECT SCOPE_IDENTITY()"
    cursor.execute(sql)
    result = cursor.fetchall()
    if(len(result) == 0):
        return None
    return result[0][0]

def insertJoinOperatingOperator(order_no, operation_no, operator_id, owc_id, start_date_time, stop_date_time):
    startDateTime = start_date_time.strftime("%Y-%m-%d %H:%M:%S")
    stopDateTime = stop_date_time.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OperatingOperator] ([OrderNo],[OperationNo],[EmpID],[OperatingWorkCenterID],[StartDateTime],[StopDateTime],[Status])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "','" + str(operator_id) + "','" + str(owc_id) + "','" + startDateTime + "','" + stopDateTime + "','COMPLETED')"
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

def insertSFR2SAP_Modifier_Delete(order_no, operation_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [SFR2SAP_Modifier] ([DateTimeStamp],[Mode],[OrderNo],[OperationNo])"
    sql += " VALUES (CURRENT_TIMESTAMP,'31',"
    sql += "'" + str(order_no) + "',"
    sql += "'" + str(operation_no) + "')"
    cursor.execute(sql)
    conn.commit()
    return

def insertSFR2SAP_Modifier_Add(order_no, operation_no, control_key, work_center_no, pdt, cost_element, price_unit, price, currency, mat_group, purchasing_group, purchasing_org, est_setup_time, est_operate_time, est_labor_time):
    conn = get_connection()
    cursor = conn.cursor()
    mode = ""
    sql = ""
    if control_key == "PP01":
        mode = "11"
        sql = "INSERT INTO [SFR2SAP_Modifier]"
        sql += " ([DateTimeStamp],[Mode],[OrderNo],[OperationNo],[ControlKey],[WorkCenter],[SetupTime],[OperTime],[LaborTime])"
        sql += " VALUES (CURRENT_TIMESTAMP,"
        sql += "'" + str(mode) + "',"
        sql += "'" + str(order_no) + "',"
        sql += "'" + str(operation_no) + "',"
        sql += "'" + str(control_key) + "',"
        sql += "'" + str(work_center_no) + "',"
        sql += "" + str(est_setup_time) + ","
        sql += "" + str(est_operate_time) + ","
        sql += "" + str(est_labor_time) + ")"
    elif control_key == "PP02":
        mode = "12"
        sql = "INSERT INTO [SFR2SAP_Modifier]"
        sql += " ([DateTimeStamp],[Mode],[OrderNo],[OperationNo],[ControlKey],[WorkCenter],[PlannedDeliveryTime],[CostElement],[PriceUnit],[Price],[Currency],[MaterialGroup],[PurchasingGroup],[PurchasingOrg])"
        sql += " VALUES (CURRENT_TIMESTAMP,"
        sql += "'" + str(mode) + "',"
        sql += "'" + str(order_no) + "',"
        sql += "'" + str(operation_no) + "',"
        sql += "'" + str(control_key) + "',"
        sql += "'" + str(work_center_no) + "',"
        sql += "" + str(pdt) + ","
        sql += "'" + str(cost_element) + "',"
        sql += "" + str(price_unit) + ","
        sql += "" + str(price) + ","
        sql += "'" + str(currency) + "',"
        sql += "'" + str(mat_group) + "',"
        sql += "'" + str(purchasing_group) + "',"
        sql += "'" + str(purchasing_org) + "')"
    cursor.execute(sql)
    conn.commit()
    return

def insertOperationControl(order_no, operation_no, work_center_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OperationControl] ([OrderNo],[OperationNo],[WorkCenterNo],[ProcessQty],[AcceptedQty],[RejectedQty])"
    sql += " VALUES ('" + order_no + "', '" + operation_no + "', '" + work_center_no + "', 0, 0, 0)"
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

def insertHistoryJoin(order_no, operation_no, join_order_no, join_operation_no, start_date_time):
    startDateTime = start_date_time.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [HistoryJoin] ([JoinToOrderNo],[JoinToOperationNo],[JoinByOrderNo],[JoinByOperationNo],[StartDateTime],[StopDateTime])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "','" + join_order_no + "','" + join_operation_no + "','" + startDateTime + "',CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    conn.commit()
    return

def insertHistoryDelete(order_no, operation_no, ip):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [dbo].[HistoryDelete] ([OrderNo],[OperationNo],[ClientIP],[DeleteDateTime])"
    sql += " VALUES ('" + str(order_no) + "','" + str(operation_no) + "','" + str(ip) + "',CURRENT_TIMESTAMP)"
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

def joinProcess(order_no, operation_no, join_order_no, join_operation_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [OperationControl] SET [JoinToOrderNo] = '" + order_no + "', [JoinToOperationNo] = '" + operation_no + "', [JoinStartDateTime] = CURRENT_TIMESTAMP"
    sql += " WHERE OrderNo = '" + join_order_no + "' AND OperationNo = '" + join_operation_no + "'"
    cursor.execute(sql)
    conn.commit()
    return

def joinProcessRemove(order_no, operation_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [OperationControl] SET [JoinToOrderNo] = NULL, [JoinToOperationNo] = NULL, [JoinStartDateTime] = NULL WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
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

def deleteAllOperatingData(order_no, operation_no):
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

def deleteOperationControl(order_no, operation_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM [OperationControl] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
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

def getClientIP(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
