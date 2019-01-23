import requests
import datetime
from dateutil.parser import parse
import xml.etree.ElementTree as etree
import sys
import os.path
import time
import threading
from copy import deepcopy

trias_link = None
RequestorRef = None


class arrival_inf:
    def __init__(self):
        self.line = None
        self.time = None
        self.direction = None

    def toString(self):
        return "{0}|{1}|{2}".format(self.line, self.time, self.direction)

    def __repr__(self):
        return "{0}|{1}|{2}".format(self.line, self.time, self.direction)


def stop_selector(stop):
    """Prompts the user to select the correct stop, if several match."""
    StopPointOptions = get_StopPointRef(stop)
    i = 1
    keys = list(StopPointOptions)
    if len(StopPointOptions) > 1:
        for key in StopPointOptions:
            print("["+str(i)+"] "+StopPointOptions[key])
            i += 1
        stopInt = input(
            "Please select the stop you are looking for by entering the number:")

        stop = StopPointOptions[keys[int(stopInt)-1]]
    else:
        stop = StopPointOptions[keys[0]]
    return stop


def create_cfg(RequestorRef, trias_link, stop_point):
    """Saves certain variables to a config."""
    config = etree.Element('config')
    item1 = etree.SubElement(config, 'RequestorRef')
    item2 = etree.SubElement(config, 'trias_link')
    item3 = etree.SubElement(config, 'stop_point')
    item1.text = RequestorRef
    item2.text = trias_link
    item3.text = stop_point
    mydata = etree.tostring(config).decode("utf-8")
    myfile = open("config.xml", "w")
    myfile.write(mydata)


def load_cfg():
    """Checks if a config file exists and loads it."""
    global RequestorRef
    global trias_link
    if os.path.isfile("config.xml"):
        tree = etree.parse("config.xml",
                           etree.XMLParser(encoding='utf-8'))
        RequestorRef = tree.find('.//RequestorRef').text
        trias_link = tree.find('.//trias_link').text
        stop = tree.find('.//stop_point').text
    else:
        RequestorRef = None
        trias_link = None
        stop = None
    return stop


def configure():
    """Configures the program and safes a config file"""
    global trias_link
    global RequestorRef
    trias_link = input("Enter the Trias link you want to use here (leave this field empty to set it to the default value):\n")
    if trias_link=="":
        trias_link = "https://trias.vrn.de/Middleware/trias"
        print("Trias link set to default value.")
    RequestorRef = input("Enter your RequestorRef here:\n")
    stop = input("Please enter the stop you want a countdown for:\n")
    stop = stop_selector(stop)
    create_cfg(RequestorRef, trias_link, stop)
    return stop


def start_up():
    """Prompts the user for the stop and RequestorRef."""
    global RequestorRef
    global trias_link
    stop = load_cfg()
    if trias_link == None or RequestorRef == None or stop == None:
        configure()
    else:
        print("A conig file has been loaded.")
        print("Do you want to:")
        print("[1] run the program with this config.")
        print("[2] reset the config.")
        print("[3] choose a new stop.")
        answer = None
        while answer not in ("1", "2", "3"):
            answer = input("Please choose one of the options:\n")
        if answer == "2":
            configure()
        elif answer == "3":
            stop = input("Please enter the stop you want a countdown for:\n")
            stop = stop_selector(stop)
            create_cfg(RequestorRef, trias_link, stop)
    return stop


def request(request_file, stop):
    """Sends a given request to the server."""
    global RequestorRef
    global trias_link
    file = open(request_file, "r")
    xml = file.read().replace(
        "$Timestamp", datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    file.close()
    xml = xml.replace("$stop", stop)
    xml = xml.replace("$RequestorRef", RequestorRef)
    headers = {'content-type': 'text/xml ','RequestorRef': RequestorRef}
    r = requests.post(trias_link,
                      data=xml,headers=headers).text.replace("<", "\n<")
    return r


def get_StopPointRef(stop):
    """Fetches the StopPointRef for the name given in the argument stop."""
    save_response(request("location_information_request.xml", stop
                          ).strip(), "location_information_response.xml")
    tree = etree.parse("location_information_response.xml",
                       etree.XMLParser(encoding='utf-8'))
    StopPointOptions = {}
    StopPointNames = tree.findall('.//{trias}StopPointName')
    for StopPointRef in tree.findall('.//{trias}StopPointRef'):
        StopPointOptions[StopPointRef.text.replace("\n", "")] = None
    StopPointNameList = []

    for StopPointName in StopPointNames:
        for node in StopPointName.getiterator():
            if node.tag == '{trias}Text':
                StopPointNameList.append(node.text.replace("\n", ""))

    i = 0
    for key in StopPointOptions:
        StopPointOptions[key] = StopPointNameList[i]
        i += 1
    return StopPointOptions


def save_response(request, filename):
    """Saves the response from a request to a file."""
    f = open(filename, 'w', encoding="utf-8")
    f.write(request)
    f.close()
    return None


def get_arrivals(stop):
    """Parses the arrival information from the response and returns it in an array."""
    save_response(request('stop_event_request.xml', stop),
                  'stop_event_response.xml')
    tree = etree.parse('stop_event_response.xml',
                       etree.XMLParser(encoding='utf-8'))
    arrivals = []

    i = 0
    PublishedLineNames = tree.findall('.//{trias}PublishedLineName')
    for PublishedLine in PublishedLineNames:
        for node in PublishedLine.getiterator():
            if node.tag == '{trias}Text':
                arrivals.append(arrival_inf())
                arrivals[i].line = node.text.replace("\n","")
                i += 1

    i = 0
    Directions = tree.findall('.//{trias}DestinationText')
    for Direction in Directions:
        for node in Direction.getiterator():
            if node.tag == '{trias}Text':
                arrivals[i].direction = node.text.replace("\n","")
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

def update_data(stop):
    global data
    while True:
        time.sleep(5)
        data = get_arrivals(stop)

def print_display():
    global data
    while True:
        display=deepcopy(data)
        i=0
        for item in display:
            time.sleep(0.1)
            item.line=data[i].line
            item.direction=data[i].direction
            item.time=data[i].time
            datetime_object = datetime.datetime.strptime(
                item.time.replace("\n", ""), '%Y-%m-%dT%H:%M:%S')
            item.time = datetime_object-datetime.datetime.now()
            i+=1
        print(display, end='\r')

def run_countdown(stop):
    global data
    """Displays a countdown for the next arrival."""
    data = get_arrivals(stop)
    t1=threading.Thread(target=print_display,args=())
    t2=threading.Thread(target=update_data,args=(stop,))
    t1.start()
    t2.start()
        
        


stop = start_up()
run_countdown(stop)
