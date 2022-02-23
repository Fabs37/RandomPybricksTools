#!/usr/bin/env pybricks-micropython

from pybricks.ev3devices import Motor as __Motor
from .sensors import CaliColorSensor as __CaliColorSensor, beep

import math as __math, time as __time, _thread as __thread

LEFT = True
RIGHT = False

class LineFollower:
    def __init__(self, motL: __Motor, motR: __Motor, colM: __CaliColorSensor, colL: __CaliColorSensor, colR: __CaliColorSensor) -> None:
        """
        Argumente:
          * `motL`: Der linke Motor des Roboters.
          * `motR`: Der rechte Motor des Roboters.
          * `colM`: Der mittlere Farbsensor des Roboters, der zum Linienfolgen verwendet wird. Er muss vor den Rädern in Fahrtrichtung montiert sein.
          * `colL`: Der linke Farbsensor des Roboters. Er und der rechte Sensor werden zum Abbiegen verwendet
          * `colR`: Der rechte Farbsensor des Roboters.
        """
        
        self.motL = motL
        "Der linke Motor, den der Linienfolger benutzt."
        self.motR = motR
        "Der rechte Motor, den der Linienfolger benutzt."
        self.colM = colM
        "Der mittlere Farbsensor des Roboters, der zum Linienfolgen verwendet wird."
        self.colL = colL
        "Der linke Farbsensor, der zum Abbiegen verwendet wird."
        self.colR = colR
        "Der rechte Farbsensor, der zum Abbiegen verwendet wird."

        self.__running = "OFF" # ON, OFF, STOP
        self.speed = 0
        "Die aktuelle (angestrebte) Geschwindigkeit, mit der der Roboter der Linie folgt. Kann einfach hierüber angepasst werden."
        self.setPointVal = 0
        "Der aktuelle Sollwert, den der Roboter anstrebt. Kann einfach hierüber angepasst werden."
        self.kp = 0.0
        "Die Proportionalitätskonstante, mit der der Roboter beim Linienfolgen rechnet. Kann einfach hierüber angepasst werden."

    def start(self, speed: int, kp: float, setPoint: int, side: bool, term: str = "x") -> None:
        """
        Lässt den Roboter einer Linie folgen. Das Programm wird nicht angehalten.
        
        Argumente:
        * `speed [deg/s]`: Die Winkelgeschwindigkeit des Roboters.
        * `kp`: Je größer diese Konstante ist, desto stärker lenkt der Roboter gegen, um an der Linie zu bleiben - oder über sie hinauszuschießen.
        * `setPoint [0-100]`: Der Sollwert an der Kante der Linie, die der Roboter ansteuert.
        * `side`: Wenn `True`, ist der mittlere Sensor links neben der Linie, sonst rechts davon.
        * `term`: [ERWEITERT] Beschreibt die Abhängigkeit der Lenkung vom Fehler. Standard ist `'x'` (proportionaler Zusammenhang), es kann aber jeder Term mit der Variable `x` (= Fehler) genommen werden, z.B. `'x^3'`. Das Modul `math` kann hierbei verwendet werden.
        """

        self.speed = speed
        self.kp = kp * (int(side)*2-1) # Wenn side == False, wird kp mit -1 multipliziert
        self.setPointVal = setPoint

        self.stop(-1)

        self.__running = "ON"
        __thread.start_new_thread(self.__start_raw, [term])


    def __start_raw(self, term):
        while self.__running == "ON":
            fehler = self.colM.reflection() - self.setPointVal
            l = eval(term, {"x": fehler, "math": __math}) * self.kp
            self.motL.run(self.speed - l)
            self.motR.run(self.speed + l)
            __time.sleep(0.01)

        if self.__running == "STOP": # Sicherstellen, dass die Kontrollschleife zu Ende ist, bevor die Motoren gestoppt werden
            self.motL.hold()
            self.motR.hold()

    def stop(self, decelerationTime: int = 0, wait: bool = True) -> None:
        """
        Bricht die Steuerungsschleife ab und bremst den Roboter.

        Argumente:
            * `decelerationTime`: Die Zeit, die der Roboter (idealerweise) braucht, um zum Stillstand zu kommen. In dieser Zeit folgt er weiterhin der Linie (mit verminderter Geschwindigkeit). Wenn `decelerationTime > 0`, dann wird nur die Kontrollschleife abgebrochen, die Motoren fahren aber mit den zuletzt berechneten Geschwindigkeiten weiter.
            * `wait`: Legt fest, ob bis zum Ende des Bremsvorgangs gewartet werden soll.
        """

        if not wait:
            __thread.start_new_thread(self.stop, (decelerationTime, True))
        else:
            if decelerationTime >= 0:
                self.accelerate(decelerationTime, 0, True)
                self.__running = "STOP"
            else:
                self.__running = "OFF"
            
    def accelerate(self, t: float, vNew: int, wait=False) -> None:
        """
        Beschleunigt / bremst den Roboter.

        Argumente:
            * `t [secs]`: Die Zeitspanne, in der der Beschleunigungsvorgang stattfindet.
            * `vNew [deg/s]`: Die neue Geschwindigkeit am Ende.
            * `wait`: Wenn `False`, wird die Methode in einem neuen Thread ausgeführt.
        """

        # alle 0.1s Wert ändern

        if not wait:
            __thread.start_new_thread(self.accelerate, (t, vNew, True))
        else:
            if t < 0.1:
                self.speed = vNew
                __time.sleep(t)
            else:
                t = float(t) # Sonst ist realDT ca. 1.6 mal so lang wie es sein sollte, frag mich nicht warum
                dv = (vNew - self.speed) / (t * 10)
                startTime = __time.time()
                for i in range(int(t*10)):
                    self.speed += dv
                    __time.sleep(0.1)
                self.speed = vNew
                print("[DEBUG l. 117] accel: Ende; dv=%s, realDt = %s" % (dv, __time.time() - startTime))
    
    def changeKP(self, t: float, kpNew: float, wait=False) -> None:
        """
        Ändert die Proportionalitätskonstante innerhalb einer Zeitspanne auf einen neuen Wert.
        
        Argumente:
            * `t [secs]`: Die Zeitspanne, in die die Änderung stattfindet.
            * `kpNew`: Die neue kp am Ende.
            * `wait`: Wenn `False`, wird die Methode in einem neuen Thread ausgeführt.
        """

        if not wait:
            __thread.start_new_thread(self.changeKP, (t, kpNew, True))
        else:
            if t < 0.1:
                self.kp = kpNew
                __time.sleep(t)
            else:
                t = float(t)
                dkp = (kpNew - self.speed) / (t * 10)
                startTime = __time.time()
                for i in range(int(t*10)):
                    self.kp += dkp
                    __time.sleep(0.1)
                self.kp = kpNew
                print("[DEBUG l. 142] chKP: Ende; dv=%s, realDt = %s" % (dkp, __time.time() - startTime))

    def changeSetPoint(self, t: float, setPointNew: float, wait=False) -> None:
        """
        Ändert den Sollwert innerhalb einer Zeitspanne auf einen neuen Wert.
        
        Argumente:
            * `t [secs]`: Die Zeitspanne, in die die Änderung stattfindet.
            * `kpNew`: Der neue Sollwert am Ende.
            * `wait`: Wenn `False`, wird die Methode in einem neuen Thread ausgeführt.
        """

        if not wait:
            __thread.start_new_thread(self.changeSetPoint, (t, setPointNew, True))
        else:
            if t < 0.1:
                self.setPointVal = setPointNew
                __time.sleep(t)
            else:
                t = float(t)
                dsp = (setPointNew - self.setPointVal) / (t * 10)
                startTime = __time.time()
                for i in range(int(t*10)):
                    self.setPointVal += dsp
                    __time.sleep(0.1)
                self.setPointVal = setPointNew
                print("[DEBUG l. 117] chSP: Ende; dsp=%s, realDt = %s" % (dsp, __time.time() - startTime))

    def nthTurningLeft(self, n: int, stop: bool = False, decelerationTime: int = 0, wait: bool = True) -> None:
        """
        ### WORK IN PROGRESS
        Biegt die `n`-te Querlinie, die von links kommt, ab. Zuvor muss ein Linienfolger angeschaltet worden sein.

        Argumente:
            * `n`: Die Abzweigung, an der abgebogen werden soll.
            * `stop`: Wenn `False`, fährt der Roboter nach dem Abbiegen weiter an der Linie.
            * `decelerationTime`: Die Zeit, die der Roboter braucht, um zum Stillstand zu kommen, wenn `stop == True`. (Siehe `stop()`)
            * `wait`: Wenn `False`, wird die Methode in einem neuen Thread ausgeführt.
        """
        if self.__running == "ON": # sonst nichts machen
            if not wait:
                __thread.start_new_thread(self.nthTurningLeft, (n, stop, decelerationTime, True))
            else:
                waitForLines(n, self.colL)

                # Eigentliches Programm goes here

                if stop:
                    self.stop(decelerationTime)

    def nthTurningRight(self, n) -> None:
        pass


def waitForLines(n: int, colSensor: __CaliColorSensor) -> None:
    """
    Wartet, bis `n` Linien an dem angegebenen Sensor vorbeigezogen sind.
    
    Argumente:

      * `n`: Die Anzahl der Linien.
      * `colSensor`: Der seitlich am Roboter montierte Farbsensor, der die Linie(n) zählen soll.
    """
    
    for i in range(n):
        while not(colSensor.reflection() > 65):
            pass
        beep(1000)
        while not(colSensor.reflection() < 40):
            pass
        beep(750)