import requests
import json
from storage import make_s_msg_obj, users_storage, keyboards, state, timetable_output_mode
import logging

def handle(event):
    user_id = event['object']['message']['from_id']
    r_msg = event['object']['message']['text'] # received message
    #s_msg = "что-то пошло не так"
    #keyboard = keyboards['main']
    groups_list = []
    try:
        groups_list = getOptionsList(r_msg)
    except Exception as e:
        print("Ошибка при запросе расписания")
        print(e)

    if(len(groups_list)<1):
        s_msg = "Не могу найти группу "+r_msg
        keyboard = keyboards['main']
        users_storage[user_id]['state'] = state.WAIT_GROUP_FOR_EXAMS
        #s_msg_obj = make_s_msg_obj(s_msg, keyboard)
        #return s_msg_obj
    if(len(groups_list)>1 and len(groups_list)<=10):
        s_msg = "уточните, пожалуйста"
        keyboard = make_optiongroup_keyboard(groups_list)
        users_storage[user_id]['state'] = state.WAIT_GROUP_FOR_EXAMS
        #s_msg_obj = make_s_msg_obj(s_msg, keyboard)
        #return s_msg_obj
    if(len(groups_list)>10):
        s_msg = "нужно уточнить группу"
        keyboard = keyboards['main']
        users_storage[user_id]['state'] = state.WAIT_GROUP_FOR_EXAMS
        #s_msg_obj = make_s_msg_obj(s_msg, keyboard)
        #return s_msg_obj
    if(len(groups_list)==1):
        timetable = getTimetable(groups_list[0])
        s_msg = f"Расписание экзаменов группы {groups_list[0]['group']}\n{formatTimetable(timetable)}"
        keyboard = keyboards['main']
        users_storage[user_id]['state'] = state.INACTION
        #s_msg_obj = make_s_msg_obj(s_msg, keyboard)
        #return s_msg_obj
    s_msg_obj = make_s_msg_obj(s_msg=s_msg, keyboard=keyboard)
    return s_msg_obj


def getOptionsList(text): # список возможных вариантов для text
    url1 = "https://kai.ru/raspisanie?p_p_id=pubStudentSchedule_WAR_publicStudentSchedule10&p_p_lifecycle=2&p_p_resource_id=getGroupsURL&query=" #для id группы
    #s = requests.Session() # session
    r1 = requests.get(url1+text) # получение kai_id группы
    r1 = r1.json() # список возможных значений 
    return r1

def getTimetable(group):
    timetable_url = "https://kai.ru/raspisanie"
    url2 = "https://kai.ru/raspisanie?p_p_id=pubStudentSchedule_WAR_publicStudentSchedule10&p_p_lifecycle=2&p_p_resource_id=examSchedule" # для расписания

    kai_group_id = group['id']
    kai_group_num = group['group']
    forma = group['forma']
    r2 = requests.post(url2, {'groupId': kai_group_id, 'programForm': forma})
    timetable = r2.json()
    return timetable

def formatTimetable(timetable):
    #weekdays = ["вс","пн","вт","ср","чт","пт","сб"]
    weekdays = ["вскресенье","понедельник","вторник","среда","четверг","пятница","суббота"]
    result = ""
    #result+="распиание для группы "+group+"\n"
    exams = timetable
    #exams = timetable.keys() # список дней в расписании
    #exams = sorted(exams) # сортировка дней в расписании
    for exam in exams:
        buildNum = exam['buildNum'].strip().replace("-", "")
        buildSymbol = "🏟" if (buildNum.find("ОЛИМП")>-1) else  "🏛"
        audNum = exam['audNum'].strip().replace("-", "")
        build_aud = f"[{buildNum}{buildSymbol}, {audNum}]" # здание и аудитория
        if(buildNum==""): build_aud=f"[{audNum}]"
        if(audNum==""): build_aud=f"[{buildNum}{buildSymbol}]"
        if((buildNum=="") and (audNum=="")): build_aud=""
        if(buildNum!=""): buildNum = buildNum + buildSymbol
        examTime = exam['examTime'].strip()
        disciplName = exam['disciplName'].strip()
        #group = exam['group'].strip()
        examDate = exam['examDate'].strip()
        result = result+ f"📆{examDate}   {build_aud} {examTime} - {disciplName}\n"
        result=result+"\n"
    return(result)

def make_optiongroup_keyboard(groups_list):
    # максимальный размер inline клавиатуры 5х6
    keyboard = {"inline": True, "buttons": []}

    """buttons_count = len(groups_list)
    rows = buttons_count // 2
    #cols = buttons_count % 2
    template = []
    for i in range(0, rows): # 0, 1, 2, ... (rows) - не включает rows
        template.append([])
        template[i].append([])
        template[i].append([])
        if(i==rows-1 and buttons_count%2>0): template[i].append([]) # если последний ряд и кол-во кнопок нечетно"""
    row = -1
    for i, group in enumerate(groups_list): # The enumerate function gives us an iterable where each element is a tuple that contains the index of the item and the original item value
        if((i+1)==len(groups_list)):
            keyboard['buttons'][row].append({'action': {'type': "text", 'label': group['group']}})
            continue
        if(i%2==0):
            keyboard['buttons'].append([]) # обавление новой строки
            row+=1
        keyboard['buttons'][row].append({'action': {'type': "text", 'label': group['group']}})
        
        #keyboard['buttons'][i]['action']['type'] = "text"
        #keyboard['buttons'][i][0]['action']['label'] = 
    """for i, group in enumerate(groups_list): # The enumerate function gives us an iterable where each element is a tuple that contains the index of the item and the original item value
        keyboard['buttons'].append([{'action': {'type': "text", 'label': "group_num"}}])
        #keyboard['buttons'][i]['action']['type'] = "text"
        keyboard['buttons'][i][0]['action']['label'] = group['group']"""
    keyboard = json.dumps(keyboard) # перевод словаря в json формат
    return keyboard