"""
A library for controlling the Kepco power supply of the GMW electromagnet.
It uses GPIB communication via pyvisa.

Author: Mecid Kocyigit
Editors: 
"""

import pyvisa
import time
import numpy as np
import math

class Kepco():

    def __init__(self, GPIB_channel = 1):
        self.GPIB_channel = GPIB_channel
        self.rm = pyvisa.ResourceManager()

        self.voltmode = 0 # Initialize mode flags
        self.currmode = 0

        self.kepco_instance = self.rm.open_resource(f'GPIB0::{self.GPIB_channel}::INSTR', 
                                                    read_termination='\n', 
                                                    write_termination='\n')
        
        self.kepco_instance.write("*RST; STATUS:PRESET; *CLS") # Reset the instrument to a known state

        self.kepco_instance.write("CURR:RANG 1") # Set current range to maximum, +- 20 A
        self.kepco_instance.write("VOLT:RANG 1") # Set voltage range to maximum, +- 20 V

        print(self.kepco_instance.query('*IDN?'))  # Query the instrument identification

    def voltageMode(self):
        # Voltage mode: the output voltage is programmed, current is the maximum limit
        self.kepco_instance.write("VOLT 0")

        self.voltmode = 1
        self.currmode = 0

        self.kepco_instance.write("FUNC:MODE VOLT")
        self.kepco_instance.write("CURR 20")

    def currentMode(self):
        # Current mode: the output current is programmed, voltage is the maximum limit
        self.kepco_instance.write("CURR 0")

        self.currmode = 1
        self.voltmode = 0

        self.kepco_instance.write("FUNC:MODE CURR")
        self.kepco_instance.write("VOLT 20")

    def setVoltage(self, voltage):
        # Set the output voltage
        self.kepco_voltage = float(voltage)

        if abs(self.kepco_voltage) > 20.0:
            # If the requested voltage exceeds the maximum limit, clamp it to the maximum value
            self.kepco_voltage = math.copysign(20.0, self.kepco_voltage)
            print(f"Requested voltage exceeds +/- 20 V. Clamping to {self.kepco_voltage} V.")

        self.kepco_instance.write(f"VOLT {self.kepco_voltage}")
        print(f"Set voltage to {self.kepco_voltage} V")

    def setCurrent(self, current):
        # Set the output current
        self.kepco_current = float(current)

        if abs(self.kepco_current) > 20.0:
            # If the requested current exceeds the maximum limit, clamp it to the maximum value
            self.kepco_current = math.copysign(20.0, self.kepco_current)
            print(f"Requested current exceeds +/- 20 A; clamping to {self.kepco_current} A.")

        self.kepco_instance.write(f"CURR {self.kepco_current}")
        print(f"Set current to {self.kepco_current} A")

    def measureCurrent(self):
        # Return the measured output current in amperes
        return float(self.kepco_instance.query("MEAS:CURR?"))

    def measureVoltage(self):
        # Return the measured output voltage in volts
        return float(self.kepco_instance.query("MEAS:VOLT?"))

    def getCurrent(self):
        # Return the programmed current set point, NOT the real measured current
        return float(self.kepco_instance.query("CURR?"))

    def checkErrors(self):
        # Drain and return the instrument error queue
        errors = []

        while True:
            err = self.kepco_instance.query("SYST:ERR?").strip()
            errors.append(err)
            code = err.split(",")[0].strip()
            if code in ("0", "+0"): # "0,..." or "+0,..." means the queue is empty
                break

        return errors
    
    def powerOn(self):
        # Turn on the output
        self.kepco_instance.write("OUTP ON")

    def powerOff(self):
        # Ramp down the current or voltage to zero and then turn off the output
        try:
            if self.currmode == 1:
                present = self.measureCurrent()
                self.rampCurrent(present, 0.0, 0.1, 0.1)
            if self.voltmode == 1:
                self.setVoltage(0)

            time.sleep(5) # Wait for the output to settle
            residual = abs(self.measureCurrent()) # Check if there is any residual current flowing before turning off the output
            if residual > 0.02:
                print(f"WARNING: {residual:.3f} A still flowing before output off.")
        finally:
            self.kepco_instance.write("OUTP OFF")

    def rampCurrent(self, I1, I2, dI, dT):
        # Ramp the output current from I1 to I2 in Amperes. dI is the step size. 
        # dT is the dwell time between steps in secs. The end point I2 is always reached exactly.
        I1 = float(I1)
        I2 = float(I2)
        dI = abs(float(dI))
        dT = float(dT)
        if dI == 0:
            raise ValueError("Step size dI must be non-zero.")

        current = I1

        # set the direction of sweep
        if I2 >= I1:
            condition = lambda c: c <= I2
            step = dI
        else:
            condition = lambda c: c >= I2
            step = -dI

        while condition(current):
            self.setCurrent(round(current, 3))
            if current == I1:
                time.sleep(3) # Extra dwell after the first point
            time.sleep(dT)
            current += step

        # ensure the final current value I2 is set if not exactly on the last step.
        if (step > 0 and current - step < I2) or (step < 0 and current - step > I2):
            self.setCurrent(round(I2, 3))

        time.sleep(dT)