from django.shortcuts import render, redirect
import pyodbc
from django.http import JsonResponse
from datetime import datetime
from dateutil import parser
# FILE READER
# from openpyxl import load_workbook, Workbook

################################################################################
##################################### PAGES ####################################
################################################################################

def blank(request):
    replace_rm_mat_code()
    context = {
    }
    return render(request, 'blank.html', context)

def index(request):
    context = {
    }
    return render(request, 'index.html', context)

#------------------------------------------------------------------- TRANSACTION

def transaction(request, orderoprno):
    #CONST
    overtimehour = 0
    canMP = False
    orderNo = ""
    operationNo = ""
    order = None
    operation = None
    isFirst = False
    isOperating = False
    isOvertime = False
    hasReportTime = False
    remainQty = -1
    state = "ERROR" #-- FIRSTPAGE / NODATAFOUND / NOOPERATIONFOUND / DATAFOUND
    #-- Left Content List
    operationList = []
    operationStatusList = []
    modList = []
    overTimeOperatorList = []
    overTimeWorkCenterList = []
    joinList = []
    #-- History
    historyOperateList = []
    historyConfirmList = []
    historyJoinList = []
    #-- ETC
    workCenterInGroupList = [] #-- What work center can be used in the same group (Only Machine)
    rejectReasonList = [] #-- All
    materialGroupList = [] #-- All
    purchaseGroupList = [] #-- All
    currencyList = [] #-- All
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
            #-- GET OPERATION WITH REMAINING QTY > 0
            if len(operationList) > 0:
                currentOperation = operationList[0].OperationNo
                for i in range(len(operationList)):
                    tempRemainQty = operationList[i].ProcessQty - (operationList[i].AcceptedQty + operationList[i].RejectedQty)
                    if tempRemainQty > 0:
                        currentOperation = operationList[i].OperationNo
                        break
                #-- IF NO OPERATION INPUT (0000), WILL AUTO REDIRECT TO CURRENT PAGE
                if operationNo == '0000':
                    return redirect('/transaction/' + orderNo + currentOperation)
            if isExistOperation(orderNo, operationNo):
                state = "DATAFOUND"
                #CONST
                overtimehour = getOvertimeHour()
                canMP = getManualReportAllow()
                #OPRATION DETIAL
                operation = getOperation(orderNo, operationNo)
                isFirst = isFirstOperation(orderNo, operationNo)
                isOperating = isOperatingOperation(orderNo, operationNo)
                isOvertime = isOvertimeOperation(orderNo, operationNo)
                hasReportTime = hasReportTimeToSAP(orderNo, operationNo)
                remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
                #-- CHECK CLOSED
                hasNoMoreQty = True
                for i in range(len(operationList)):
                    tempRemainQty = operationList[i].ProcessQty - (operationList[i].AcceptedQty + operationList[i].RejectedQty)
                    if tempRemainQty > 0:
                        hasNoMoreQty = False
                        break
                #-- IF CLOSED DONT SHOW CURRENT OPERATION
                if hasNoMoreQty:
                    currentOperation = -1
                isPartial = False
                for i in range(len(operationList)):
                    #-- GET STATUS OF OPERATION LIST
                    tempRemainQty = operationList[i].ProcessQty - (operationList[i].AcceptedQty + operationList[i].RejectedQty)
                    if isPartial == False and tempRemainQty > 0:
                        isPartial = True
                    temphasReportTime = hasReportTimeToSAP(orderNo, operationList[i].OperationNo)
                    if operationList[i].ProcessQty == 0 and hasNoMoreQty:
                        operationStatusList.append("CLOSED")
                    elif operationList[i].ProcessQty == 0:
                        operationStatusList.append("WAITING")
                    elif operationList[i].JoinToOrderNo != None and operationList[i].JoinToOperationNo != None:
                        operationStatusList.append("JOINING")
                    elif isOvertimeOperation(orderNo, operationList[i].OperationNo):
                        operationStatusList.append("OVERTIME")
                    elif tempRemainQty > 0 and operationList[i].ProcessStart != None:
                        operationStatusList.append("WORKING")
                    elif tempRemainQty > 0 and operationList[i].ProcessStart == None:
                        operationStatusList.append("READY")
                    elif tempRemainQty == 0 and isPartial == False and temphasReportTime:
                        operationStatusList.append("COMPLETED")
                    elif tempRemainQty == 0 and isPartial == False:
                        operationStatusList.append("COMPLETED, NO WORKING TIME REPORT")
                    elif tempRemainQty == 0 and isPartial == True:
                        operationStatusList.append("PARTIALCOMPLETED")
                    else:
                        operationStatusList.append("ERROR")
                    #-- GET PREV & NEXT OPERATION
                    if operationNo == operationList[i].OperationNo.strip():
                        if i != 0:
                            operationBefore = operationList[i-1].OperationNo
                        if i != len(operationList) - 1:
                            operationAfter = operationList[i+1].OperationNo
                #-- MOD LIST
                modList = getModList(orderNo)
                #-- OVERTIME LIST
                overTimeOperatorList = getOverTimeOperatorList(orderNo, operationNo)
                overTimeWorkCenterList = getOverTimeWorkCenterList(orderNo, operationNo)
                #-- JOIN LIST
                if operation.JoinToOrderNo == None and operation.JoinToOperationNo == None:
                    joinList = getJoinList(orderNo, operationNo)
                #-- HISTORY LIST
                historyOperateList = getHistoryOperateList(orderNo, operationNo)
                historyConfirmList = getHistoryConfirmList(orderNo, operationNo)
                historyJoinList = getHistoryJoinList(orderNo, operationNo)
                #-- ETC LIST
                if operation.WorkCenterType == 'Machine':
                    workCenterInGroupList = getWorkCenterInGroupList(operation.WorkCenterGroup)
                rejectReasonList = getRejectReasonList()
                materialGroupList = getMaterialGroupList()
                purchaseGroupList = getPurchaseGroupList()
                currencyList = getCurrencyList()
    printString(orderNo + "-" + operationNo + " (" + state + ")")
    context = {
        'overtimehour' : overtimehour,
        'canMP' : canMP,
        'orderNo' : orderNo,
        'operationNo' : operationNo,
        'state' : state,
        'order' : order,
        'operation' : operation,
        'isFirst' : isFirst,
        'isOperating' : isOperating,
        'isOvertime' : isOvertime,
        'hasReportTime' : hasReportTime,
        'remainQty' : remainQty,
        'operationList' : operationList,
        'operationStatusList' : operationStatusList,
        'modList' : modList,
        'overTimeOperatorList' : overTimeOperatorList,
        'overTimeWorkCenterList' : overTimeWorkCenterList,
        'joinList' : joinList,
        'historyOperateList' : historyOperateList,
        'historyConfirmList' : historyConfirmList,
        'historyJoinList' : historyJoinList,
        'workCenterInGroupList' : workCenterInGroupList,
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

def lot_traveller(request, orderno, lotno):
    orderNo = ""
    LotNo = ""
    order = None
    state = ""
    pltList = []
    plt = None
    operationList = []
    operationList1 = []
    operationList2 = []
    operationList3 = []
    planDayCountList1 = []
    planDayCountList2 = []
    planDayCountList3 = []
    pageCount = 1
    maxRows = 13
    counter = 0
    #--
    if orderno == "0":
        state = "FIRSTPAGE"
    else:
        orderNo = orderno
        LotNo = lotno
        if isExistOrder(orderNo) == False:
            state = "NODATAFOUND"
        else:
            state = "DATAFOUND"
            order = getOrder(orderNo)
            operationList = getOperationList(orderNo)
            pltList = getPTLList(orderNo)
            #-- IF COME FROM FIRST PAGE
            if LotNo == "-1":
                #-- IF NEVER DO PLT GO TO 0
                if pltList == []:
                    return redirect('/lot_traveller/' + orderNo + "&0")
                #-- IF EVER DO PLT GO TO LASTEST PLT
                else:
                    return redirect('/lot_traveller/' + orderNo + "&" + str(pltList[0].LotNo))
            #-- IF TRY TO GO TO 0 AFTER EVER DONE PLT, WILL KICK TO LASTEST PLT
            elif LotNo == "0":
                if pltList != []:
                    return redirect('/lot_traveller/' + orderNo + "&" + str(pltList[0].LotNo))
            else:
                #-- IF TRY TO GO TO # AFTER NEVER DONE PLT, WILL KICK TO 0
                if pltList == []:
                    return redirect('/lot_traveller/' + orderNo + "&0")
                plt = getPTL(orderNo, LotNo)
                for opr in operationList:
                    if opr.OperationNo >= plt.StartOperationNo:
                        if counter == maxRows:
                            pageCount += 1
                            counter = 0
                        start_date = datetime.strptime(opr.PlanStartDate, '%Y-%m-%d')
                        stop_date = datetime.strptime(opr.PlanFinishDate, '%Y-%m-%d')
                        days = stop_date - start_date
                        if pageCount == 1:
                            operationList1.append(opr)
                            planDayCountList1.append(days.days)
                        elif pageCount == 2:
                            operationList2.append(opr)
                            planDayCountList2.append(days.days)
                        else:
                            operationList3.append(opr)
                            planDayCountList3.append(days.days)
                        counter += 1
    context = {
        'orderNo' : orderNo,
        'LotNo' : LotNo,
        'order' : order,
        'state' : state,
        'pltList' : pltList,
        'plt' : plt,
        'operationList' : operationList,
        'operationList1' : operationList1,
        'operationList2' : operationList2,
        'operationList3' : operationList3,
        'planDayCountList1': planDayCountList1,
        'planDayCountList2': planDayCountList2,
        'planDayCountList3': planDayCountList3,
        'pageCount': pageCount,
    }
    return render(request, 'lot_traveller.html', context)

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

#--------------------------------------------------------------------- DATA PAGE

def wc(request, wcno, fmonth):
    if fmonth == "NOW":
        fmonth = datetime.today().strftime('%Y-%m')
    workCenter = getWorkCenter(wcno)
    year = fmonth[0:4]
    month = fmonth[5:7]
    historyTransList = getWorkCenterHistoryTransactionList(wcno, month, year)
    historyOvertimeList = getWorkCenterHistoryOvertimeList(wcno, month, year)
    #STATISTIC
    totalSetupTime = 0
    totalOperTime = 0
    totalWorkingTime = 0
    for trans in historyTransList:
        totalSetupTime = totalSetupTime + trans.Setup
        totalOperTime = totalOperTime + trans.Oper
    totalWorkingTime = totalSetupTime + totalOperTime
    totalSetupTime = str(int(totalSetupTime/60)) + " Hours " + str(int(totalSetupTime%60)) + " Minutes"
    totalOperTime = str(int(totalOperTime/60)) + " Hours " + str(int(totalOperTime%60)) + " Minutes"
    totalWorkingTime = str(int(totalWorkingTime/60)) + " Hours " + str(int(totalWorkingTime%60)) + " Minutes"
    context = {
        'workCenter': workCenter,
        'fmonth': fmonth,
        'historyTransList': historyTransList,
        'historyOvertimeList': historyOvertimeList,
        'totalSetupTime': totalSetupTime,
        'totalOperTime': totalOperTime,
        'totalWorkingTime': totalWorkingTime,
    }
    return render(request, 'wc.html', context)

def emp(request, empid, fmonth):
    if fmonth == "NOW":
        fmonth = datetime.today().strftime('%Y-%m')
    employee = getOperator(empid)
    year = fmonth[0:4]
    month = fmonth[5:7]
    historyTransList = getEmployeeHistoryTransactionList(empid, month, year)
    historyConfirmList = getEmployeeHistoryConfirmList(empid, month, year)
    historyOvertimeList = getEmployeeHistoryOvertimeList(empid, month, year)
    #STATISTIC
    totalSetupTime = 0
    totalLaborTime = 0
    totalWorkingTime = 0
    for trans in historyTransList:
        totalSetupTime = totalSetupTime + trans.Setup
        totalLaborTime = totalLaborTime + trans.Labor
    totalWorkingTime = totalSetupTime + totalLaborTime
    totalSetupTime = str(int(totalSetupTime/60)) + " Hours " + str(int(totalSetupTime%60)) + " Minutes"
    totalLaborTime = str(int(totalLaborTime/60)) + " Hours " + str(int(totalLaborTime%60)) + " Minutes"
    totalWorkingTime = str(int(totalWorkingTime/60)) + " Hours " + str(int(totalWorkingTime%60)) + " Minutes"
    context = {
        'employee': employee,
        'fmonth': fmonth,
        'historyTransList': historyTransList,
        'historyConfirmList': historyConfirmList,
        'historyOvertimeList': historyOvertimeList,
        'totalSetupTime': totalSetupTime,
        'totalLaborTime': totalLaborTime,
        'totalWorkingTime': totalWorkingTime,
    }
    return render(request, 'emp.html', context)

#-------------------------------------------------------------------- MONITORING

def working_order(request):
    workingOrderList = getWorkingOrderList()
    context = {
        'workingOrderList': workingOrderList,
    }
    return render(request, 'working_order.html', context)

def working_wc(request):
    overtimehour = getOvertimeHour()
    warninghour = overtimehour - 2
    workingWorkCenterList = getWorkingWorkCenterList()
    context = {
        'overtimehour': overtimehour,
        'warninghour': warninghour,
        'workingWorkCenterList': workingWorkCenterList,
    }
    return render(request, 'working_wc.html', context)

def working_emp(request):
    overtimehour = getOvertimeHour()
    warninghour = overtimehour - 2
    workingOperatorList = getWorkingOperatorList()
    context = {
        'overtimehour': overtimehour,
        'warninghour': warninghour,
        'workingOperatorList': workingOperatorList,
    }
    return render(request, 'working_emp.html', context)

#------------------------------------------------------------------------ REPORT

def ot_table(request, fmonth):
    if fmonth == "NOW":
        fmonth = datetime.today().strftime('%Y-%m')
    year = fmonth[0:4]
    month = fmonth[5:7]
    overtimeOperatorList = getOvertimeOperatorList(month, year)
    overtimeWorkCenterList = getOvertimeWorkCenterList(month, year)
    context = {
        'fmonth': fmonth,
        'overtimeOperatorList': overtimeOperatorList,
        'overtimeWorkCenterList': overtimeWorkCenterList,
    }
    return render(request, 'ot_table.html', context)

def mp_ot_auto_machine(request, fmonth):
    if fmonth == "NOW":
        fmonth = datetime.today().strftime('%Y-%m')
    year = fmonth[0:4]
    month = fmonth[5:7]
    ReportList = getAutoMachineManualReportOvertimeList(month, year)
    context = {
        'fmonth': fmonth,
        'ReportList': ReportList,
    }
    return render(request, 'mp_ot_auto_machine.html', context)

def monthly_work_rec(request, fmonth):
    if fmonth == "NOW":
        fmonth = datetime.today().strftime('%Y-%m')
    year = fmonth[0:4]
    month = fmonth[5:7]
    empWorkRecords = getEmpWorkRecordsList(month, year)
    workCenterWorkRecords = getWorkCenterWorkRecordsList(month, year)
    context = {
        'fmonth': fmonth,
        'empWorkRecords': empWorkRecords,
        'workCenterWorkRecords': workCenterWorkRecords,
    }
    return render(request, 'monthly_work_rec.html', context)

def zpp02(request):

    context = {

    }
    return render(request, 'zpp02.html', context)

def zpp04(request):

    context = {

    }
    return render(request, 'zpp04.html', context)

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

#------------------------------------------------------------------- ADMIN PANEL

def admin_controller(request):
    userList = getUserList()
    empNameList = []
    for user in userList:
        empNameList.append(getEmpIDByUserID(user.UserID))
    canMP = getManualReportAllow()
    context = {
        'userList': userList,
        'empNameList': empNameList,
        'canMP': canMP,
    }
    return render(request, 'admin_controller.html', context)

def error_data(request):
    oderNoRoutingList = getSAPOrderNoRoutingList()
    duplicateRoutingList = getSAPDuplicateRoutingList()
    orderNotStartList = getOrderNotStartList()
    workCenterErrorList = getWorkCenterErrorList()
    context = {
        'oderNoRoutingList': oderNoRoutingList,
        'duplicateRoutingList': duplicateRoutingList,
        'orderNotStartList': orderNotStartList,
        'workCenterErrorList': workCenterErrorList,
    }
    return render(request, 'error_data.html', context)

################################################################################
#################################### REQUEST ###################################
################################################################################

def fp_emp_search(request):
    operator_id = request.GET.get('operator_id')
    path = ""
    operator = getOperator(operator_id)
    if emp != None:
        if isOperatorOperating(operator_id):
            oopr = getOperatorOperatingByEmpID(operator_id)
            path = str(oopr.OperatorOrderNo) + "" + str(oopr.OperatorOperationNo)
    data = {
        'path': path,
    }
    return JsonResponse(data)

#-------------------------------------------------------------------- MAIN TABLE

def get_operating_workcenter_list(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    OWCList = [list(i) for i in getOperatingWorkCenterListForTable(order_no, operation_no)]
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
    OOPRList = [list(i) for i in getOperatingOperatorListForTable(order_no, operation_no)]
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
        elif workcenter.IsActive == False:
            invalid_text = WorkCenterNo + " is In-Active."
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
        #-- WORKCENTER : SAVE SETUP TIME
        oopr = getOperatorOperatingByID(id)
        updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
        #-- SAP : SETUP TIME
        oopr = getOperatorOperatingByID(id)
        setuptime = int(((oopr.OperatorStopDateTime - oopr.OperatorStartDateTime).total_seconds())/60)
        #-- IF SETUP TIME IS LESS THAN 1 MIN DON'T SEND DATA TOP SAP
        if int(setuptime > 0):
            insertSFR2SAP_Report(oopr.WorkCenterNo,oopr.OrderNo,oopr.OperationNo,0,0,setuptime,0,0,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
        #-- OPERATOR : SETUP TIME LOG
        insertHistoryOperate(oopr.OrderNo,oopr.OperationNo, oopr.EmpID, oopr.WorkCenterNo, "SETUP", setuptime, 0, 0, oopr.OperatorStartDateTime, oopr.OperatorStopDateTime)
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
    #-- WORKCENTER : SAVE SETUP TIME
    oopr = getOperatorOperatingByID(id)
    updateOperatingWorkCenter(oopr.OperatingWorkCenterID, "COMPLETED")
    #-- SAP : SETUP TIME
    setuptime = int(((oopr.OperatorStopDateTime - oopr.OperatorStartDateTime).total_seconds())/60)
    #-- IF SETUP TIME IS LESS THAN 1 MIN DON'T SEND DATA TOP SAP
    if int(setuptime > 0):
        insertSFR2SAP_Report(oopr.WorkCenterNo,oopr.OrderNo,oopr.OperationNo,0,0,setuptime,0,0,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
    #-- OPERATOR : SETUP TIME LOG
    insertHistoryOperate(oopr.OrderNo,oopr.OperationNo, oopr.EmpID, oopr.WorkCenterNo, "SETUP", setuptime, 0, 0, oopr.OperatorStartDateTime, oopr.OperatorStopDateTime)
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
    type = "WORKING"
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
    if status == "EXT-WORK":
        worktimeOperator = 0
    #-- IF EXTERNAL PROCESS DONT SEND DATA TO SAP (COMFIRMATION WILL HAVE ALL THIS INFO)
    #-- IF WORK TIME IS LESS THAN 1 MIN DON'T SEND DATA TOP SAP
    if status != "EXT-WORK" and (int(worktimeMachine) > 0 or int(worktimeOperator) > 0):
        insertSFR2SAP_Report(workcenter,oopr.OperatorOrderNo,oopr.OperatorOperationNo,0,0,0,worktimeMachine,worktimeOperator,oopr.OperatorStartDateTime,oopr.OperatorStopDateTime,oopr.EmpID)
    #-- OPERATOR : OPERATING TIME LOG
    insertHistoryOperate(oopr.OperatorOrderNo,oopr.OperatorOperationNo, oopr.EmpID, workcenter, type, 0, worktimeMachine, worktimeOperator, oopr.OperatorStartDateTime, oopr.OperatorStopDateTime)
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
    worktimeMachine = int(((owc.StopDateTime - owc.StartDateTime).total_seconds())/60)
    #-- IF WORK TIME IS LESS THAN 1 MIN DON'T SEND DATA TOP SAP
    if int(worktimeMachine) > 0:
        insertSFR2SAP_Report(owc.WorkCenterNo,owc.OrderNo,owc.OperationNo,0,0,0,worktimeMachine,0,owc.StartDateTime,owc.StopDateTime,'9999')
    #-- WORKCENTER : OPERATING TIME LOG
    insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "WORKING", 0, worktimeMachine, 0, owc.StartDateTime, owc.StopDateTime)
    #-- CHECK REMAINING IS OPERATING
    IsOperating = isOperatingOperation(owc.OrderNo, owc.OperationNo)
    data = {
        'IsOperating' : IsOperating,
    }
    return JsonResponse(data)

#-----------------------------------------CONFIRM & MANUAL REPORT & FIX OVERTIME

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
    if reject_reason == "-1" or reject_qty == 0:
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
        if reject_reason == "SCRAP FROM PREVIOUS PROCESS":
            sap_reject_qty = 0
        #-- IN-CASE OF REJECT SPECIAL CASE BUT NO GOOD QTY
        if int(sap_reject_qty) == 0 and int(good_qty) == 0:
            a = 0
        else:
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
                if owc.Status == 'WORKING' and owc.MachineType.strip() == 'Auto':
                    #-- WORKCENTER : STOP
                    updateOperatingWorkCenter(owc.OperatingWorkCenterID, "COMPLETED")
                    #-- SAP : WORKING TIME
                    owc = getWorkCenterOperatingByID(owc.OperatingWorkCenterID)
                    worktimeMachine = str(int(((owc.StopDateTime - owc.StartDateTime).total_seconds())/60))
                    #-- IF WORK TIME IS LESS THAN 1 MIN DON'T SEND DATA TO SAP
                    if int(worktimeMachine) > 0:
                        insertSFR2SAP_Report(owc.WorkCenterNo,owc.OrderNo,owc.OperationNo,0,0,0,worktimeMachine,0,owc.StartDateTime,owc.StopDateTime,'9999')
                    #-- WORKCENTER : OPERATING TIME LOG
                    insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "WORKING",0,worktimeMachine,0, owc.StartDateTime, owc.StopDateTime)
            #-- CLEAR ALL CONTROL DATA
            deleteAllOperatingData(orderNo, operationNo)
            #-- STOP OPERATION
            updateOperationControl(orderNo, operationNo, 0, 0, "STOP")
            #-- IF LAST OPERATION IN ORDER or IF NO MORE REMAINING QTY IN ORDER
            hasNoMoreQty = True
            operationList = getOperationList(orderNo)
            for i in range(len(operationList)):
                tempRemainQty = operationList[i].ProcessQty - (operationList[i].AcceptedQty + operationList[i].RejectedQty)
                if tempRemainQty > 0:
                    hasNoMoreQty = False
                    break
            if isLastOperation(orderNo, operationNo) and hasNoMoreQty:
                #-- ORDER : STOP
                updateOrderControl(orderNo, "STOP")
    data = {
    }
    return JsonResponse(data)

def manual_report(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    emp_id = request.GET.get('emp_id')
    workcenter_no = request.GET.get('workcenter_no')
    labor_time = request.GET.get('labor_time')
    operate_time = request.GET.get('operate_time')
    setup_time = request.GET.get('setup_time')
    start_time = parser.parse(request.GET.get('start_time'))
    stop_time = parser.parse(request.GET.get('stop_time'))
    good_qty = request.GET.get('good_qty')
    reject_qty = request.GET.get('reject_qty')
    reject_reason = request.GET.get('reject_reason')
    other_reason = request.GET.get('other_reason')
    if reject_reason == "-1" or reject_qty == 0:
        reject_reason = ""
    elif reject_reason == "OTHER":
        reject_reason = other_reason
    #-- RECHECK QTY
    operation = getOperation(order_no, operation_no)
    remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
    if remainQty >= (int(good_qty) + int(reject_qty)):
        #-- IF NOT START OPERATION YET
        if hasNotStartOperation(order_no, operation_no):
            #-- OPERATION : START
            updateOperationControl(order_no, operation_no, 0, 0, "START")
            #-- IF NOT START ORDER YET
            if hasNotStartOrder(order_no):
                #-- ORDER : START
                updateOrderControl(order_no, "START")
        #-- SPECIAL CASE **
        sap_reject_qty = reject_qty
        if reject_reason == "SCRAP FROM PREVIOUS PROCESS":
            sap_reject_qty = 0
        #-- IN-CASE OF REJECT SPECIAL CASE BUT NO GOOD QTY OR TIME
        if int(sap_reject_qty) == 0 and int(good_qty) == 0 and int(setup_time) == 0 and int(operate_time) == 0 and int(labor_time) == 0:
            a = 0
        else:
            # SAP : CONFIRM TIME & QTY
            insertSFR2SAP_Report(workcenter_no,order_no,operation_no,good_qty,sap_reject_qty,setup_time,operate_time,labor_time,start_time,stop_time,emp_id)
        #-- MANUAL REPORT : LOG
        insertHistoryOperate(order_no, operation_no, emp_id, workcenter_no, "MANUAL", setup_time, operate_time, labor_time, start_time, stop_time)
        #-- CONFIRM : LOG
        if int(good_qty) > 0 or int(reject_qty) > 0:
            insertHistoryConfirm(order_no, operation_no, emp_id, workcenter_no, good_qty, reject_qty, reject_reason)
            #-- UPDATE QTY OF CURRENT OPERATION
            updateOperationControl(order_no, operation_no, good_qty, reject_qty, "UPDATEQTY")
            #-- UPDATE PROCESS QTY OF NEXT OPERATION
            nextOperation = getNextOperation(order_no, operation_no)
            if nextOperation != None:
                updateOperationControl(nextOperation.OrderNo,nextOperation.OperationNo, good_qty, 0, "PROCESSQTY")
            #-- NO MORE REMAINING QTY
            operation = getOperation(order_no, operation_no)
            remainQty = operation.ProcessQty - (operation.AcceptedQty + operation.RejectedQty)
            if remainQty == 0:
                #-- IF AUTO MACHINE(S) STILL WORKING
                owcList = getOperatingWorkCenterList(order_no, operation_no)
                for owc in owcList:
                    if owc.Status == 'WORKING':
                        #-- WORKCENTER : STOP
                        updateOperatingWorkCenter(owc.OperatingWorkCenterID, "COMPLETED")
                        #-- SAP : WORKING TIME
                        owc = getWorkCenterOperatingByID(owc.OperatingWorkCenterID)
                        worktimeMachine = str(int(((owc.StopDateTime - owc.StartDateTime).total_seconds())/60))
                        #-- IF WORK TIME IS LESS THAN 1 MIN DON'T SEND DATA TOP SAP
                        if int(worktimeMachine) > 0:
                            insertSFR2SAP_Report(owc.WorkCenterNo,owc.OrderNo,owc.OperationNo,0,0,0,worktimeMachine,0,owc.StartDateTime,owc.StopDateTime,'9999')
                        #-- WORKCENTER : OPERATING TIME LOG
                        insertHistoryOperate(owc.OrderNo,owc.OperationNo, "NULL", owc.WorkCenterNo, "WORKING",0,worktimeMachine,0, owc.StartDateTime, owc.StopDateTime)
                #-- CLEAR ALL CONTROL DATA
                deleteAllOperatingData(order_no, operation_no)
                #-- STOP OPERATION
                updateOperationControl(order_no, operation_no, 0, 0, "STOP")
                #-- IF LAST OPERATION IN ORDER or IF NO MORE REMAINING QTY IN ORDER
                hasNoMoreQty = True
                operationList = getOperationList(order_no)
                for i in range(len(operationList)):
                    tempRemainQty = operationList[i].ProcessQty - (operationList[i].AcceptedQty + operationList[i].RejectedQty)
                    if tempRemainQty > 0:
                        hasNoMoreQty = False
                        break
                if isLastOperation(order_no, operation_no) and hasNoMoreQty:
                    #-- ORDER : STOP
                    updateOrderControl(order_no, "STOP")
    data = {
    }
    return JsonResponse(data)

def fix_overtime(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    operation = getOperation(order_no, operation_no)
    operatingOperatorList = getOperatingOperatorList(order_no, operation_no)
    for oopr in operatingOperatorList:
        if isOvertimeOperator(oopr.OperatingOperatorID):
            insertOvertimeOperator(oopr)
    if operation.WorkCenterType.strip() == 'Machine' and operation.MachineType.strip() == 'Auto':
        operatingWorkCenterList = getOperatingWorkCenterList(order_no, operation_no)
        for owc in operatingWorkCenterList:
            #-- ONLY WORKING WORKCENTER
            if isOvertimeWorkCenter(owc.OperatingWorkCenterID):
                insertOvertimeWorkCenter(owc)
    #-- DELETE ALL OPERATING DATA
    deleteAllOperatingData(order_no, operation_no)
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

def inc_qty(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    emp_id = request.GET.get('emp_id')
    password = request.GET.get('password')
    amount = request.GET.get('amount')
    operation = getOperation(order_no, operation_no)
    #-- INCREASE QTY OF 1st OPERATION & ORDER
    increaseQty(order_no, operation_no, amount)
    #-- HISTORY : INCREASE QTY
    user = getUserByPassword(password)
    insertHistoryModifier("INC QTY", order_no, operation_no, emp_id, user.UserID)
    data = {
    }
    return JsonResponse(data)

def dec_qty(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    emp_id = request.GET.get('emp_id')
    password = request.GET.get('password')
    amount = request.GET.get('amount')
    operation = getOperation(order_no, operation_no)
    #-- DECREASE QTY OF 1st OPERATION & ORDER
    decreaseQty(order_no, operation_no, amount)
    #-- HISTORY : DECREASE QTY
    user = getUserByPassword(password)
    insertHistoryModifier("DEC QTY", order_no, operation_no, emp_id, user.UserID)
    data = {
    }
    return JsonResponse(data)

def delete_operation(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    emp_id = request.GET.get('emp_id')
    password = request.GET.get('password')
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
        updateOrderControl(operation_no, "STOP")
    #-- SAP MODIFIER : DELETE OPERATION
    insertSFR2SAP_Modifier_Delete(order_no, operation_no)
    #-- HISTORY : DELETE OPERATION
    user = getUserByPassword(password)
    insertHistoryModifier("DELETE", order_no, operation_no, emp_id, user.UserID)
    #-- DELETE THIS OPERATION
    deleteOperationControl(order_no, operation_no)
    data = {
        'nextlink' : nextlink,
    }
    return JsonResponse(data)

def add_operation(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('new_operation_no')
    emp_id = request.GET.get('emp_id')
    work_center_no = request.GET.get('work_center_no')
    plan_start_date = request.GET.get('plan_start_date')
    plan_finish_date = request.GET.get('plan_finish_date')
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
    password = request.GET.get('password')
    #-- ADD OPERATION CONTROL
    if control_key == "PP01":
        insertOperationControl(order_no, operation_no, work_center_no, plan_start_date, plan_finish_date, est_setup_time, est_operate_time, est_labor_time)
    else:
        insertOperationControl(order_no, operation_no, work_center_no, plan_start_date, plan_finish_date, 0, 0, 0)
    #-- SAP : ADD OPERATION
    insertSFR2SAP_Modifier_Add(order_no, operation_no, control_key, work_center_no, pdt, cost_element, price_unit, price, currency, mat_group, purchasing_group, purchasing_org, est_setup_time, est_operate_time, est_labor_time)
    #-- HISTORY : ADD OPERATION
    user = getUserByPassword(password)
    insertHistoryModifier("ADD", order_no, operation_no, emp_id, user.UserID)
    #-- IF NEXT OPERATION HAS PROCESS QTY TRANSFER TO NEW OPERATION
    nextOperation = getNextOperation(order_no, operation_no)
    if nextOperation != None:
        updateOperationControl(order_no, operation_no, nextOperation.ProcessQty, 0, "PROCESSQTY")
        updateOperationControl(order_no,nextOperation.OperationNo, (nextOperation.ProcessQty * -1), 0, "PROCESSQTY")
    data = {
    }
    return JsonResponse(data)

def change_operation(request):
    order_no = request.GET.get('order_no')
    operation_no = request.GET.get('operation_no')
    emp_id = request.GET.get('emp_id')
    work_center_no = request.GET.get('work_center_no')
    plan_start_date = request.GET.get('plan_start_date')
    plan_finish_date = request.GET.get('plan_finish_date')
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
    password = request.GET.get('password')
    #-- CLEAR DATA MIGHT LEFT (LIKE WAITING WORKCENTER)
    deleteAllOperatingData(order_no, operation_no)
    #-- SAP REQUIRED TO SEND ONLY 1 CHANGE OF THE SAME OPERATION PER HOURLY FILE
    deleteSFR2SAP_Modifier_Change(order_no, operation_no)
    #-- CHANGE OPERATION CONTROL
    if control_key == "PP01":
        changeOperationControl(order_no, operation_no, work_center_no, plan_start_date, plan_finish_date, est_setup_time, est_operate_time, est_labor_time)
    else:
        changeOperationControl(order_no, operation_no, work_center_no, plan_start_date, plan_finish_date, 0, 0, 0)
    #-- SAP : CHANGE OPERATION
    insertSFR2SAP_Modifier_Change(order_no, operation_no, control_key, work_center_no, pdt, cost_element, price_unit, price, currency, mat_group, purchasing_group, purchasing_org, est_setup_time, est_operate_time, est_labor_time)
    #-- HISTORY : CHANGE OPERATION
    user = getUserByPassword(password)
    insertHistoryModifier("CHANGE", order_no, operation_no, emp_id, user.UserID)
    data = {
    }
    return JsonResponse(data)

#-------------------------------------------------------------------------- NOTE

def save_note(request):
    order_no = request.GET.get('order_no')
    order_note = request.GET.get('order_note')
    operation_note_list = request.GET.getlist('operation_note_list[]')
    operationList = getOperationList(order_no)
    updateOrderNote(order_no, order_note)
    for i in range(len(operationList)):
        updateOperationNote(order_no, operationList[i].OperationNo, operation_note_list[i])
    data = {
    }
    return JsonResponse(data)

#-------------------------------------------------------------------- VALIDATION
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
    invalidText = ""
    isExt = False
    work_center = getWorkCenter(work_center_no)
    if work_center == None:
        canUse = False
        invalidText = "Routing not found."
    elif work_center.IsRouting == False:
        canUse = False
        invalidText = "This Work Center is not a routing."
    else:
        isExt = work_center.IsExternalProcess
    data = {
        'canUse': canUse,
        'invalidText': invalidText,
        'isExt': isExt,
    }
    return JsonResponse(data)

def validate_work_center(request):
    work_center_no = request.GET.get('work_center_no')
    work_center_group = request.GET.get('work_center_group')
    canUse = True
    invalidText = ''
    work_center = getWorkCenter(work_center_no)
    if work_center == None:
        canUse = False
        invalidText = 'Work Center Not Found.'
    elif work_center.IsRouting:
        canUse = False
        invalidText = 'Routing can not be used.'
    elif work_center.WorkCenterGroup != work_center_group:
        canUse = False
        invalidText = 'This Work Center is not in the same Work Center Group.'
    elif work_center.IsActive == False:
        canUse = False
        invalidText = 'This Work Center is In-Active.'
    data = {
        'canUse': canUse,
        'invalidText': invalidText,
    }
    return JsonResponse(data)

def validate_operator(request):
    emp_id = request.GET.get('emp_id')
    isExist = isExistOperator(emp_id)
    data = {
        'isExist': isExist,
    }
    return JsonResponse(data)

def validate_password(request):
    password = request.GET.get('password')
    isCorrect = False
    user = getUserByPassword(password)
    if user != None:
        isCorrect = True
    data = {
        'isCorrect': isCorrect,
    }
    return JsonResponse(data)

def validate_section_chief_password(request):
    password = request.GET.get('password')
    isCorrect = False
    user = getUserByPassword(password)
    if user != None and (user.UserRole.strip() == 'CHIEF' or user.UserRole.strip() == 'ADMIN' or user.UserRole.strip() == 'SUPERADMIN'):
        isCorrect = True
    data = {
        'isCorrect': isCorrect,
    }
    return JsonResponse(data)

def validate_admin_password(request):
    password = request.GET.get('password')
    isCorrect = False
    user = getUserByPassword(password)
    if user != None and (user.UserRole.strip() == 'ADMIN' or user.UserRole.strip() == 'SUPERADMIN'):
        isCorrect = True
    data = {
        'isCorrect': isCorrect,
    }
    return JsonResponse(data)

def validate_super_admin_password(request):
    password = request.GET.get('password')
    isCorrect = False
    user = getUserByPassword(password)
    if user != None and user.UserRole.strip() == 'SUPERADMIN':
        isCorrect = True
    data = {
        'isCorrect': isCorrect,
    }
    return JsonResponse(data)

def validate_new_user_id(request):
    user_id = request.GET.get('user_id')
    canUse = False
    user = getUserByUserID(user_id)
    if user == None:
        canUse = True
    data = {
        'canUse': canUse,
    }
    return JsonResponse(data)

def validate_new_password(request):
    password = request.GET.get('password')
    canUse = False
    user = getUserByPassword(password)
    if user == None:
        canUse = True
    data = {
        'canUse': canUse,
    }
    return JsonResponse(data)

#------------------------------------------------------------------- ADMIN PANEL
def add_new_user(request):
    user_id = request.GET.get('user_id')
    user_password = request.GET.get('user_password')
    user_role = request.GET.get('user_role')
    insertUser(user_id, user_password, user_role)
    data = {
    }
    return JsonResponse(data)

def delete_user(request):
    user_id = request.GET.get('user_id')
    deleteUser(user_id)
    data = {
    }
    return JsonResponse(data)

def change_user_password(request):
    user_id = request.GET.get('user_id')
    user_password = request.GET.get('user_password')
    changeUserPassword(user_id, user_password)
    data = {
    }
    return JsonResponse(data)

def mpa(request):
    status = request.GET.get('status')
    updateManualReportAllowdance(status)
    data = {
    }
    return JsonResponse(data)

def reset_order(request):
    order_no = request.GET.get('order_no')
    start_operation_no = request.GET.get('start_operation_no')
    conn = get_connection()
    cursor = conn.cursor()
    sql = " DELETE FROM OperatingOperator WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM OperatingWorkCenter WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM HistoryConfirm WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM HistoryOperate WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM HistoryJoin WHERE JoinToOrderNo = "+order_no+" "
    sql += " DELETE FROM HistoryJoin WHERE JoinByOrderNo = "+order_no+" "
    sql += " DELETE FROM HistoryModifier WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM OvertimeOperator WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM OvertimeWorkCenter WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM OrderControl WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM OperationControl WHERE OrderNo = "+order_no+" "
    sql += " DELETE FROM PartialLotTraveller WHERE OrderNo = "+order_no+" "
    # sql += " DELETE FROM SFR2SAP_Report WHERE ProductionOrderNo = "+order_no+" "
    sql += " DELETE SAP_Routing WHERE ProductionOrderNo = '"+order_no+"' AND OperationNumber < " + str(start_operation_no)
    cursor.execute(sql)
    conn.commit()
    data = {
    }
    return JsonResponse(data)

def reset_all(request):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
            DELETE FROM SAP_Order
            DELETE FROM SAP_Routing
            DELETE FROM OperatingOperator
            DELETE FROM OperatingWorkCenter
            DELETE FROM SFR2SAP_Report
            DELETE FROM SFR2SAP_Modifier
            DELETE FROM HistoryConfirm
            DELETE FROM HistoryOperate
            DELETE FROM HistoryJoin
            DELETE FROM HistoryModifier
            DELETE FROM OvertimeOperator
            DELETE FROM OvertimeWorkCenter
            DELETE FROM OrderControl
            DELETE FROM OperationControl
            DELETE FROM PartialLotTraveller
            """
    cursor.execute(sql)
    conn.commit()
    data = {
    }
    return JsonResponse(data)

#--------------------------------------------------------------------------- ETC

def increase_lot_no(request):
    order_no = request.GET.get('order_no')
    start_operation_no = request.GET.get('start_operation_no')
    final_lot_no = request.GET.get('final_lot_no')
    lot_qty = request.GET.get('lot_qty')
    type = request.GET.get('type')
    password = request.GET.get('password')
    lot_no = int(final_lot_no) + 1
    chief_id = getUserByPassword(password).UserID
    updateOrderLotNo(order_no)
    insertPLT(order_no, start_operation_no, lot_no, lot_qty, type, chief_id)
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
    sql = """
            SELECT EMP.EmpID, EMP.EmpName, EMP.Section, EMP.IsActive, MAX(StartDateTime) AS LastStartWorkingTime FROM Employee AS EMP
            LEFT JOIN HistoryOperate AS HO ON EMP.EmpID = HO.EmpID
            GROUP BY EMP.EmpId, EMP.EmpName, EMP.Section, EMP.IsActive
        """
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
    sql = "SELECT * FROM [OperationControl] as OC"
    sql += " LEFT JOIN [WorkCenter] as WC ON OC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OrderNo = '" + order_no + "' ORDER BY OperationNo ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getModList(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryModifier] WHERE OrderNo = '" + order_no + "' ORDER BY ModifyDateTime DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getOverTimeOperatorList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OvertimeOperator] WHERE OrderNo = '"+order_no+"' AND OperationNo = '"+operation_no+"' ORDER BY DateTimeStamp DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getOverTimeWorkCenterList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OvertimeWorkCenter] WHERE OrderNo = '"+order_no+"' AND OperationNo = '"+operation_no+"' ORDER BY DateTimeStamp DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getUserList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [User]"
    cursor.execute(sql)
    return cursor.fetchall()

def getWorkingOrderList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OrderControl] WHERE ProcessStart IS NOT NULL AND ProcessStop IS NULL"
    cursor.execute(sql)
    return cursor.fetchall()

def getWorkingWorkCenterList():
    cursor = get_connection().cursor()
    sql = "SELECT OWC.WorkCenterNo AS WCN, * FROM [OperatingWorkCenter] as OWC INNER JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " INNER JOIN [OperationControl] as OC ON OC.OrderNo = OWC.OrderNo AND OC.OperationNo = OWC.OperationNo"
    sql += " INNER JOIN [OrderControl] as ORDC ON OWC.OrderNo = ORDC.OrderNo"
    sql += " WHERE Status <> 'COMPLETED' ORDER BY OWC.OperatingWorkCenterID ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getWorkingOperatorList():
    cursor = get_connection().cursor()
    sql = "SELECT OOPR.EmpID, EMP.EmpName, EMP.Section, OOPR.Status, OOPR.OrderNo, OOPR.OperationNo, OOPR.StartDateTime, OWC.WorkCenterNo, OC.Note, ORDC.FG_MaterialCode "
    sql += " FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " INNER JOIN [OperationControl] as OC ON OC.OrderNo = OOPR.OrderNo AND OC.OperationNo = OOPR.OperationNo"
    sql += " INNER JOIN [OrderControl] as ORDC ON OOPR.OrderNo = ORDC.OrderNo"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.Status <> 'COMPLETED' ORDER BY OOPR.OperatingOperatorID ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperatingWorkCenterList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingWorkCenter] as OWC INNER JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' ORDER BY OWC.OperatingWorkCenterID ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperatingWorkCenterListForTable(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT OWC.OperatingWorkCenterID, OWC.WorkCenterNo, WC.WorkCenterName, OWC.StartDateTime, OWC.StopDateTime, OWC.Status, WC.MachineType, *"
    sql += " FROM [OperatingWorkCenter] as OWC INNER JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' ORDER BY OWC.OperatingWorkCenterID DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperatingOperatorList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT OOPR.OperatingOperatorID, OOPR.OrderNo, OOPR.OperationNo, OOPR.EmpID, OOPR.StartDateTime, OOPR.StopDateTime, OOPR.Status, OOPR.OperatingWorkCenterID, OWC.WorkCenterNo"
    sql += " FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.OrderNo = '" + order_no + "' AND OOPR.OperationNo = '" + operation_no + "' ORDER BY OOPR.OperatingOperatorID ASC"
    cursor.execute(sql)
    return cursor.fetchall()

def getOperatingOperatorListForTable(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT OOPR.OperatingOperatorID, WC.WorkCenterNo, WC.WorkCenterName, OOPR.EmpID, EMP.EmpName, OOPR.StartDateTime, OOPR.StopDateTime, OOPR.Status,*"
    sql += " FROM [OperatingOperator] as OOPR INNER JOIN [Employee] as EMP ON OOPR.EmpID = EMP.EmpID"
    sql += " LEFT JOIN [OperatingWorkCenter] as OWC ON OOPR.OperatingWorkCenterID = OWC.OperatingWorkCenterID"
    sql += " LEFT JOIN [WorkCenter] as WC ON OWC.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OOPR.OrderNo = '" + order_no + "' AND OOPR.OperationNo = '" + operation_no + "' ORDER BY OOPR.OperatingOperatorID DESC"
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
    sql = "SELECT * FROM [HistoryOperate] AS HO"
    sql += " INNER JOIN WorkCenter AS WC ON HO.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE OrderNo = '"+order_no+"' AND OperationNo = '"+operation_no+"' ORDER BY StopDateTime DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getHistoryConfirmList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryConfirm] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' ORDER BY ConfirmDateTime DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getHistoryJoinList(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryJoin] "
    sql += " WHERE (JoinToOrderNo = '" + order_no + "' AND JoinToOperationNo = '" + operation_no + "')"
    sql += " OR (JoinByOrderNo = '" + order_no + "' AND JoinByOperationNo = '" + operation_no + "')"
    cursor.execute(sql)
    return cursor.fetchall()

def getWorkCenterHistoryTransactionList(work_center_no, month, year):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryOperate] WHERE WorkCenterNo = '"+work_center_no+"' AND month(StartDateTime) = '"+month+"' AND year(StartDateTime) = '"+year+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getWorkCenterHistoryOvertimeList(work_center_no, month, year):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OvertimeWorkCenter] WHERE WorkCenterNo = '"+work_center_no+"' AND month(StartDateTime) = '"+month+"' AND year(StartDateTime) = '"+year+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getOvertimeWorkCenterList(month, year):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OvertimeWorkCenter] WHERE month(StartDateTime) = '"+month+"' AND year(StartDateTime) = '"+year+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getEmployeeHistoryTransactionList(emp_id, month, year):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryOperate] AS HO"
    sql += " INNER JOIN WorkCenter AS WC ON HO.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE EmpID = '"+emp_id+"'AND month(StartDateTime) = '"+month+"' AND year(StartDateTime) = '"+year+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getEmployeeHistoryConfirmList(emp_id, month, year):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryConfirm] WHERE EmpID = '"+emp_id+"' AND month(ConfirmDateTime) = '"+month+"' AND year(ConfirmDateTime) = '"+year+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getEmployeeHistoryOvertimeList(emp_id, month, year):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OvertimeOperator] WHERE EmpID = '"+emp_id+"' AND month(StartDateTime) = '"+month+"' AND year(StartDateTime) = '"+year+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getOvertimeOperatorList(month, year):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OvertimeOperator] WHERE month(StartDateTime) = '"+month+"' AND year(StartDateTime) = '"+year+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getPTLList(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [PartialLotTraveller] WHERE OrderNo = '" + order_no + "' ORDER BY LotNo DESC"
    cursor.execute(sql)
    return cursor.fetchall()

def getSAPOrderNoRoutingList():
    cursor = get_connection().cursor()
    sql = "SELECT OD.ProductionOrderNo, OD.DateGetFromSAP"
    sql += " From SAP_Order AS OD LEFT JOIN SAP_Routing AS RT ON OD.ProductionOrderNo = RT.ProductionOrderNo WHERE RT.ProductionOrderNo IS NULL"
    cursor.execute(sql)
    return cursor.fetchall()

def getSAPDuplicateRoutingList():
    cursor = get_connection().cursor()
    sql = """
            SELECT RT1.ProductionOrderNo, RT1.OperationNumber, RT1.DateGetFromSAP AS RT1DateGetFromSAP, RT2.DateGetFromSAP AS RT2DateGetFromSAP
            FROM SAP_Routing AS RT1 INNER JOIN SAP_Routing AS RT2 ON RT1.ProductionOrderNo = RT2.ProductionOrderNo AND RT1.OperationNumber = RT2.OperationNumber
            WHERE RT1.DateGetFromSAP < RT2.DateGetFromSAP
        """
    cursor.execute(sql)
    return cursor.fetchall()

def getOrderNotStartList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM OrderControl WHERE ProcessStart IS NULL"
    cursor.execute(sql)
    return cursor.fetchall()

def getWorkCenterErrorList():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM SAP_Routing AS RT LEFT JOIN WorkCenter AS WC ON RT.WorkCenter = WC.WorkCenterNo WHERE WC.WorkCenterNo IS NULL"
    cursor.execute(sql)
    return cursor.fetchall()

def getWorkCenterInGroupList(work_center_group):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM WorkCenter WHERE IsRouting = 0 AND WorkCenterGroup = '"+work_center_group+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getAutoMachineManualReportOvertimeList(month, year):
    cursor = get_connection().cursor()
    sql = "SELECT DateTimeStamp, HO.OrderNo, HO.OperationNo, EmpID, HO.WorkCenterNo, Setup, Oper, Labor"
    sql += " FROM HistoryOperate AS HO "
    sql += " INNER JOIN OvertimeWorkCenter AS OTWC ON HO.OrderNo = OTWC.OrderNo AND HO.OperationNo = OTWC.OperationNo "
    sql += " INNER JOIN WorkCenter AS WC ON HO.WorkCenterNo = WC.WorkCenterNo "
    sql += " WHERE Type = 'MANUAL' AND WC.MachineType = 'Auto' AND (Setup != 0 OR Oper != 0 OR Labor != 0) "
    sql += " AND month(DateTimeStamp) = '"+month+"' AND year(DateTimeStamp) = '"+year+"'"
    cursor.execute(sql)
    return cursor.fetchall()

def getEmpWorkRecordsList(month, year):
    cursor = get_connection().cursor()
    sql = "SELECT HO.EmpID, EMP.EmpName, EMP.Section, SUM(Setup) AS Setup, SUM(Labor) AS Labor"
    sql += " FROM HistoryOperate AS HO INNER JOIN Employee AS EMP ON HO.EmpID = EMP.EmpID"
    sql += " WHERE month(StartDateTime) = '"+month+"' AND year(StartDateTime) = '"+year+"'"
    sql += " GROUP BY HO.EmpID, EMP.EmpName, EMP.Section"
    cursor.execute(sql)
    return cursor.fetchall()

def getWorkCenterWorkRecordsList(month, year):
    cursor = get_connection().cursor()
    sql = "SELECT WorkCenterGroup, WC.WorkCenterNo, WorkCenterName, SUM(Setup) AS Setup, SUM(Oper) AS Oper"
    sql += " FROM HistoryOperate AS HO INNER JOIN WorkCenter AS WC ON HO.WorkCenterNo = WC.WorkCenterNo"
    sql += " WHERE month(StartDateTime) = '"+month+"' AND year(StartDateTime) = '"+year+"'"
    sql += " GROUP BY WC.WorkCenterGroup, WC.WorkCenterNo, WC.WorkCenterName"
    cursor.execute(sql)
    return cursor.fetchall()

#-------------------------------------------------------------------------- ITEM
def getOrder(order_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OrderControl] WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    return cursor.fetchone()

def getOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] as OPT"
    sql += " LEFT JOIN [WorkCenter] as WC ON OPT.WorkCenterNo = WC.WorkCenterNo"
    # sql += " LEFT JOIN [SAP_Routing] as SAPRT ON OPT.OrderNo = SAPRT.ProductionOrderNo AND OPT.OperationNo = SAPRT.OperationNumber"
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

def getUserByPassword(password):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [dbo].[User] WHERE PasswordHash = HASHBYTES('SHA2_512', '"+ password + "')"
    cursor.execute(sql)
    return cursor.fetchone()

def getUserByUserID(user_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [dbo].[User] WHERE UserID = '"+ user_id + "'"
    cursor.execute(sql)
    return cursor.fetchone()

def getPTL(order_no, lot_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [PartialLotTraveller] WHERE OrderNo = '" + order_no + "' AND LotNo = " + lot_no
    cursor.execute(sql)
    return cursor.fetchone()

def getEmpIDByUserID(user_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [dbo].[Employee] WHERE EmpID = '"+ user_id + "'"
    cursor.execute(sql)
    return cursor.fetchone()

def getOvertimeHour():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [dbo].[AdminConfig] WHERE KeyText = 'OVERTIME_HOUR'"
    cursor.execute(sql)
    return int((cursor.fetchone()).Value)

def getManualReportAllow():
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [AdminConfig] WHERE KeyText = 'MANUAL_REPORT_ALLOWDANCE'"
    cursor.execute(sql)
    return (cursor.fetchone().Value)

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

def isFirstOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE OrderNo = '" + order_no + "' ORDER BY OperationNo ASC"
    cursor.execute(sql)
    result = cursor.fetchall()
    return (result[0].OperationNo.strip() == operation_no)

def isLastOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperationControl] WHERE OrderNo = '" + order_no + "' ORDER BY OperationNo DESC"
    cursor.execute(sql)
    result = cursor.fetchall()
    return (result[0].OperationNo.strip() == operation_no)

def isExistDeletedOperation(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [HistoryModifier] WHERE Type = 'DELETE' AND OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def isOvertimeOperation(order_no, operation_no):
    ot = str(getOvertimeHour())
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingOperator] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' AND (Status = 'WORKING' OR Status = 'SETUP') AND (DATEADD(HOUR, "+ot+", StartDateTime) < CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    if len(cursor.fetchall()) > 0:
        return True
    else:
        cursor = get_connection().cursor()
        sql = "SELECT * FROM [OperatingWorkCenter] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' AND (Status = 'WORKING' OR Status = 'SETUP') AND (DATEADD(HOUR, "+ot+", StartDateTime) < CURRENT_TIMESTAMP)"
        cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def isOvertimeOperator(oopr_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingOperator] WHERE OperatingOperatorID = '"+str(oopr_id)+"' AND (Status = 'WORKING' OR Status = 'SETUP') AND (DATEADD(HOUR, 12, StartDateTime) < CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

#-- ONLY WORKING WORKCENTER
def isOvertimeWorkCenter(owc_id):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [OperatingWorkCenter] WHERE OperatingWorkCenterID = '"+str(owc_id)+"' AND Status = 'WORKING' AND (DATEADD(HOUR, 12, StartDateTime) < CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    return (len(cursor.fetchall()) > 0)

def hasReportTimeToSAP(order_no, operation_no):
    cursor = get_connection().cursor()
    sql = "SELECT * FROM [SFR2SAP_Report] WHERE ProductionOrderNo = '"+order_no+"' AND OperationNumber = '"+operation_no+"' AND LaborTime > 0"
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
    sql = "SELECT * FROM [SAP_Order] WHERE ProductionOrderNo = '" + order_no + "'"
    cursor.execute(sql)
    order = cursor.fetchone()
    SalesOrderNo = ""
    RequestDate = ""
    ReleaseDate = ""
    DateGetFromSAP = order.DateGetFromSAP.strftime("%Y-%m-%d %H:%M:%S")
    if order.SalesCreateDate == "00.00.0000":
        SalesOrderNo = "NULL"
    else:
        SalesOrderNo = "CONVERT(DATETIME,'"+order.SalesCreateDate+"',104)"
    if order.RequestDate == "00.00.0000":
        RequestDate = "NULL"
    else:
        RequestDate = "CONVERT(DATETIME,'"+order.RequestDate+"',104)"
    if order.ReleaseDate == "00.00.0000":
        ReleaseDate = "NULL"
    else:
        ReleaseDate = "CONVERT(DATETIME,'"+order.ReleaseDate+"',104)"
    cursor = conn.cursor()
    sql = "INSERT INTO [OrderControl] ([OrderNo],[LotNo],[CustomerPONo],[PartNo],[PartName],[SalesOrderNo],[SalesCreateDate],[SalesOrderQuantity],[ProductionOrderQuatity],[FG_MaterialCode],[RM_MaterialCode],[MRP_Controller],[RequestDate],[ReleaseDate],[DrawingNo],[AeroSpace],[RoutingGroup],[RoutingGroupCounter],[Plant],[DateGetFromSAP]) VALUES "
    sql += "('"+order_no+"',0,'"+order.CustomerPONo+"','"+order.PartNo+"','"+order.PartName.replace("'", " ")+"','"+order.SalesOrderNo+"',"
    sql += SalesOrderNo+","+str(order.SalesOrderQuantity)+","+str(order.ProductionOrderQuatity)+",'"+order.FG_MaterialCode+"','"+order.RM_MaterialCode+"',"
    sql += "'"+order.MRP_Controller+"',"+RequestDate+","+ReleaseDate+",'"+order.DrawingNo+"','"+order.AeroSpace+"',"
    sql += "'"+order.RoutingGroup+"','"+order.RoutingGroupCounter+"','"+order.Plant+"','"+DateGetFromSAP+"')"
    cursor.execute(sql)
    conn.commit()
    return

def setOperationControlFromSAP(order_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM [SAP_Order] WHERE ProductionOrderNo = '" + order_no + "'"
    cursor.execute(sql)
    order = cursor.fetchone()
    sql = "SELECT * FROM [SAP_Routing] WHERE ProductionOrderNo = '" + order_no + "' ORDER BY OperationNumber ASC"
    cursor.execute(sql)
    operations = cursor.fetchall()
    for i in range(len(operations)):
        operationNo = frontZero(operations[i].OperationNumber.strip(), 4)
        #--
        date_get_from_sap = ""
        if operations[i].DateGetFromSAP != None:
            date_get_from_sap = str(operations[i].DateGetFromSAP)
        else:
            date_get_from_sap = str(datetime.now())
        date_get_from_sap = str(date_get_from_sap[0:19])
        #--
        sql = "INSERT INTO [OperationControl] ([OrderNo],[OperationNo],[WorkCenterNo],[ProcessQty],[AcceptedQty],[RejectedQty],[PlanStartDate],[PlanFinishDate],[EstSetupTime],[EstOperationTime],[EstLaborTime],[DateGetFromSAP])"
        if i == 0:
            sql += " VALUES ('"+order_no+"','"+operationNo+"','"+operations[i].WorkCenter+"',"+str(order.ProductionOrderQuatity)+",0,0,CONVERT(DATETIME, '"+str(operations[i].PlanStartDate)+"', 104),CONVERT(DATETIME, '"+str(operations[i].PlanFinishDate)+"', 104),"+str(operations[i].EstimateSetTime)+","+str(operations[i].EstimateOperationTime)+","+str(operations[i].EstimateLaborTime)+",'"+date_get_from_sap+"')"
        else:
            sql += " VALUES ('"+order_no+"','"+operationNo+"','"+operations[i].WorkCenter+"',0,0,0,CONVERT(DATETIME, '"+str(operations[i].PlanStartDate)+"', 104),CONVERT(DATETIME, '"+str(operations[i].PlanFinishDate)+"', 104),"+str(operations[i].EstimateSetTime)+","+str(operations[i].EstimateOperationTime)+","+str(operations[i].EstimateLaborTime)+",'"+date_get_from_sap+"')"
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
    DateTimeStamp = "CURRENT_TIMESTAMP"
    # if datetime.now().hour == 23:
    #     DateTimeStamp = "DATEADD(HOUR,1,CURRENT_TIMESTAMP)"
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
    DateTimeStamp = "CURRENT_TIMESTAMP"
    # if datetime.now().hour == 23:
    #     DateTimeStamp = "DATEADD(HOUR,1,CURRENT_TIMESTAMP)"
    conn = get_connection()
    cursor = conn.cursor()
    mode = ""
    sql = ""
    if control_key == "PP01":
        if int(est_setup_time) == 0:
            est_setup_time = 'NULL'
        if int(est_operate_time) == 0:
            est_operate_time = 'NULL'
        if int(est_labor_time) == 0:
            est_labor_time = 'NULL'
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

def insertSFR2SAP_Modifier_Change(order_no, operation_no, control_key, work_center_no, pdt, cost_element, price_unit, price, currency, mat_group, purchasing_group, purchasing_org, est_setup_time, est_operate_time, est_labor_time):
    conn = get_connection()
    cursor = conn.cursor()
    mode = ""
    sql = ""
    if control_key == "PP01":
        if int(est_setup_time) == 0:
            est_setup_time = 'NULL'
        if int(est_operate_time) == 0:
            est_operate_time = 'NULL'
        if int(est_labor_time) == 0:
            est_labor_time = 'NULL'
        mode = "21"
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
        mode = "22"
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

def insertOperationControl(order_no, operation_no, work_center_no, plan_start_date, plan_finish_date, est_setup_time, est_operate_time, est_labor_time):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OperationControl] ([OrderNo],[OperationNo],[WorkCenterNo],[ProcessQty],[AcceptedQty],[RejectedQty],[PlanStartDate],[PlanFinishDate],[EstSetupTime],[EstOperationTime],[EstLaborTime])"
    sql += " VALUES ('" + str(order_no) + "', '" + str(operation_no) + "', '" + str(work_center_no) + "', 0, 0, 0,'" + str(plan_start_date) + "','" + str(plan_finish_date) + "'," + str(est_setup_time) + "," + str(est_operate_time) + "," + str(est_labor_time) + ")"
    cursor.execute(sql)
    conn.commit()
    return

def insertHistoryOperate(order_no, operation_no, operator_id, workcenter_no, type, setup, oper, labor, start_date_time, stop_date_time):
    startDateTime = start_date_time.strftime("%Y-%m-%d %H:%M:%S")
    stopDateTime = stop_date_time.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [HistoryOperate] ([OrderNo],[OperationNo],[EmpID],[WorkCenterNo],[Type],[Setup],[Oper],[Labor],[StartDateTime],[StopDateTime])"
    sql += " VALUES ('" + order_no + "','" + operation_no + "'," + str(operator_id) + ",'" + workcenter_no + "','" + type + "'," + str(setup) + "," + str(oper) + "," + str(labor) + ",'" + startDateTime + "','" + stopDateTime + "')"
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

def insertHistoryModifier(type, order_no, operation_no, emp_id, chief_id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [dbo].[HistoryModifier] ([Type],[OrderNo],[OperationNo],[EmpID],[ChiefID],[ModifyDateTime])"
    sql += " VALUES ('" + str(type) + "','" + str(order_no) + "','" + str(operation_no) + "','" + str(emp_id) + "','" + str(chief_id) + "',CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    conn.commit()
    return

def insertUser(user_id, user_password, user_role):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO dbo.[User] (UserID, PasswordHash, UserRole) VALUES('"+user_id+"', HASHBYTES('SHA2_512', '"+user_password+"'), '"+user_role+"')"
    cursor.execute(sql)
    conn.commit()
    return

def insertPLT(order_no, operation_no, lot_no, lot_qty, type, chief_id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [dbo].[PartialLotTraveller] ([OrderNo],[StartOperationNo],[LotNo],[LotQty],[Type],[ChiefID],[StartDateTime]) VALUES "
    sql += " ('"+order_no+"','"+operation_no+"',"+str(lot_no)+","+str(lot_qty)+",'"+type+"','"+chief_id+"',CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    conn.commit()
    return

def insertOvertimeWorkCenter(owc):
    startDateTime = owc.StartDateTime.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OvertimeWorkCenter] ([DateTimeStamp],[OrderNo],[OperationNo],[WorkCenterNo],[StartDateTime])"
    sql += " VALUES (CURRENT_TIMESTAMP,'"+owc.OrderNo+"','"+owc.OperationNo+"','"+owc.WorkCenterNo+"','"+startDateTime+"')"
    cursor.execute(sql)
    conn.commit()
    return

def insertOvertimeOperator(oopr):
    startDateTime = oopr.StartDateTime.strftime("%Y-%m-%d %H:%M:%S")
    WorkCenter = oopr.WorkCenterNo
    if WorkCenter == None:
        WorkCenter = '-1'
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO [OvertimeOperator] ([DateTimeStamp],[OrderNo],[OperationNo],[EmpID],[WorkCenterNo],[Status],[StartDateTime])"
    sql += " VALUES (CURRENT_TIMESTAMP,'"+oopr.OrderNo+"','"+oopr.OperationNo+"','"+oopr.EmpID+"','"+WorkCenter+"','"+oopr.Status+"','"+startDateTime+"')"
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

def changeOperationControl(order_no, operation_no, work_center_no, plan_start_date, plan_finish_date, est_setup_time, est_operate_time, est_labor_time):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [OperationControl] SET WorkCenterNo = '"+ str(work_center_no) + "', PlanStartDate = '" + str(plan_start_date) + "', PlanFinishDate = '" + str(plan_finish_date) + "', EstSetupTime = '" + str(est_setup_time) + "', EstOperationTime = '" + str(est_operate_time) + "', EstLaborTime = '" + str(est_labor_time) + "' WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
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

def changeUserPassword(user_id, user_password):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [User] SET [PasswordHash] = HASHBYTES('SHA2_512', '"+user_password+"') WHERE UserID = '"+user_id+"'"
    cursor.execute(sql)
    conn.commit()
    return

def updateOrderLotNo(order_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [OrderControl] SET [LotNo] += 1 WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    conn.commit()
    return

def updateManualReportAllowdance(status):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [AdminConfig] SET [Value] = '"+status+"' WHERE KeyText = 'MANUAL_REPORT_ALLOWDANCE'"
    cursor.execute(sql)
    conn.commit()
    return

def increaseQty(order_no, operation_no, amount):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [OrderControl] SET [ProductionOrderQuatity] += '" + amount + "' WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    conn.commit()
    sql = "UPDATE [OperationControl] SET [ProcessQty] += '" + amount + "' WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    conn.commit()
    return

def decreaseQty(order_no, operation_no, amount):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [OrderControl] SET [ProductionOrderQuatity] -= '" + amount + "' WHERE OrderNo = '" + order_no + "'"
    cursor.execute(sql)
    conn.commit()
    sql = "UPDATE [OperationControl] SET [ProcessQty] -= '" + amount + "' WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "'"
    cursor.execute(sql)
    conn.commit()
    return

def updateOrderNote(order_no, note):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [OrderControl] SET [Note] = '"+note+"' WHERE OrderNo = '"+order_no+"'"
    cursor.execute(sql)
    conn.commit()
    return

def updateOperationNote(order_no, operation_no, note):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE [OperationControl] SET [Note] = '"+note+"' WHERE OrderNo = '"+order_no+"' AND OperationNo = '"+operation_no+"'"
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

def deleteSFR2SAP_Modifier_Change(order_no, operation_no):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM [SFR2SAP_Modifier] WHERE OrderNo = '" + order_no + "' AND OperationNo = '" + operation_no + "' AND (Mode = 22 OR Mode = 21) AND CAST(DateTimeStamp AS DATE) = CAST(CURRENT_TIMESTAMP AS DATE) AND DATEPART(HOUR, DateTimeStamp) = DATEPART(HOUR, CURRENT_TIMESTAMP)"
    cursor.execute(sql)
    conn.commit()
    return

def deleteUser(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM [User] WHERE UserID = '"+user_id+"'"
    cursor.execute(sql)
    conn.commit()
    return

################################################################################
################################################################################
################################################################################

def getClientIP(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def printString(str):
    print("################################################################################")
    print(str)
    print("################################################################################")
    return

def frontZero(str, length):
    result = str
    for i in range(length - len(str)):
        result = "0" + result
    return result

# def replace_rm_mat_code():
#     wb = load_workbook(filename = 'media/Material Bom.xlsx')
#     ws = wb.active
#     skip_count = 3
#     success_count = 0
#     temp_order_no = None
#     for i in range(ws.max_row + 1):
#         if i < skip_count:
#             continue
#         order_no = ws['A' + str(i)].value
#         new_rm_mat_code = ws['B' + str(i)].value
#         bom_item = ws['C' + str(i)].value
#         if isinstance(order_no, int):
#             if temp_order_no != order_no:
#                 temp_order_no = order_no
#                 cursor = get_connection().cursor()
#                 sql = "SELECT ProductionOrderNo, RM_MaterialCode FROM [SAP_Order] WHERE ProductionOrderNo = '"+str(order_no)+"'"
#                 cursor.execute(sql)
#                 old_order_no = cursor.fetchone()
#                 cursor.commit()
#                 if old_order_no == None:
#                     print("Order Not Found -->", order_no)
#                 else:
#                     old_rm_mat_code = old_order_no.RM_MaterialCode
#                     if old_rm_mat_code == new_rm_mat_code:
#                         print("Already Correct -->", order_no)
#                     elif old_rm_mat_code != new_rm_mat_code:
#                         print("Fixing -->", order_no, "| Old RM Mat Code :", old_rm_mat_code, "| New RM Mat Code :", new_rm_mat_code, "| Bom Item :", bom_item)
#                         # conn = get_connection()
#                         # cursor = conn.cursor()
#                         # sql = "UPDATE [OrderControl] SET [RM_MaterialCode] = '"+new_rm_mat_code+"' WHERE OrderNo = '"+order_no+"'"
#                         # cursor.execute(sql)
#                         # conn.commit()
#                         # cursor = conn.cursor()
#                         # sql = "UPDATE [SAP_Order] SET [RM_MaterialCode] = '"+new_rm_mat_code+"' WHERE ProductionOrderNo = '"+order_no+"'"
#                         # cursor.execute(sql)
#                         # conn.commit()
#                         success_count = success_count + 1
#     print("Data Correction Amount :", success_count)
#     # return
