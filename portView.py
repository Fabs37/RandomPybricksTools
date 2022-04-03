#!/usr/bin/env pybricks-micropython


from pybricks.parameters import Port, Color, Button
# from pybricks.ev3devices import Motor, ColorSensor, InfraredSensor, GyroSensor, TouchSensor, UltrasonicSensor
from pybricks.hubs import EV3Brick
from pybricks.media.ev3dev import Font, Image, ImageFile
from os import listdir, system
import os.path
import time, _thread, typing, sys, traceback, json

# Credits: <https://github.com/pybricks/support/issues/152#issuecomment-709608118>

def rl(path) -> str:
    "Open a file, return its first line and close the file afterwards, ignoring any errors."
    try:
        f = open(path)
        txt = f.readline()
        f.close()
    except:
        txt = "0"
    return txt

class Sensor:
    def __init__(self, path) -> None:
        self.path = path
        self.driverName = rl(self.path+"/driver_name")[:-1]
        self.portLetter = rl(self.path+"/address")[12:13]
        self.numValues = int(rl(self.path+"/num_values")[:-1])
        self.mode = rl(self.path+"/mode")[:-1]
        self.values = None
        self.modes = rl(self.path+"/modes").split()
        self.commands = rl(self.path + "/commands").split()
        self.additionalAttributes = {"gyro-ang-offset": 0, "gyro-tilt-offset": 0} if self.driverName == "lego-ev3-gyro" else {}

    def setMode(self, mode):
        self.mode = mode
        system("echo %s > %s/mode" % (mode, self.path))
        self.numValues = int(rl(self.path+"/num_values")[:-1])

    def getValues(self):
        self.values = [int(rl(self.path+"/value"+str(i))[:-1]) for i in range(self.numValues)]
        return self.values

    def execCommand(self, command):
        system("echo %s > %s/command" % (command, self.path))
        self.numValues = int(rl(self.path+"/num_values")[:-1])

class Motor:
    def __init__(self, path) -> None:
        self.path = path
        self.portLetter = rl(self.path+"/address")[-2:-1]
        self.driverName = rl(self.path+"/driver_name")[:-1]
        self.speed = None
        self.position = None

    def getPosition(self):
        self.position = int(rl(self.path+"/position")[:-1])
        return self.position

    def getSpeed(self):
        self.speed = int(rl(self.path+"/speed")[:-1])
        return self.speed

    def resetPos(self):
        system("echo reset > %s/command" % self.path)




sensorNames = []
motorNames = []


portDevList = [None] * 8

# portDevList:typing.List[typing.Union[None, Motor, Sensor]] = [None] * 8

def updateDevList():
    global portDevList, sensorNames, motorNames

    dirs = listdir("/sys/class/tacho-motor")
    if dirs != motorNames: # motor added / removed
        print("updateDevList: Motor added/removed")
        portDevList[:4] = [None] * 4
        for dir in dirs:
            m = Motor("/sys/class/tacho-motor/"+dir)
            portDevList[ord(m.portLetter)-65] = m
    motorNames = dirs

    dirs = listdir("/sys/class/lego-sensor")
    if dirs != sensorNames: # sensor added / removed
        print("updateDevList: Sensor added/removed")
        portDevList[4:] = [None] * 4
        for dir in dirs:
            s = Sensor("/sys/class/lego-sensor/"+dir)
            portDevList[int(s.portLetter)+3] = s
    sensorNames = dirs
        
def caliEv3Reflect(sensor: Sensor):
    global portDevList, b, render, allCaliVals
    render = False
    time.sleep(0.1)

    b.screen.clear()
    b.screen.set_font(f18)
    txt = "Calibration: Port " + sensor.portLetter
    b.screen.draw_text((b.screen.width - f18.text_width(txt))/2, 0, txt)
    b.screen.set_font(f12)
    txt = "Put the sensor on a"
    b.screen.draw_text((b.screen.width - f12.text_width(txt))/2, 30, txt)
    txt = "surface and press [CENTER]"
    b.screen.draw_text((b.screen.width - f12.text_width(txt))/2, 70, txt)
    b.screen.set_font(f24)
    txt = "BLACK"
    b.screen.draw_text((b.screen.width - f24.text_width(txt))/2, 42, txt)
    sensor.setMode("COL-REFLECT")

    while not Button.CENTER in b.buttons.pressed():
        time.sleep(0.05)
    while Button.CENTER in b.buttons.pressed():
        time.sleep(0.05)
    black = sensor.getValues()[0]

    b.screen.draw_box(0, 42, b.screen.width, 70, fill=True, color=Color.WHITE)
    txt = "WHITE"
    b.screen.draw_text((b.screen.width - f24.text_width(txt))/2, 42, txt)


    while not Button.CENTER in b.buttons.pressed():
        time.sleep(0.05)
    white = sensor.getValues()[0]

    if white == black:
        b.screen.clear()
        b.screen.set_font(f12)
        b.screen.draw_text(0, 5, "Invalid values.")
        b.screen.draw_text(0, 25, "Please recalibrate.")
        while not any(b.buttons.pressed()):
            time.sleep(0.05)
    else:
        with open("/home/robot/.caliValues.json") as f:
            allCaliVals = json.load(f)
        allCaliVals[sensor.portLetter]["reflect"][0] = 100 / (white - black)
        allCaliVals[sensor.portLetter]["reflect"][1] = (-100 * black) / (white - black)
        with open("/home/robot/.caliValues.json", "w") as f:
            json.dump(allCaliVals, f, indent=4)


    render = True


def caliEv3Rgb(sensor: Sensor):
    global b, render
    render = False

    # Radios:rounded boxes, unfilled circle left (with dot inside if active), caption right, inverted colors if selected
    # Cali-Modes: (Todo: Try out -> Default)
        # Black + White
        # Black + Red+Green+Blue
    # Value range:
        # 0-255 (default)
        # 0-100
    # Start-Button (selected by default)


    render = True
    
def resetGyroAngles(sensor: Sensor):
    if sensor.mode in ("GYRO-ANG", "GYRO-G&A"):
        sensor.additionalAttributes["gyro-ang-offset"] = int(sensor.values[0])
    elif sensor.mode == "TILT-ANG":
        sensor.additionalAttributes["gyro-tilt-offset"] = int(sensor.values[0])




additionalFunctions = {
    "lego-ev3-color": {
        "Calib. COL-REFLECT": caliEv3Reflect,
        # "Calib. RGB-RAW": caliEv3Rgb
    },
    # "lego-ev3-gyro": {
    #     "Reset angles": resetGyroAngles
    # }
}

b = EV3Brick()
selectedDevNr = 6 # Number of the selected device (0-7)
modeSelected = [1, ""] # mode/command selected
menuOptionNrSelected = 0 # including headings
menuScrollPos = 0 # scroll pos of modeMenu
menuOptionsList = [] # All elements of the menu, including headings
portLetters = ["A", "B", "C", "D", "1", "2", "3", "4"]
menuOpen = False
allCaliVals = []
render = True # if False, stop rendering
f12 = Font(size=12)
f18 = Font(size=18)
f24 = Font(size=24)

defaultSettings = {'calibration.ev3col.reflect.enabled': True, 'calibration.ev3col.rgb.enabled': False, 'calibration.ev3col.rgb.defaultRange': 255, 'calibration.ev3col.rgb.defaultMode': 'single', 'hideModes': {'lego-ev3-color': ['COL-CAL'], 'lego-ev3-gyro': ['GYRO-CAL'], 'lego-ev3-ir': ['IR-CAL', 'IR-S-ALT']}}  
try:
    settings = json.load(open("/home/robot/.portView.conf.json"))
except:
    try:
        settings = json.load(open(__file__.rsplit("/", 1)[0]+"/.portView.conf.json"))
    except:
        settings = defaultSettings
for k in defaultSettings.keys():
        if k not in settings.keys():
            settings[k] = defaultSettings[k]

#arrow_up = Image("arrow_up_s.png")
arrow_up = Image.empty(22, 22)
arrow_up.draw_box(0, 0, 21, 21, fill=True)
arrow_up.draw_line(8, 18, 16, 18, color=Color.WHITE)
arrow_up.draw_line(8, 18, 8, 10, color=Color.WHITE)
arrow_up.draw_line(16, 18, 16, 10, color=Color.WHITE)
arrow_up.draw_line(8, 10, 4, 10, color=Color.WHITE)
arrow_up.draw_line(16, 10, 20, 10, color=Color.WHITE)
arrow_up.draw_line(4, 10, 12, 2, color=Color.WHITE)
arrow_up.draw_line(20, 10, 12, 2, color=Color.WHITE)

#arrow_down = Image("arrow_down_s.png")
arrow_down = Image.empty(22, 22)
arrow_down.draw_box(0, 0, 21, 21, fill=True)
arrow_down.draw_line(8, 6, 16, 6, color=Color.WHITE)
arrow_down.draw_line(8, 6, 8, 14, color=Color.WHITE)
arrow_down.draw_line(16, 6, 16, 14, color=Color.WHITE)
arrow_down.draw_line(8, 14, 4, 14, color=Color.WHITE)
arrow_down.draw_line(16, 14, 20, 14, color=Color.WHITE)
arrow_down.draw_line(4, 14, 12, 22, color=Color.WHITE)
arrow_down.draw_line(20, 14, 12, 22, color=Color.WHITE)

if any([settings["calibration.ev3col.reflect.enabled"], settings["calibration.ev3col.rgb.enabled"]]):
    try:
        f = open("/home/robot/.caliValues.json")
        allCaliVals = json.load(f)
        f.close()
    except:
        #f = open("/home/robot/.caliValues.json", "w")
        #f.write("{\"1\": [0, 100], \"2\": [0, 100], \"3\": [0, 100], \"4\": [0, 100]}")
        #f.close()
        #allCaliVals = {str(i+1): [0, 100] for i in range(4)}
        allCaliVals = {str(i+1): {"reflect": [1, 0], "rgb": {c: [1, 0] for c in ["red", "green", "blue"]}} for i in range(4)}
        json.dump(allCaliVals, open("/home/robot/.caliValues.json", "w"))
        print("CaliLoader: Created new .caliValues file")

def keyhandler():
    global selectedDevNr, modeSelected, menuOptionNrSelected, menuScrollPos, menuOptionsList, menuOpen, b, portDevList
    while True:
        while not any(b.buttons.pressed()):
            time.sleep(0.05)
        
        buttons = b.buttons.pressed()
        if not menuOpen:
            if Button.LEFT in buttons:
                if selectedDevNr == 0:
                    selectedDevNr = 7
                else:
                    selectedDevNr -= 1
            elif Button.RIGHT in buttons:
                if selectedDevNr == 7:
                    selectedDevNr = 0
                else:
                    selectedDevNr += 1
            elif Button.UP in buttons or Button.DOWN in buttons:
                if selectedDevNr > 3:
                    selectedDevNr -= 4
                else:
                    selectedDevNr += 4
            elif Button.CENTER in buttons and portDevList[selectedDevNr] != None:
                if selectedDevNr > 3: # Sensor -> open menu
                    menuOpen = True
                    print("keyhandler: opening modeMenu")

                    # menuOptionsList = [(0, "Modes:")] + [(1, elem) for elem in portDevList[selectedDevNr].modes if elem not in settings["hideModes"][portDevList[selectedDevNr].driverName]]
                    menuOptionsList = [(0, "Modes:")]
                    for mode in portDevList[selectedDevNr].modes:
                        if portDevList[selectedDevNr].driverName in settings["hideModes"]:
                            if mode in settings["hideModes"][portDevList[selectedDevNr].driverName]:
                                continue
                        menuOptionsList += [(1, mode)]

                    if portDevList[selectedDevNr].commands != []:
                        menuOptionsList += [(0, "Commands:")] + [(2, elem) for elem in portDevList[selectedDevNr].commands]
                    if portDevList[selectedDevNr].driverName in additionalFunctions.keys():
                        menuOptionsList += [(0, "Additional functions")]
                        for title in additionalFunctions[portDevList[selectedDevNr].driverName].keys():
                            menuOptionsList += [(3, title, additionalFunctions[portDevList[selectedDevNr].driverName][title])]
                    #if portDevList[selectedDevNr].driverName == "lego-ev3-color" and any(settings["calibration.ev3col.reflect.enabled"], settings["calibration.ev3col.rgb.enabled"]): # Calibration
                    #    menuOptionsList += [(0, "Additional: Calibration")]
                    #    if settings["calibration.ev3col.reflect.enabled"]:
                    #        menuOptionsList += [(3, "Calib. COL-REFLECT", caliEv3Reflect)]
                    #    if settings["calibration.ev3col.rgb.enabled"]:
                    #    menuOptionsList += [(3, "Calib. RGB-RAW", caliEv3Rgb)]

                    menuOptionNrSelected = menuOptionsList.index((1, portDevList[selectedDevNr].mode))
                    menuScrollPos = 0
                    if len(menuOptionsList) > 5:
                        if menuOptionNrSelected > 4:
                            menuScrollPos = menuOptionNrSelected - 4
                    
                    print("keyhandler: menuOptionsList:", menuOptionsList)

                else: # Motor -> reset
                    portDevList[selectedDevNr].resetPos()
                    print("keyhandler: resetting pos")
        
        else: # menuOpen == True
            if Button.UP in buttons:
                if menuOptionNrSelected != 1: # 0 -> Heading "Modes"
                    menuOptionNrSelected -= 1
                if menuOptionsList[menuOptionNrSelected][0] == 0:
                    menuOptionNrSelected -= 1

                if menuOptionNrSelected == 1 and menuScrollPos != 0: # Scroll up to make the heading visible
                    menuScrollPos = 0
                elif menuOptionNrSelected < menuScrollPos and menuScrollPos != 0:
                    menuScrollPos -= 1

            elif Button.DOWN in buttons:
                if menuOptionNrSelected != len(menuOptionsList)-1:
                    menuOptionNrSelected += 1
                if menuOptionsList[menuOptionNrSelected][0] == 0:
                    menuOptionNrSelected += 1

                for i in range(2):
                    if menuOptionNrSelected-4 > menuScrollPos:
                        menuScrollPos += 1

            elif Button.LEFT in buttons: # close the menu without changing anything
                menuOpen = False
                print("keyhandler: closing modeMenu")

            elif Button.CENTER in buttons:
                if menuOptionsList[menuOptionNrSelected][0] == 1: # Mode
                    portDevList[selectedDevNr].setMode(menuOptionsList[menuOptionNrSelected][1])
                elif menuOptionsList[menuOptionNrSelected][0] == 2: # Command
                    portDevList[selectedDevNr].execCommand(menuOptionsList[menuOptionNrSelected][1])
                elif menuOptionsList[menuOptionNrSelected][0] == 3: # Additional function
                    menuOptionsList[menuOptionNrSelected][2](portDevList[selectedDevNr])

                print("keyhandler: closing modeMenu")
                menuOpen = False
                
            

        while any(b.buttons.pressed()):
            time.sleep(0.05)

_thread.start_new_thread(keyhandler, [])

while True:
    if not render:
        time.sleep(0.1)
        continue

    # try:
    if not menuOpen:
        time.sleep(0.1)
        
        updateDevList()

        # print(portDevList)
        b.screen.clear()
        b.screen.set_font(f12)

        for i in range(4): # Motoren
            if i == selectedDevNr:
                b.screen.draw_box(44*i, 0, 44+44*i, 22, 5, True)
                b.screen.draw_image(10+44*i, -3, arrow_down)
            else:
                b.screen.draw_box(44*i, 0, 44+44*i, 22, 5, False)
                if portDevList[i] == None:
                    b.screen.draw_text(16+44*i, 5, "---")
                else:
                    txt = str(portDevList[i].getPosition())
                    b.screen.draw_text(44*i + (44-f12.text_width(txt))/2, 5, txt)

        for i in range(4): # Sensoren
            if i+4 == selectedDevNr:
                b.screen.draw_box(44*i, 105, 44+44*i, 127, 5, True)
                b.screen.draw_image(10+44*i, 105, arrow_up)
            else:
                b.screen.draw_box(44*i, 105, 44+44*i, 127, 5, False)
                if portDevList[i+4] == None:
                    b.screen.draw_text(16+44*i, 110, "---")
                elif len(portDevList[i+4].getValues()) > 1:
                    b.screen.draw_text(14+44*i, 110, "[...]")
                else:
                    if portDevList[i+4].mode == "COL-REFLECT" and settings['calibration.ev3col.reflect.enabled']:
                        vals = allCaliVals[portDevList[selectedDevNr].portLetter]["reflect"]
                        txt = str(int(vals[0] * portDevList[i+4].values[0] + vals[1]))
                    else:
                        txt = str(portDevList[i+4].values[0])
                    b.screen.draw_text(44*i + (44-f12.text_width(txt))/2, 110, txt)

        b.screen.set_font(f18)
        if portDevList[selectedDevNr] == None:
            b.screen.draw_text(0, 24, "%s: None" % portLetters[selectedDevNr])
        else:
            
            if selectedDevNr < 4: # Motor:
                b.screen.draw_text(0, 24, "%s: %s" % (portLetters[selectedDevNr], portDevList[selectedDevNr].driverName))
                b.screen.set_font(f12)
                b.screen.draw_text(7, 50, "Position [deg]")
                b.screen.draw_text(95, 50, "Speed [deg/s]")
                # b.screen.set_font(f18 if abs(int(portDevList[selectedDevNr].getPosition())) < 1000 and abs(int(portDevList[selectedDevNr].getSpeed())) < 1000 else f12)
                b.screen.set_font(f24)

                pos = str(portDevList[selectedDevNr].getPosition())
                b.screen.draw_text((b.screen.width/2 - f24.text_width(pos))/2, 75, pos)
                b.screen.draw_line(88, 42, 88, 90)

                speed = str(portDevList[selectedDevNr].getSpeed())
                b.screen.draw_text(b.screen.width/2 + (b.screen.width/2 - f24.text_width(speed))/2, 75, speed)

                # b.screen.set_font(f12)
                # b.screen.draw_text(0, 80, "Press [CENTER] to reset position")
            else: # Sensor
                b.screen.draw_text(0, 24, "%s: %s" % (portLetters[selectedDevNr], portDevList[selectedDevNr].mode))
                b.screen.set_font(f12)
                nv = portDevList[selectedDevNr].numValues
                b.screen.draw_text(0, 40, str(nv) + (" Value" if nv == 1 else " Values"))
                b.screen.set_font(f24)
                b.screen.draw_text(30, 55, str(portDevList[selectedDevNr].getValues())[1:-1])

                if portDevList[selectedDevNr].driverName == "lego-ev3-color" and portDevList[selectedDevNr].mode == "COL-REFLECT" and settings["calibration.ev3col.reflect.enabled"]:
                    b.screen.draw_line(88, 42, 88, 90)
                    b.screen.set_font(f12)
                    b.screen.draw_text(95, 40, "Calibrated")
                    b.screen.set_font(f24)
                    vals = allCaliVals[portDevList[selectedDevNr].portLetter]["reflect"]
                    b.screen.draw_text(110, 55, str(int(vals[0] * portDevList[selectedDevNr].values[0] + vals[1])))

                if portDevList[selectedDevNr].driverName == "lego-ev3-color" and portDevList[selectedDevNr].mode == "RGB-RAW" and settings["calibration.ev3col.rgb.enabled"]:
                    b.screen.draw_line(88, 42, 88, 90)
                    b.screen.set_font(f12)
                    b.screen.draw_text(95, 40, "Calibrated")
                    b.screen.set_font(f24)
                    vals = [allCaliVals[portDevList[selectedDevNr].portLetter]["rgb"][key] for key in ["red", "green", "blue"]]
                    input(vals)
                    b.screen.draw_text(110, 55, str([int(vals[colNr][1] * portDevList[selectedDevNr].values[colNr] + vals[colNr][2]) for colNr in range(3)])[1:-1])

    else: # menuOpen       
        time.sleep(0.1) 
        b.screen.clear()

        txt = portDevList[selectedDevNr].driverName
        f = f18 if f18.text_width(txt) < b.screen.width else f12
        b.screen.set_font(f)
        b.screen.draw_text((b.screen.width - f.text_width(txt))/2, 0, txt)

        rows2display = []
        if len(menuOptionsList) > 5:
            rows2display = menuOptionsList[menuScrollPos:menuScrollPos+5]
            # Scrollbar https://stackoverflow.com/questions/16366795/how-to-calculate-the-size-of-scroll-bar-thumb/22710156#22710156
            b.screen.draw_box(b.screen.width-8, 22, b.screen.width-1, 120)
            arrowHeight = 4
            viewportHeight = 100
            contentHeight = len(menuOptionsList) * 20

            # viewableRatio = viewportHeight / contentHeight
            # scrollbarArea = viewportHeight - arrowHeight * 2
            thumbHeight = (viewportHeight - arrowHeight * 2) * (viewportHeight / contentHeight)

            # scrollTrackSpace = contentHeight - scrollbarArea
            # scrollThumbSpace = viewportHeight - thumbHeight
            # scrollJump = scrollTrackSpace / scrollThumbSpace

            # contentOffset = menuScrollPos * 20
            thumbOffset = ((menuScrollPos * 20) / ((contentHeight - (viewportHeight - arrowHeight * 2)) / (viewportHeight - thumbHeight))) + 22 + arrowHeight/2
            # print(scrollbarArea, viewableRatio, thumbHeight, thumbOffset)
            # barLength = (5/len(menuOptionsList)) * 94
            # absScrollPos = (menuOptionNrSelected+1 / len(menuOptionsList)) * 94
            # topOffset = 24 + absScrollPos + barLength/2
            b.screen.draw_box(b.screen.width - 6, thumbOffset, b.screen.width - 3, thumbOffset + thumbHeight-1, r=2, fill=True)
        else:
            rows2display = menuOptionsList
            
        b.screen.set_font(f12)
        # Debug
        # b.screen.draw_text(0, 0, str(menuOptionNrSelected))
        # b.screen.draw_text(b.screen.width-f12.text_width(str(menuScrollPos)), 0, str(menuScrollPos))

        for i in range(len(rows2display)):
            if rows2display[i][0] == 0: # Heading
                b.screen.draw_text(0, 25+20*i, rows2display[i][1])
                b.screen.draw_line(0, 38+20*i, b.screen.width-11, 38+20*i)

            else: # Mode / command / extra
                if i+menuScrollPos == menuOptionNrSelected:
                    b.screen.draw_box(10, 22+20*i, b.screen.width-11, 40+20*i, 5, fill=True)
                    b.screen.draw_text(15, 25+20*i, rows2display[i][1], Color.WHITE)
                else:
                    b.screen.draw_box(10, 22+20*i, b.screen.width-11, 40+20*i, 5)
                    b.screen.draw_text(15, 25+20*i, rows2display[i][1])

    # except Exception as e:
    #     print("Exception occured during rendering:")
    #     print(e)
    #     print()

     
