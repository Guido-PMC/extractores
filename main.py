from asyncore import dispatcher
from telegram import *
from telegram.ext import *
from requests import *
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import schedule
import time
import requests
import gspread
import pandas as pd
from tuyapy import TuyaApi
from oauth2client.service_account import ServiceAccountCredentials

class switch:
    def __init__(self, id, nombre, obj):
        self.id = id
        self.nombre = nombre
        self.obj = obj


updater = Updater(token="5892683093:AAExln2A6M5JillrPfALhzSbAuZtZPk5FDE")
dispatcher = updater.dispatcher
credenciales = "/creds/pilarminingco-c11e8da70b2f.json"

print(f"La hora actual es: {datetime.now().strftime('%H:%M')}")


def turnONByName(list_devices,name):
    list_devices[name].turn_on()


def turnOFFByName(list_devices,name):
    list_devices[name].turn_off()


def list_SmartLifeObjs():
    api = TuyaApi()
    try:
        username,password,country_code,application = "guido@pilarmining.co","Creative31.","44","smart_life"
        api.init(username,password,country_code,application)
        devices = api.get_all_devices()
        list_devices = dict(sorted(dict((i.name(),i) for i in devices if i.obj_type == 'switch').items()))
    except Exception as e:
        print(e)
        for i in range(0,180):
            time.sleep(1)
            print(i)
        username,password,country_code,application = "guido@pilarmining.co","Creative31.","44","smart_life"
        api.init(username,password,country_code,application)
        devices = api.get_all_devices()
        list_devices = dict(sorted(dict((i.name(),i) for i in devices if i.obj_type == 'switch').items()))
    return list_devices

list_devices = list_SmartLifeObjs()

def startJob():
    print("Es la hora de prender el extractor")
    turnONByName(list_devices,"EXTRACTOR PODER2")

def stopJob():
    print("Es la hora de apagar el extractor")
    turnOFFByName(list_devices,"EXTRACTOR PODER2")

def getSheetsDataFrame(sheet, worksheet):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(credenciales, scope)
    client = gspread.authorize(creds)
    work_sheet = client.open(sheet)
    sheet_instance = work_sheet.worksheet(worksheet)
    records_data = sheet_instance.get_all_records()
    return (pd.DataFrame.from_dict(records_data))

def updateCellByLetter(documento, hoja, cell, data):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(credenciales, scope)
    client = gspread.authorize(creds)
    sheet = client.open(documento)
    sheet_instance = sheet.worksheet(hoja)
    sheet_instance.update(cell, data,value_input_option="USER_ENTERED")

admins_ids = getSheetsDataFrame("Automatismo Extractores", "Hoja 1")["IDS Admins"].to_list()
start_time = getSheetsDataFrame("Automatismo Extractores", "Hoja 1")["Start"].to_list()[0]
end_time = getSheetsDataFrame("Automatismo Extractores", "Hoja 1")["End"].to_list()[0]
print(admins_ids,start_time,end_time)

def startCommand(update: Update, context: CallbackContext):
    if (update.effective_chat.username) in admins_ids:
        print("Estoy hablando con un ADMIN")
        print(update.effective_chat)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Usar /setStartTime '12:00' usando comillas")

def setStartTime(update: Update, context: CallbackContext):
    if (update.effective_chat.username) in admins_ids:
        print("Estoy hablando con un ADMIN")
        hora = update.effective_message.text.split()[-1].replace("'","")
        hora = hora.replace('"','')
        if "setStartTime" in hora:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"String VACIO - ERROR")
        else:
            try:
                updateCellByLetter("Automatismo Extractores", "Hoja 1", "B2", hora)
                schedule.cancel_job(startJob)
                schedule.every(1).day.at(str(hora)).do(startJob)
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"Seteado START a las {hora}")
            except Exception as e:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error actualizando Base de datos + {e}")



def setStopTime(update: Update, context: CallbackContext):
    if (update.effective_chat.username) in admins_ids:
        print("Estoy hablando con un ADMIN")
        hora = update.effective_message.text.split()[-1].replace("'","")
        hora = hora.replace('"','')
        if "setStopTime" in hora:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"String VACIO - ERROR")
        else:
            try:
                updateCellByLetter("Automatismo Extractores", "Hoja 1", "C2", hora)
                schedule.cancel_job(startJob)
                schedule.every(1).day.at(str(hora)).do(stopJob)
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"Seteado STOP a las {hora}")
            except Exception as e:
                context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error actualizando Base de datos + {e}")

def getInfo(update: Update, context: CallbackContext):
    if (update.effective_chat.username) in admins_ids:
        print("Estoy hablando con un ADMIN")
        try:
            admins_ids2 = getSheetsDataFrame("Automatismo Extractores", "Hoja 1")["IDS Admins"].to_list()
            start_time = getSheetsDataFrame("Automatismo Extractores", "Hoja 1")["Start"].to_list()[0]
            end_time = getSheetsDataFrame("Automatismo Extractores", "Hoja 1")["End"].to_list()[0]
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"admins_ids = {admins_ids2} - start_time = {start_time} - end_time = {end_time}")
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error leyendo Base de datos + {e}")



dispatcher.add_handler(CommandHandler("start", startCommand))
dispatcher.add_handler(CommandHandler("setStartTime", setStartTime))
dispatcher.add_handler(CommandHandler("setStopTime", setStopTime))
dispatcher.add_handler(CommandHandler("getInfo", getInfo))

updater.start_polling()

while True:
    schedule.run_pending()
    updater.start_polling()


#job()
#schedule.cancel_job(job)
#schedule.every(1).day.at(str(start_time)).do(startJob)
#schedule.every(1).day.at(str(end_time)).do(endJob)
