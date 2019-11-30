# -*- coding: utf-8 -*-
version = "7.0.1"
from datetime import datetime

import configparser
import shutil
import os
import sys
import sqlite3
import requests
import json
import pymysql

# объявление функций
if True:
    def formatSize(size):
        "Formats size to be displayed in the most fitting unit"
        power = math.floor((len(str(abs(int(size))))-1)/3)
        units = {
                0: " B",
                1: "KB",
                2: "MB",
                3: "GB",
                4: "TB",
                5: "PB",
                6: "EB",
                7: "ZB",
                8: "YB"
            }
        unit = units.get(power)
        sizeForm = size / (1000.00**power)
        return "{:9.2f} {}".format(sizeForm, unit)
        
    def getLastDate(node_id): # возвращает последнюю дату сохраненую в главной базе данных
        args = (node_id)
        query = ''' SELECT MAX(date) FROM bandwidth WHERE nodeId = %s '''
        cursorMain.execute(query,args)
        result = cursorMain.fetchone()[0]
        if result:
            return result
        else: 
            return False

    def removeLastData(node_id, last_date): # удаляет данные на последнюю дату в главной базе данных (т.к. они могут быть не полными)
        args = (node_id, last_date)
        query = ''' DELETE FROM bandwidth WHERE nodeId = %s AND date = %s '''
        try:
            cursorMain.execute(query,args)
            rowsAffected = cursorMain.rowcount
            dbConnectionMain.commit()
            print('Удалено ', rowsAffected, 'строк.' )
        except Exception as e:
            sys.exit('Не удалось удалить последние данные', e)
        else:
            return True

# Инициализация переменных, подключения к базам данных и прочие проверки
if True:
    # разворачиваем дефолтный конфиг
    appFolderName = os.path.join(sys.path[0])
    print(appFolderName)
    configFileName = 'collector.conf'

    configPath = os.path.join(appFolderName, configFileName)
    if not os.path.isfile(configPath):
        if os.path.isfile(os.path.join(configPath + ".sample")):
            print('Копирую начальный конфиг')
            shutil.copy(os.path.join(configPath + ".sample"), configPath)
        else:
            sys.exit('ОШИБКА: Путь не существует: ' + configPath)

    config = configparser.ConfigParser()
    config.read(configPath)

    # проверяем наличие sqlite баз ноды и открыаем на чтение
    sqliteDbPath = config.get('stuff', 'sqliteDbPath')

    if os.path.exists(sqliteDbPath) == False:
        sys.exit('ОШИБКА: Путь не существует: ' + sqliteDbPath)

    if os.path.isfile(os.path.join(sqliteDbPath,"bandwidth.db")) == True:
        dbPath = sqliteDbPath
        dbPathBW = os.path.join(dbPath,"bandwidth.db")
        dbPathBW = 'file:' + dbPathBW + '?mode=ro'
    else:
        sys.exit('ОШИБКА: Файл bandwidth.db не существует: ' + dbPathBW )

    dbExternalConfig = dict(config.items('database'))

    dbConnectionNode = sqlite3.connect(dbPathBW, uri=True)
    if dbConnectionNode:
        cursorNode = dbConnectionNode.cursor()
    else: 
        sys.exit('ОШИБКА: Подключение к базе данных ноды не удалось')

    # устанавливаем подключение к главной базе данных
    dbConnectionMain =  pymysql.connect(**dbExternalConfig)
    if dbConnectionMain:
        cursorMain = dbConnectionMain.cursor()
    else: 
        sys.exit('ОШИБКА: Подключение к главной базе данных не удалось')

    # получаем данные от ноды по API
    satellites = []
    satellitesStats = {}
    try:
        response  = requests.get(config.get('stuff', 'api')+ 'dashboard')

        nodeId = json.loads(response.text)['data']['nodeID']

        for item in json.loads(response.text)['data']['satellites']:
            satellites.append(item['id'])

        for nodeSatellite in satellites:
            satellitesStats[nodeSatellite] = {}
            satellitesStats[nodeSatellite]['audit'] = json.loads(requests.get(config.get('stuff', 'api')+ 'satellite/' + nodeSatellite).text)['data']['audit']
            satellitesStats[nodeSatellite]['uptime'] = json.loads(requests.get(config.get('stuff', 'api')+ 'satellite/' + nodeSatellite).text)['data']['uptime']
    except Exception as e:
        sys.exit('ОШИБКА: API ноды недоступен')

    # получаем имя ноды (из имени хоста :) )
    f = open('/etc/hostname', 'r')
    nodeName = f.read().strip().replace("node-", '')
    f.close()

    # получаем последнюю дату из главной базы данных
    lastDate = getLastDate(nodeId)

# Собственно сам код
if False:
    if lastDate:
        print('Последняя дата в главной базе данных: ', lastDate)
        removeLastData(nodeId, lastDate)
    else:
        lastDate = datetime(2019,1,1).strftime("%Y-%m-%d")
        print('В главной базе данных нет информации')
    
    args = {'nodeId': nodeId, 'nodeName': nodeName, 'lastDate': lastDate }

    queryRepeatingPart = '''
            hex(satellite_id) AS satelliteId,
            CASE hex(satellite_id)
                WHEN 'A28B4F04E10BAE85D67F4C6CB82BF8D4C0F0F47A8EA72627524DEB6EC0000000' THEN 'us-central-1'
                WHEN 'AF2C42003EFC826AB4361F73F9D890942146FE0EBE806786F8E7190800000000' THEN 'europe-west-1'
                WHEN '84A74C2CD43C5BA76535E1F42F5DF7C287ED68D33522782F4AFABFDB40000000' THEN 'asia-east-1'
                WHEN '004AE89E970E703DF42BA4AB1416A3B30B7E1D8E14AA0E558F7EE26800000000' THEN 'stefan-benten'
                ELSE '-UNKNOWN-'
            END satelliteName,
            action,
            CASE action
                WHEN 1 THEN 'Ingress'
                WHEN 2 THEN 'Egress'
                WHEN 3 THEN 'Egress Audit'
                WHEN 4 THEN 'Egress Repair'
                WHEN 5 THEN 'Ingress Repair'
            END actionName,        
            amount '''

    query = '''
            SELECT
            :nodeId, :nodeName, date, month, satelliteId, satelliteName, action, actionName, SUM(amount)
            FROM (
                SELECT :nodeId, :nodeName, date(created_at) AS date, strftime('%m', created_at) AS month,''' + queryRepeatingPart + ''' FROM bandwidth_usage 
            UNION 
                SELECT :nodeId, :nodeName, date(interval_start) AS date, strftime('%m', interval_start) AS month,''' + queryRepeatingPart + ''' FROM bandwidth_usage_rollups)
            WHERE date >= :lastDate
            GROUP BY date, satelliteName, actionName
            ORDER BY date, action, actionName ASC
    '''

    data = dbConnectionNode.execute(query, args).fetchall()
    dbConnectionNode.close()
    
    rowsAffected = 0
    for row in data:
        try:
            cursorMain.execute("INSERT INTO bandwidth VALUES (Null, %s,%s,%s,%s,%s,%s,%s,%s,%s);", row)
        except Exception as e:
            print("ОШИБКА: Что-то произошло при вставке", e)
        else:
           rowsAffected = rowsAffected + cursorMain.rowcount
    dbConnectionMain.commit()
    dbConnectionMain.close()

    print('Записано ', rowsAffected, 'строк.')
