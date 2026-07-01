"""
A library for controlling the Keysight N5183B MXG analog signal generator.
It uses GPIB communication via pyvisa.

Author: Mecid Kocyigit
Editors:
"""

import pyvisa
import time

class N5183B():

    def __init__(self, GPIB_address=3):
        self.GPIB_address = GPIB_address
        self.rm = pyvisa.ResourceManager()

        self.mxg_instance = self.rm.open_resource(f'GPIB0::{self.GPIB_address}::INSTR',
                                                  read_termination='\n',
                                                  write_termination='\n'
                                                  )

        self.mxg_instance.timeout = 10000  # Extra long timeout

        print(self.mxg_instance.query('*IDN?'))  # Query the instrument identification

    def query(self, command):
        return self.mxg_instance.query(command).strip()

    def write(self, command):
        self.mxg_instance.write(command)

    def reset(self):
        self.mxg_instance.write('*RST')
        self.mxg_instance.write('*CLS')
        self.waitForComplete()
        print("N5183B has been reset to default settings.")

    def close(self):
        try:
            self.mxg_instance.close()
        finally:
            self.rm.close()

    def waitForComplete(self):
        # Block until the instrument finishes doing stuff
        self.mxg_instance.query('*OPC?')

    def errorStatus(self):
        # Read the next error from the queue
        return self.query(':SYSTem:ERRor?')

    def checkErrors(self):
        # Drain the error queue and return a list of errors
        errors = []
        while True:
            err = self.errorStatus()
            if err.startswith('+0') or err.startswith('0,'):
                break
            errors.append(err)
        return errors

    def frequencyWrite(self, frequency_hz):
        # Set frequency in Hz, 9e3 to 40e9 Hz
        self.mxg_instance.write(f':FREQuency:FIXed {frequency_hz}')
        print(f"Frequency set to {frequency_hz} Hz.")

    def frequencyRead(self):
        return float(self.query(':FREQuency:FIXed?'))

    def powerWrite(self, power_dbm):
        # Set output amplitude in dBm
        self.mxg_instance.write(f':POWer:AMPLitude {power_dbm} dBm')
        print(f"Power set to {power_dbm} dBm.")

    def powerRead(self):
        return float(self.query(':POWer:AMPLitude?'))

    def outputOn(self):
        # Turn the RF output on
        self.mxg_instance.write(':OUTPut:STATe 1')
        print("RF output on.")

    def outputOff(self):
        # Turn the RF output off
        self.mxg_instance.write(':OUTPut:STATe 0')
        print("RF output off.")

    def outputRead(self):
        return bool(int(self.query(':OUTPut:STATe?')))

    def modulationWrite(self, on=True):
        # Master modulation on/off, applies to all modulation schemes
        self.mxg_instance.write(f':OUTPut:MODulation:STATe {1 if on else 0}')
        print(f"Modulation {'on' if on else 'off'}.")

    def modulationRead(self):
        return bool(int(self.query(':OUTPut:MODulation:STATe?')))
    
    def frequencyModeWrite(self, mode='CW'):
        # 'CW' (fixed), 'LIST' or 'SWEep'
        self.mxg_instance.write(f':FREQuency:MODE {mode.upper()}')
        print(f"Frequency mode set to {mode}.")

    def sweepConfig(self, start_hz, stop_hz, points, dwell_s):
        # Configure a step sweep over [start, stop]
        self.mxg_instance.write(f':FREQuency:STARt {start_hz}')
        self.mxg_instance.write(f':FREQuency:STOP {stop_hz}')
        self.mxg_instance.write(f':SWEep:POINts {int(points)}')
        self.mxg_instance.write(f':SWEep:DWELl {dwell_s}')

        print(f"Sweep set: {start_hz} to {stop_hz} Hz, {int(points)} points, {dwell_s} s dwell.")

    # ------- Amplitude modulation functions
    def amWrite(self, on=True):
        self.mxg_instance.write(f':AM:STATe {1 if on else 0}')
        print(f"AM {'on' if on else 'off'}.")

    def amRead(self):
        return bool(int(self.query(':AM:STATe?')))

    def amDepthWrite(self, depth_percent):
        # Linear AM depth in percent (0 to 100)
        if not 0.0 <= depth_percent <= 100.0:
            raise ValueError("AM depth must be between 0 and 100 percent.")
        self.mxg_instance.write(f':AM:DEPTh:LINear {depth_percent}')
        print(f"AM depth set to {depth_percent} %.")

    def amDepthRead(self):
        return float(self.query(':AM:DEPTh:LINear?'))

    def amFrequencyWrite(self, frequency_hz):
        # Internal AM rate in Hz
        self.mxg_instance.write(f':AM:INTernal:FREQuency {frequency_hz}')
        print(f"AM rate set to {frequency_hz} Hz.")

    def amFrequencyRead(self):
        return float(self.query(':AM:INTernal:FREQuency?'))

    def amSourceWrite(self, internal=True):
        # Select internal or external AM source
        self.mxg_instance.write(f':AM:SOURce {"INT" if internal else "EXT"}')
        print(f"AM source set to {'internal' if internal else 'external'}.")

    # ------- Frequency modulation functions
    def fmWrite(self, on=True):
        self.mxg_instance.write(f':FM:STATe {1 if on else 0}')
        print(f"FM {'on' if on else 'off'}.")

    def fmRead(self):
        return bool(int(self.query(':FM:STATe?')))

    def fmDeviationWrite(self, deviation_hz):
        # FM peak deviation in Hz
        self.mxg_instance.write(f':FM:DEViation {deviation_hz}')
        print(f"FM deviation set to {deviation_hz} Hz.")

    def fmDeviationRead(self):
        return float(self.query(':FM:DEViation?'))

    def fmFrequencyWrite(self, frequency_hz):
        # Internal FM rate in Hz
        self.mxg_instance.write(f':FM:INTernal:FREQuency {frequency_hz}')
        print(f"FM rate set to {frequency_hz} Hz.")

    def fmFrequencyRead(self):
        return float(self.query(':FM:INTernal:FREQuency?'))

    # ------ Phase modulation functions
    def pmWrite(self, on=True):
        self.mxg_instance.write(f':PM:STATe {1 if on else 0}')
        print(f"PM {'on' if on else 'off'}.")

    def pmRead(self):
        return bool(int(self.query(':PM:STATe?')))

    def pmDeviationWrite(self, deviation_rad):
        # PM peak deviation in radians
        self.mxg_instance.write(f':PM:DEViation {deviation_rad}')
        print(f"PM deviation set to {deviation_rad} rad.")

    def pmDeviationRead(self):
        return float(self.query(':PM:DEViation?'))

    # ----- Pulse modulation functions
    def pulseWrite(self, on=True):
        self.mxg_instance.write(f':PULM:STATe {1 if on else 0}')
        print(f"Pulse modulation {'on' if on else 'off'}.")

    def pulseRead(self):
        return bool(int(self.query(':PULM:STATe?')))

    def pulseSourceWrite(self, internal=True):
        # Select internal or external pulse source
        self.mxg_instance.write(f':PULM:SOURce {"INT" if internal else "EXT"}')
        print(f"Pulse source set to {'internal' if internal else 'external'}.")

    def pulsePeriodWrite(self, period_s):
        # Internal pulse period in seconds
        self.mxg_instance.write(f':PULM:INTernal:PERiod {period_s}')
        print(f"Pulse period set to {period_s} s.")

    def pulseWidthWrite(self, width_s):
        # Internal pulse width in seconds
        self.mxg_instance.write(f':PULM:INTernal:PWIDth {width_s}')
        print(f"Pulse width set to {width_s} s.")