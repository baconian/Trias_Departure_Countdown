import requests
import datetime
from dateutil.parser import parse
import xml.etree.ElementTree as etree
import sys


class arrival_inf:
    def __init__(self):
        self.line = None
        self.time = None
        self.direction = None

    def toString(self):
        return "{0}|{1}|{2}".format(self.line, self.time, self.direction)

    def __repr__(self):
        return "{0}|{1}|{2}".format(self.line, self.time, self.direction)


def start_up():
    global RequestorRef
    stop = input("Please enter the stop you want a countdown for.")
    RequestorRef = input("Enter your RequestorRef here.")
    return stop


def request(request_file, stop):
    """Sends a given request to the server."""
    global RequestorRef
    file = open(request_file, "r")
    xml = file.read().replace(
        "$Timestamp", datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    file.close()
    xml = xml.replace("$stop", stop)
    r = requests.post("https://trias.vrn.de/Middleware/Data/trias",
                      data=xml).text.replace("<", "\n<")
    return r


def get_StopPointRef(stop):
    """Fetches the StopPointRef for the name given in the argument stop."""
    save_response(request("location_information_request.xml",
                          stop), "location_information_response.xml")
    tree = etree.parse("location_information_response.xml",
                       etree.XMLParser(encoding='utf-8'))
    StopPointRef = tree.find('.//{trias}StopPointRef')
    return StopPointRef.text


def save_response(request, filename):
    """Saves the response from a request to a file."""
    f = open(filename, 'w', encoding="utf-8")
    print("saved")
    f.write(request)
    f.close()
    return None


def get_arrivals(stop):
    """Parses the arrival information from the response and returns it in an array."""
    print(request('stop_event_request.xml', stop))
    save_response(request('stop_event_request.xml', stop),
                  'stop_event_response.xml')
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


def run_countdown(stop):
    """Displays a countdown for the next arrival."""
    data = get_arrivals(stop)
    i = 0
    while True:
        for item in data:
            datetime_object = datetime.datetime.strptime(
                item.time.replace("\n", ""), '%Y-%m-%dT%H:%M:%S')
            entry = arrival_inf()
            entry.line = item.line
            entry.direction = item.direction
            entry.time = datetime_object-datetime.datetime.now()
            print(entry, end="\r")
        if i > 150000:
            data = get_arrivals(stop)
            i = 0


stop = start_up()
run_countdown(get_StopPointRef(stop))