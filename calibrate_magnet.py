"""
A script to calibrate the magnetic field of a GMW electromagnet using a Kepco power
supply and a Lakeshore 425 gaussmeter. The script sweeps the current through the electromagnet
and records the corresponding magnetic field readings.

Author: Mecid Kocyigit
Editors:
"""

import pyvisa
import numpy as np
import time

from libraries.kepco_lib import Kepco
from libraries.gaussmeter_lib import Lakeshore425

SETTLE_TIME = 1.0 # Wait amount in seconds for each current step

RAMP_STEP = 0.5 # dI per step in Amperes, used for ramping current
RAMP_DELAY = 0.2 # dT per step in seconds, used for ramping current

FIELD_READINGS = 10 # Number of field measurements to average for each current step

if __name__ == "__main__":
    # Initialize the power supply and gaussmeter
    kepco = Kepco(GPIB_channel=1)
    gaussmeter = Lakeshore425(resource="ASRL1::INSTR")

    try:
        # Set the gaussmeter to DC mode and set units, then auto-range
        gaussmeter.dcMode()
        gaussmeter.setUnits('T')
        gaussmeter.autoRange()

        # Set the Kepco to current mode
        kepco.currentMode()

        # Define the current range for the sweep, max current (16 A) is used here
        current_range = np.linspace(-16, 16, 41)

        readings = []

        print("Ramping to starting current...")
        kepco.rampCurrent(kepco.measureCurrent(), current_range[0], RAMP_STEP, RAMP_DELAY)

        print("Starting current sweep...")
        for current in current_range:
            kepco.rampCurrent(kepco.measureCurrent(), current, RAMP_STEP, RAMP_DELAY)
            time.sleep(SETTLE_TIME)  # Wait for the system to stabilize

            # Do numerous readings and average them to reduce noise
            field_readings = []
            for _ in range(FIELD_READINGS):
                field_readings.append(float(gaussmeter.measureField()))
                time.sleep(0.1)

            field_reading = np.mean(field_readings)
            readings.append((current, field_reading))

            print(f"Current: {current:.2f} A, Magnetic Field: {field_reading:.6f} mT")

        print("Current sweep completed.")

        # Save the readings to a txt file
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"cal_{timestamp}.txt"
        np.savetxt(
            filename,
            readings,
            header="Current (A)\tField (T)",
            fmt="%.6f",
            delimiter="\t",
        )
        print(f"Saved readings to {filename}")

    finally:
        # Ramp the current back to 0 A and close the connections
        try:
            print("Ramping current back to 0 A...")
            kepco.rampCurrent(kepco.measureCurrent(), 0, RAMP_STEP, RAMP_DELAY)
        except Exception as e:
            print(f"WARNING: failed to ramp current to 0 A: {e}")

        try:
            kepco.powerOff()
        except Exception as e:
            print(f"WARNING: failed to close Kepco connection: {e}")

        try:
            gaussmeter.close()
        except Exception as e:
            print(f"WARNING: failed to close gaussmeter connection: {e}")