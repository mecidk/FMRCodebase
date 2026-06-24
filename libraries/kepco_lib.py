"""
A library for controlling the Kepco power supply of the GMW electromagnet via GPIB.

Author: Mecid Kocyigit
Editors: 
"""

import pyvisa

class Kepco():

    def __init__(self, GPIB_channel = 1):
        self.GPIB_channel = GPIB_channel
        self.rm = pyvisa.ResourceManager() # 
        self.kepco_instance = self.rm.open_resource(f'GPIB0::{self.GPIB_channel}::INSTR', 
                                                    read_termination='\n', 
                                                    write_termination='\n')