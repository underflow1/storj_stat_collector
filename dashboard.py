from flask import render_template, Flask, Response
from configparser import ConfigParser
from datetime import datetime
import pymysql, sys, json, math

app=Flask(__name__)
app.debug=False

def formatSize(size):
    "Formats size to be displayed in the most fitting unit"
    power = math.floor((len(str(abs(int(size))))-1)/3)
    units = {
            0: "b",
            1: "Kb",
            2: "Mb",
            3: "Gb",
            4: "Tb",
            5: "Pb",
            6: "Eb",
            7: "Zb",
            8: "Yb"
        }
    unit = units.get(power)
    sizeForm = size / (1024.00**power)
    return "{:.2f}{}".format(sizeForm, unit)
    
def pretty_time_delta(seconds): # преобразовать секунды в понятное время
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%dd%dh%dm%ds' % (days, hours, minutes, seconds)
    elif hours > 0:
        return '%dh%dm%ds' % (hours, minutes, seconds)
    elif minutes > 0:
        return '%dm%ds' % (minutes, seconds)
    else:
        return '%ds' % (seconds,)


config = ConfigParser()
config.read('collector.conf')


# устанавливаем подключение к главной базе данных
mainDbConfig = dict(config.items('database'))





#dashboardData['uptime'] = pretty_time_delta((datetime.strptime(json.loads(nodeApiDashboadData)['data']['startedAt'].split('.')[0], '%Y-%m-%dT%H:%M:%S') - datetime.now()).seconds)



@app.route("/dashboard")
def hello():
    try:
        con =  pymysql.connect(**mainDbConfig)
        cursor = con.cursor(pymysql.cursors.DictCursor)
    except Exception as e:
        print(e)
        sys.exit('ОШИБКА: Подключение к главной базе данных не удалось')    
    query = "SELECT nodeId, nodeName, nodeApiData FROM statistics"
    cursor.execute(query)
    result = cursor.fetchall()
    con.close()

    dashboardSummaryData = {}
    dashboardData = []
    egressTotal = 0
    ingressTotal = 0
    deleteTotal = 0
    diskSpaceUsedTotal = 0
    diskSpaceAvailableTotal = 0
    diskSpaceFreeTotal = 0
    for record in result:
        dashboardRow = {}
        
        apiData = json.loads(record['nodeApiData'])
        dashboardRow['nodeId'] = record['nodeId']
        dashboardRow['nodeName'] = record['nodeName']
        dashboardRow['version'] = apiData['dashboard']['data']['version']
        dashboardRow['uptodate'] = apiData['dashboard']['data']['upToDate']
        
        diskSpaceAvailable = apiData['dashboard']['data']['diskSpace']['available']
        diskSpaceUsed = apiData['dashboard']['data']['diskSpace']['used']
        diskSpaceFree = diskSpaceAvailable - diskSpaceUsed
        diskSpaceUsedPercent = round((diskSpaceUsed / diskSpaceAvailable)*100)

        dashboardRow['diskSpaceAvailable'] = formatSize(diskSpaceAvailable)
        dashboardRow['diskSpaceUsed'] = formatSize(diskSpaceUsed)
        dashboardRow['diskSpaceFree'] = formatSize(diskSpaceFree)
        dashboardRow['diskSpaceUsedPercent'] = str(diskSpaceUsedPercent) + '%'

        egress = 0
        ingress = 0
        delete = 0
        for satelliteItem in apiData['satellite']:
            for bandwidthDailyItem in satelliteItem['data']['bandwidthDaily']:
                egress += bandwidthDailyItem['egress']['usage']
                ingress += bandwidthDailyItem['ingress']['usage']
                delete += bandwidthDailyItem['delete']
        dashboardRow['egress'] = formatSize(egress)
        dashboardRow['ingress'] = formatSize(ingress)    
        startedAt = datetime.strptime(apiData['dashboard']['data']['startedAt'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        rightNow = datetime.now()
        delta = rightNow - startedAt

        dashboardRow['uptime'] = pretty_time_delta(delta.days*86400 + delta.seconds)
        dashboardData.append(dashboardRow)

        egressTotal += egress
        ingressTotal += ingress
        deleteTotal += delete
        diskSpaceUsedTotal += diskSpaceUsed
        diskSpaceAvailableTotal += diskSpaceAvailable
        diskSpaceFreeTotal += diskSpaceFree
    dashboardSummaryData['egressTotal'] = formatSize(egressTotal)
    dashboardSummaryData['ingressTotal'] = formatSize(ingressTotal)
    dashboardSummaryData['deleteTotal'] = formatSize(deleteTotal)
    dashboardSummaryData['diskSpaceUsedTotal'] = formatSize(diskSpaceUsedTotal)
    dashboardSummaryData['diskSpaceAvailableTotal'] = formatSize(diskSpaceAvailableTotal)
    dashboardSummaryData['diskSpaceFreeTotal'] = formatSize(diskSpaceFreeTotal)


    print(dashboardSummaryData)
    return render_template('template.html', dashboardData = dashboardData, dashboardSummaryData = dashboardSummaryData)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
