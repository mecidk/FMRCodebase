"""
A library for controlling the Kepco power supply of the GMW electromagnet via GPIB.

Author: Mecid Kocyigit
Editors: 
"""

import pyvisa
import time
import numpy as np

class Kepco():

    def __init__(self, GPIB_channel = 1):
        self.GPIB_channel = GPIB_channel
        self.rm = pyvisa.ResourceManager()
        self.voltmode = 0
        self.currmode = 0
        self.kepco_instance = self.rm.open_resource(f'GPIB0::{self.GPIB_channel}::INSTR', 
                                                    read_termination='\n', 
                                                    write_termination='\n')
        
        self.kepco_inst.write("*RST; STATUS:PRESET; *CLS") # Reset the instrument to a known state

        self.kepco_inst.write("CURR:RANG 1") # Set current range to maximum, +- 20 A
        self.kepco_inst.write("VOLT:RANG 1") # Set voltage range to maximum, +- 20 V

        print(self.kepco_instance.query('*IDN?'))  # Query the instrument identification

    def mode_voltage(self):
        """Voltage mode: the output voltage is programmed, current is the limit."""
        self.kepco_inst.write("VOLT 0")
        self.voltmode = 1
        self.currmode = 0
        self.kepco_inst.write("FUNC:MODE VOLT")
        self.kepco_inst.write("CURR {curr}".format(curr=self.i_max))

    def mode_current(self):
        """Current mode: the output current is programmed, voltage is the limit.

        This is the usual mode for driving an electromagnet, since the field
        tracks the current.  The voltage limit is set to v_max so the supply
        has full compliance headroom to push current through the inductor
        during ramps (V = L * dI/dt).
        """
        self.kepco_inst.write("CURR 0")
        self.currmode = 1
        self.voltmode = 0
        self.kepco_inst.write("FUNC:MODE CURR")
        self.kepco_inst.write("VOLT {volt}".format(volt=self.v_max))