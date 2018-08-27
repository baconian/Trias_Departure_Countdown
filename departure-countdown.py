import requests
import datetime
from dateutil.parser import parse
import xml.etree.ElementTree as etree


RequestorRef = ""  # Enter your RequestorRef here.


class arrival_inf:
    def __init__(self):
        self.line = None
        self.time = None
        self.direction = None

    def toString(self):
        return "{0}{1}{2}".format(self.line, self.time, self.direction)

    def __repr__(self):
        return "{0}{1}{2}".format(self.line, self.time, self.direction)


def request(request_file):
    file = open(request_file, "r")
    xml = file.read().replace(
        "%Timestamp%", datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    file.close()
    xml = xml.replace("%RequestorRef%", RequestorRef)
    r = requests.post("https://trias.vrn.de/Middleware/Data/trias",
                      data=xml).text.replace("<", "\n<")
    return r


def save_response(request, filename):
    f = open(filename, 'w', encoding="utf-8")
    f.write(request)
    f.close()
    return None


class arrival:
    def __init__(self, line, time):
        self.line = line
        self.time = time


def get_arrivals():
    tree = etree.parse('stop_event_response.xml',
                       etree.XMLParser(encoding='utf-8'))
    i = 0
    arrivals = []
    PublishedLineNames = tree.findall('.//{trias}PublishedLineName')
    for PublishedLine in PublishedLineNames:
        for node in PublishedLine.getiterator():
            if node.tag == '{trias}Text':
                arrivals.append(arrival_inf())
                arrivals[i].line = node.text
                i += 1

    i = 0
    Directions = tree.findall('.//{trias}DestinationText')
    for Direction in Directions:
        for node in Direction.getiterator():
            if node.tag == '{trias}Text':
                arrivals[i].direction = node.text
                i += 1

    i = 0
    for EstimatedTime in tree.findall('.//{trias}EstimatedTime'):
        arrivals[i].time = EstimatedTime.text
        i += 1

    i = 0
    for TimetableTime in tree.findall('.//{trias}TimetabledTime'):
        if arrivals[i].time == None:
            arrivals[i].time = TimetableTime.text
        i += 1

    return arrivals


def run_countdown():
    save_response(request('stop_event_request.xml'), 'stop_event_response.xml')
    data = get_arrivals()
    while True:
        for item in data:
            datetime_object = datetime.datetime.strptime(
                item.time.replace("\n",""), '%Y-%m-%dT%H:%M:%S')
            entry = arrival_inf()
            entry.line = item.line
            entry.direction = item.direction
            entry.time = datetime_object-datetime.datetime.now()
            print(entry, end='\r')

run_countdown()