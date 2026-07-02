"""
A library for controlling the LakeShore Model 425 gaussmeter.
It uses USB communication via pyvisa.

Author: Mecid Kocyigit
Editors: 
"""

import pyvisa
from pyvisa.constants import Parity, StopBits
import time

class Lakeshore425():

    def __init__(self, COM_address = 3):
        self.COM_address = COM_address
        self.rm = pyvisa.ResourceManager()

        self.mode = "DC" # Initialize mode flag

        self.gauss_instance = self.rm.open_resource(f'ASRL{self.COM_address}::INSTR',
                                            read_termination='\n',
                                            write_termination='\n',
                                            baud_rate=57600,
                                            data_bits=7,
                                            parity=Parity.odd,
                                            stop_bits=StopBits.one)

        self.gauss_instance.write("*CLS") # Clear the interface to a known state

        print(self.gauss_instance.query('*IDN?'))  # Query the instrument identification

    def setUnits(self, units):
        # Set the field display units: 'G', 'T', 'Oe', or 'A/m'
        codes = {"G": 1, "T": 2, "Oe": 3, "A/m": 4}
        if units not in codes:
            print(f"Unknown units '{units}'. Use one of {list(codes)}.")
            return

        self.gauss_instance.write(f"UNIT {codes[units]}")
        print(f"Set units to {units}.")

    def dcMode(self, filter_on = True):
        # DC mode measures static or slowly changing fields
        self.mode = "DC"

        # Moving filter is on by default, band is ignored in DC
        self.gauss_instance.write(f"RDGMODE 1,{int(bool(filter_on))},2")
        print("Set DC mode.")

    def rmsMode(self, wideband = False):
        # RMS mode measures periodic AC fields
        # Narrow band reaches 400 Hz and wide band reaches 10 kHz with more noise
        self.mode = "RMS"

        band = 1 if wideband else 2 # 1 = wide, 2 = narrow
        self.gauss_instance.write(f"RDGMODE 2,1,{band}")
        print(f"Set RMS mode ({'wide' if wideband else 'narrow'} band).")

    def setRange(self, rng):
        # Manually set the field range, 1 (lowest) to 4 (highest)
        rng = int(rng)
        if rng < 1 or rng > 4:
            print("Range must be 1-4.")
            return

        self.gauss_instance.write("AUTO 0") # Manual range turns autorange off
        self.gauss_instance.write(f"RANGE {rng}")
        print(f"Set range to {rng}.")

    def autoRange(self):
        # Automatically select the range
        self.gauss_instance.write("AUTO 1")
        print("Autorange on.")

    def zeroProbe(self):
        # Null the probe zero offset, needs a zero gauss chamber
        self.gauss_instance.write("ZPROBE")
        print("Zeroing probe...")

    def clearZero(self):
        # Discard the stored zero probe offsets
        self.gauss_instance.write("ZCLEAR")
        print("Cleared probe zero offsets")

    def measureField(self):
        # Return the present field reading in the active units
        return float(self.gauss_instance.query("RDGFIELD?"))

    def maxHold(self, on = True):
        # Turn the max hold capture on or off
        self.gauss_instance.write(f"MXHOLD {int(bool(on))}")

    def getMax(self):
        # Return the captured max hold reading
        return float(self.gauss_instance.query("RDGMX?"))

    def maxReset(self):
        # Reset the max hold value to the present reading
        self.gauss_instance.write("MXRST")

    def relativeMode(self, on = True):
        # Relative mode subtracts the relative setpoint from the reading
        # The setpoint is the current reading when this command is called
        self.gauss_instance.write(f"REL {int(bool(on))}")

    def getRelative(self):
        # Return the relative reading (field minus setpoint)
        return float(self.gauss_instance.query("RDGREL?"))

    def setRelativeSetpoint(self, setpoint):
        # Manually set the relative setpoint, in the active units
        self.gauss_instance.write(f"RELSP {float(setpoint)}")
        print(f"Set relative setpoint to {float(setpoint)}")

    def probeZeroed(self):
        # Return true when a zero probe operation has completed (status bit 7)
        status = int(self.gauss_instance.query("OPST?"))
        return bool(status & 128)

    def checkStatus(self):
        # Decode the operational status byte and return the flags
        status = int(self.gauss_instance.query("OPST?"))
        flags = {1: "no probe", 2: "field overload", 4: "new reading",
                 8: "alarm", 16: "invalid probe", 64: "calibration error",
                 128: "zero probe done"}
        return [name for bit, name in flags.items() if status & bit]

    def lock(self):
        # Lock the front panel keypad
        self.gauss_instance.write("LOCK 1")

    def unlock(self):
        # Unlock the front panel keypad
        self.gauss_instance.write("LOCK 0")

    def factoryReset(self):
        # Reset all configuration values to factory defaults
        self.gauss_instance.write("DFLT 99")
        print("Reset to factory defaults")

    def close(self):
        try:
            self.gauss_instance.close()
        finally:
            self.rm.close()