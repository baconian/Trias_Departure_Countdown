import requests
import datetime
from dateutil.parser import parse
import xml.etree.ElementTree as ET

RequestorRef = ""  #Enter your RequestorRef here.

def request(request_file):
    file = open(request_file, "r")
    xml=file.read().replace("%Timestamp%",datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    file.close()
    xml= xml.replace("%RequestorRef%", RequestorRef)
    r = requests.post("https://trias.vrn.de/Middleware/Data/trias", data=xml).text.replace("<","\n<")
    return r

def save_response(request,filename):
    f = open(filename,'w', encoding="utf-8")
    f.write(request)
    f.close()
    return None

class arrival:
    def __init__(self, line, time):
        self.line = line
        self.time = time

def get_Schedule(response):
    data=[]
    response=response.split("<Text>Heidelberg, Bethanien-Krankh.\n </Text>")
    for item in response:
        if item.find("<PublishedLineName>\n <Text>")>0:

            temp=item.split("<PublishedLineName>\n <Text>")
            temp2=temp[1].split("</Text>")
            line=temp2[0].replace("\n","")
            temp3=temp[0].split("<EstimatedTime>")
            temp3[1]=temp3[1].split("</EstimatedTime>")
            time=temp3[1][0].replace("\n ","")

            arr=[]
            arr.append(line)
            arr.append(time)
            data.append(arr)
    return data

def update_data(data):
    data=get_Schedule(request("stop_event_request.xml"))

def run_countdown():
    data=get_Schedule(request("stop_event_request.xml"))
    for item in data:
        item.append(item[1])
    i=0
    while True:
        for item in data:
            datetime_object = datetime.datetime.strptime(item[2],'%Y-%m-%dT%H:%M:%S')
            item[1]=str(datetime_object-datetime.datetime.now())
        print(data, end='\r')
        i+=1
        if i>150000:
                data=get_Schedule(request("stop_event_request.xml"))
                for item in data:
                    item.append(item[1])
                i=0

save_response(request("stop_event_request.xml"),"stop_event_response.xml")