import pyvisa
import numpy as np
import time

from libraries.kepco_lib import Kepco
from libraries.stanford_lib import SR830
from libraries.gaussmeter_lib import Lakeshore425
from libraries.keysight_lib import N5183B

if __name__ == "__main__":
    start_time = time.time()

    # Get the instrument instances and initialize/reset them
    kepco_inst = Kepco(GPIB_address=1)
    kepco_inst.currentMode()
    kepco_inst.outputOn()

    sr830_inst = SR830(GPIB_address=8)
    sr830_inst.reset()
    sr830_inst.sensitivityWrite(26) # Set max sensitivity to protect the instrument

    gaussmeter_inst = Lakeshore425(COM_address=3)
    gaussmeter_inst.dcMode()
    gaussmeter_inst.setUnits('T')
    gaussmeter_inst.autoRange()

    mxg_inst = N5183B(GPIB_address=3)
    mxg_inst.reset()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    try:
        # Perform the FMR measurement
        # (Insert your FMR measurement code here)

        # Example: Set frequency and measure response
        frequency = 10e9  # 10 GHz
        mxg_inst.frequencyWrite(frequency)
        time.sleep(1)  # Wait for the frequency to stabilize

        # Measure the magnetic field
        field = gaussmeter_inst.measureField()
        print(f"Measured Magnetic Field: {field} T")

    finally:
        # Do some cleanup and close the instruments
        kepco_inst.outputOff()
        kepco_inst.close()
        
        sr830_inst.setSensitivityValue(26)  # Reset sensitivity to max
        sr830_inst.amplitudeWrite(0.004)    # Set amplitude to 4 mV, minimum value. 
                                            # This instrument doesn't have an "output off" command
        sr830_inst.close()

        gaussmeter_inst.close()

        mxg_inst.outputOff() # Turn off the output of the signal generator
        mxg_inst.close()

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Total elapsed time: {elapsed_time:.2f} seconds")