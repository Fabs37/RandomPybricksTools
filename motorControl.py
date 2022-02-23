#!/usr/bin/env pybricks-micropython

import time, _thread
from pybricks.hubs import EV3Brick
from pybricks.parameters import Port, Button, Color
from pybricks.ev3devices import Motor
from pybricks.media.ev3dev import Font

b = EV3Brick()
f28 = Font(size=40)
f18 = Font(size=28)
motors = [None] * 4
letters = [chr(65+i) for i in range(4)]
selectedMotNr = 0
try:
    selectedMot = Motor(eval("Port." + letters[selectedMotNr], {"Port": Port}))
except:
    selectedMot = None

props = [[100, True] for i in range(4)] # [Power, notReversed]

def runner():
    global selectedMotNr, selectedMot, props, motors, b
    cPressedTime = 0.0
    cPressed = False
    while True:
        while not any(b.buttons.pressed()):
            time.sleep(0.05)
        if Button.UP in b.buttons.pressed():
            if selectedMot != None:
                selectedMot.dc(props[selectedMotNr][0] * ((int(props[selectedMotNr][1])*2)-1))
        elif Button.DOWN in b.buttons.pressed():
            if selectedMot != None:
                selectedMot.dc(props[selectedMotNr][0] * ((int(props[selectedMotNr][1])*2)-1) * -1)
        elif Button.LEFT in b.buttons.pressed():
            if selectedMotNr == 0:
                selectedMotNr = 3
            else:
                selectedMotNr -= 1

            try:
                selectedMot = Motor(eval("Port." + letters[selectedMotNr], {"Port": Port}))
            except:
                selectedMot = None

        elif Button.RIGHT in b.buttons.pressed():
            if selectedMotNr == 3:
                selectedMotNr = 0
            else:
                selectedMotNr += 1

            try:
                selectedMot = Motor(eval("Port." + letters[selectedMotNr], {"Port": Port}))
            except:
                selectedMot = None
        elif Button.CENTER in b.buttons.pressed():
            cPressed = True

        if cPressed:
            while any(b.buttons.pressed()):
                time.sleep(0.05)
                cPressedTime += 0.05
                if cPressedTime >= 1:
                    # reverse Motor
                    props[selectedMotNr][1] = not(props[selectedMotNr][1])
                    break
            if cPressedTime < 1:
                # change speed
                if props[selectedMotNr][0] == 25:
                    props[selectedMotNr][0] = 100
                else:
                    props[selectedMotNr][0] -= 25


        else:
            while any(b.buttons.pressed()):
                time.sleep(0.05)
            if selectedMot != None:
                selectedMot.stop()

        """
        if cPressed == True:
            if cPressedTime > 2:
                props[selectedMotNr][1] = not(props[selectedMotNr][1]
            else:
                if props[selectedMotNr][0] == 25:
                    props[selectedMotNr][0] = 100
                else:
                    props[selectedMotNr][0] -= 25
        """

        cPressed = False
        cPressedTime = 0

_thread.start_new_thread(runner, [])

while True:
    time.sleep(0.05)
    b.screen.clear()
    # Chevrons left/right
    b.screen.draw_line(44, 33, 17, 60, 3)
    b.screen.draw_line(17, 60, 42, 85, 3)
    b.screen.draw_line(135, 34, 161, 60, 3)
    b.screen.draw_line(161, 60, 133, 88, 3)
    for i in range(17, 20):
        b.screen.draw_circle(88, 45, i)
    b.screen.draw_box(58, 45, 118, 75, fill=True, color=Color.WHITE)

    if props[selectedMotNr][1]: # clockwise -> right
        b.screen.draw_line(105, 45, 113, 38, 3)
        b.screen.draw_line(105, 45, 97, 38, 3)
    else:
        b.screen.draw_line(110-39, 45, 118-39, 38, 3)
        b.screen.draw_line(110-39, 45, 102-39, 38, 3)

    b.screen.draw_text((178-f28.text_width(letters[selectedMotNr]))/2, 50, letters[selectedMotNr])

    # Full circle -> white rect = half circle (upper half)
    # Arrow to semicircle
    # Port letter (selected)
    # Speed

    b.screen.draw_text((178-f18.text_width(str(props[selectedMotNr][0])+"%"))/2, 95, str(props[selectedMotNr][0])+"%")
