# RandomPybricksTools

These are the working parts of what I've been coding for ev3dev and pybricks.

## Installation

- If your Brick is connected to the internet:
    - run `git clone github.com/Fabs37/RandomPybricksTools` via SSH on your brick.
- Else:
    - Download this repo as shown above to your computer.
    - Upload it to the brick (e.g. via VSCode's ev3dev extension).
- On the brick, run `setup.sh` in the repo. It will create a file which stores the calibration values (`~/.caliValues.json`).
- If you want, you can move or symlink the single parts wherever you want them, e.g. `lights` to `/usr/bin` or `robAPI` to `/usr/lib/pybricks-micropython`.

## Content

### General: Calibration

Calibration of color sensors is one of the main goals of this project. You can calibrate the `reflection` / `COL-REFLECT` mode of the EV3 Color Sensor and read the calibrated values via the [`CaliColorSensor` class](/robAPI/sensors.py#L114) and the [portView UI](#portviewpy).

### [robAPI](/robAPI/)

This Python module contains two submodules:

- [`sensors.py`](/robAPI/sensors.py)
    - Contains:
        - The [calibrated color sensor](/robAPI/sensors.py#L114)
        - A [driver](/robAPI/sensors.py#L60) for the HiTechnic NXT Color Sensor V2
        - A [shortcut function](/robAPI/sensors.py#L177) for `pybricks.hubs.EV3Brick.speaker.beep()`
- [`lineTools.py`](/robAPI/lineTools.py)
    - This module is designed for robots that have
        - one (calibrated) EV3 Color Sensor in front of their wheels and
        - one color sensor on each side in order to detect line crossings.
    - It contains
        - a [class for line following](/robAPI/lineTools.py#L11) (its methods `nthTurningLeft` and `nthTurningRight` are *not yet implemented* and will be different for each robot) and
        - a function that [counts the lines](/robAPI/lineTools.py#L199) that pass the robot.

The API documentation is (currently) only available as docstrings and is partly in German.



### [lights](/lights)

A command line program to control the single status LEDs of the brick. (It doesn't work if a pybricks script is being executed, this is not a bug.)

See `lights --help` for more info.

### [lsev3devices](/lsev3devices)

A command line tool that lists the sensors and motors detected by the brick, their driver name and the port to which they are connected.

### [motorControl.py](/motorControl.py)

A GUI program that controls the motors connected to the brick via its buttons.

- Left / right button: Change the selected motor.
- Up / down button: Run the selected motor clockwise or counterclockwise.
- Middle button: Change the speed of the selected motor. The speed is stored for every single motor seperately.
- Middle button (hold): Change the direction of the selected motor.

### [portView.py](/portView.py)

An EV3 firmware-like GUI program to view the values of the motors and sensors connected to the brick.

- Left / right / up / down: Change the selected motor / sensor.
- Middle button:
    - When a motor is selected, reset its position.
    - When a sensor is selected, open its mode/command menu. Here, you can select the different modes and execute commands provided by the [sensor's sysfs driver](https://docs.ev3dev.org/projects/lego-linux-drivers/en/ev3dev-stretch/sensor_data.html).

Calibrated values for the EV3 Color sensor are shown when in `COL-REFLECT` mode. It can be calibrated by selecting `Additional functions > Calib. COL-REFLECT` in the mode/command menu.

Via [`portView.conf.json`](/portView.conf.json) (which should be at `~/.portView.conf.json` or in the same directory as `portView.py`), you can configure this program. The sensor modes that are disabled in the default settings file aren't working properly[^1]. The calibration of the EV3 Color Sensor's RGB mode is not yet fully implemented (since I don't think you can use this mode sensibly even if the calibration works).



[^1]: e.g. https://docs.ev3dev.org/projects/lego-linux-drivers/en/ev3dev-stretch/sensor_data.html#lego-ev3-color-mode5