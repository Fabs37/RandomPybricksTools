#!/usr/bin/env pybricks-micropython

from pybricks import parameters as __parameters, ev3devices as __ev3devices

import os as __os, json as __json

__num2Port = {"1": __parameters.Port.S1, "2": __parameters.Port.S2, "3": __parameters.Port.S3, "4": __parameters.Port.S4}
__port2Num = {__parameters.Port.S1: "1", __parameters.Port.S2: "2", __parameters.Port.S3: "3", __parameters.Port.S4: "4"}

def __rl(path) -> str:
    "Open a file, return its first line and close the file afterwards, ignoring any errors."
    try:
        f = open(path)
        txt = f.readline()
        f.close()
    except:
        txt = "0"
    return txt

class BetterEv3devSensor():
    def __init__(self, port:__parameters.Port, driverName:str):
        """Initiates the sensor at Port `port`. If no sensor is connected there or if it doesn't match the `driverName`, raise `ValueError`."""
        sensorFound = False
        for sens in __os.listdir("/sys/class/lego-sensor"):
            # print("checking sensor %s, drivername: %s" % (sens, __rl("/sys/class/lego-sensor/"+sens+"/driver_name")[:-1]))
            if __num2Port[__rl("/sys/class/lego-sensor/"+sens+"/address")[-2:-1]] != port:
                continue
            if __rl("/sys/class/lego-sensor/"+sens+"/driver_name")[:-1] != driverName:
                continue
            sensorFound = True
            self._path = "/sys/class/lego-sensor/"+sens+"/"
            self._driverName = driverName
            self._commands = __rl(self._path + "commands").split()
            self._modes = __rl(self._path+"modes").split()
            break
        if not sensorFound:
            raise ValueError("No '%s' sensor found on Port %s" % (driverName, port))
    
    def _read(self, mode:str) -> tuple[int]:
        """Reads all values provided by the sensor being set to `mode`. Raise `ValueError` if `mode` can't be applied to the sensor."""
        if mode not in self._modes:
            raise ValueError("Mode '%s' doesn't exist for this '%s' sensor." % (mode, self._driverName))
        else:
            __os.system("echo %s > %smode" % (mode, self._path))
            errorCount = 0
            while errorCount < 3:
                try:
                    return tuple([int(__rl(self._path+"value"+str(i))[:-1]) for i in range(int(__rl(self._path+"num_values")))])
                except:
                    errorCount += 1
            return ()

    def _execCommand(self, command:str):
        """Sends the `command` to the sensor's command file. If the sensor doesn't support the command, raise `ValueError`."""
        if command not in self._commands:
            raise ValueError("Command '%s' is not supported by this '%s' sensor." % (command, self._driverName))
        __os.system("echo %s > %scommand" % (command, self._path))


class HtNxtColorV2Sensor(BetterEv3devSensor):
    """HiTechnic NXT Color Sensor V2."""
    def __init__(self, port: __parameters.Port):
        """
        Arguments:
            * `port`: Port to which the sensor is connected.
        """
        super().__init__(port, "ht-nxt-color-v2")
    
    def color(self) -> int:
        """Returns the color code of the color detected by the sensor. The codes are the the following:
        
        Color         | Code
        --------------|---------
        Black         | 0
        Purple        | 1
        Blue          | 2
        Cyan          | 3
        Green         | 4
        Yellow        | 5, 6
        Orange        | 7
        Red           | 8
        Red/Magenta   | 9
        Magenta       | 10
        Light Purple  | 11
        Light Yellow  | 12, 13
        Light Orange  | 14
        Light Red     | 15
        Light Magenta | 16
        White         | 17
        """
        return super()._read("COLOR")[0]
    
    def rgb(self) -> tuple[int, int, int, int]:
        """Returns the red, green, blue and white components of the detected color (0-255)."""
        return super()._read("RGB")

    def norm(self) -> tuple[int, int, int, int]:
        """Returns the normalized red, green, blue and white components of the detected color (0-255)."""
        return super()._read("NORM")
    
    def passive(self) -> tuple[int, int, int, int]:
        """Returns the red, green, blue and white components of the passively detected color, means that the sensor's LED is switched off. (0-255)."""
        return super()._read("PASSIVE")

    def raw(self) -> tuple[int, int, int, int]:
        """Returns the raw red, green, blue and white components of the detected color (0-255?)."""
        return super()._read("RAW")

    def set50HzMode(self) -> None:
        """Configures the sensor for 50Hz power mains."""
        super()._execCommand("50HZ")

    def set60HzMode(self) -> None:
        """Configures the sensor for 60Hz power mains."""
        super()._execCommand("60HZ")


class CaliColorSensor:
    """
    Stellt einen kalibrierbaren Farbsensor zur Verfügung. Die Schwarz- und Weiß-Werte werden in der Datei `/home/robot/.caliValues.json` gespeichert.
    """
    def __init__(self, port: __parameters.Port):
        """
        Argumente:
          * `port`: Die Portnummer des zu verwendenden Sensors.
        """

        if type(port) == int:
            self.baseSensor = __ev3devices.ColorSensor(__num2Port(port)) # initialisiert den unkalibrierten Sensor
            self.__port = port
        else:
            self.baseSensor = __ev3devices.ColorSensor(port)
            self.__port = __port2Num[port]


        self.reflect = 0
        self.rgbValues = [0, 0, 0]
        try:
            with open("/home/robot/.caliValues.json") as f:
                self.__values = __json.load(f)[str(self.__port)]  # Werte aus JSON-Datei holen
        except RuntimeError as e: # Wenn z.B. die JSON-Datei noch leer ist:
            self.__values = {"reflect": [1, 0], "rgb": {c: [1, 0] for c in ["red", "green", "blue"]}}
            print("Fehler beim Laden der Werte: " + str(e))
        
    
    def reflection(self) -> float:
        """
        Gibt die kalibrierte Reflexion des roten Lichts an einer Oberfläche zurück und speichert sie im Attribut `reflect`.
        """
        self.reflect = self.__values["reflect"][0] * self.baseSensor.reflection() + self.__values["reflect"][1]
        return self.reflect

    def rgb(self) -> tuple[float, float, float]:
        """
        Gibt die kalibrierten RGB-Werte des Sensors zurück und speichert sie im Attribut `rgbValues`.
        """
        rawValues = self.baseSensor.rgb()
        self.rgbValues[0] = self.__values["rgb"]["red"]  [0] * rawValues[0] + self.__values["rgb"]["red"]  [1]
        self.rgbValues[1] = self.__values["rgb"]["green"][0] * rawValues[1] + self.__values["rgb"]["green"][1]
        self.rgbValues[2] = self.__values["rgb"]["blue"] [0] * rawValues[2] + self.__values["rgb"]["blue"] [1]
        return tuple(self.rgbValues)

    
    def setReflectValues(self, black: int, white: int):
        """Kalibriert den `reflect`-Modus des Sensors. `black` darf nicht gleich `white` sein (und NEIN, das ist NICHT rassistisch gemeint!!!).
        
        Argumente:
            * `black`: Der unkalibrierte Sensorwert, wenn der Sensor auf einer schwarzen Oberfläche ist.
            * `white`: Der unkalibrierte Sensorwert, wenn der Sensor auf einer weißen Oberfläche ist.
        """

        self.__values["reflect"][0] = 100 / (white - black)             # mx + t: m
        self.__values["reflect"][1] = (-100 * black) / (white - black)  # mx + t: t

        with open("/home/robot/.caliValues.json") as f:
            alleWerte = __json.load(f)
            alleWerte[str(self.__port)] = self.__values
        with open("/home/robot/.caliValues.json", "w") as f:
            __json.dump(alleWerte, f, indent=4)

def beep(freq: float = 440.0, duration: float = 200.0, reps: int = 1) -> None:
    """Spielt einen Ton, ohne das Programm anzuhalten.
    
    Argumente:
        * `freq [Hz]`: Die Frequenz des Tons.
        * `duration [ms]`: Die Dauer des Tons.
        * `reps`: Gibt an, wie oft der Ton wiederholt wird.
    """

    __os.system("beep -f %s -l %s -r %s" % (freq, duration, reps))
