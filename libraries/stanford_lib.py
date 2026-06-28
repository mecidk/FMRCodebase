"""
A library for controlling the Stanford Research Systems SR830 lock-in amplifier.

Author: Mecid Kocyigit
Editors: 
"""

import pyvisa
from pyvisa.constants import StopBits, Parity
import time
import numpy as np

class SR830():

    # Some lookup tables
    # Full scale sensitivity in volts
    SENSITIVITY = [
        2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9,
        1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6,
        1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1.0
    ]
 
    # Time constant in seconds
    TIME_CONSTANT = [
        10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3, 100e-3, 300e-3,
        1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1e3, 3e3, 10e3, 30e3
    ]
 
    # Low-pass filter slope in dB/oct
    FILTER_SLOPE = [6, 12, 18, 24]
 
    # Sample rate in Hz (index 14 == external trigger)
    SAMPLE_RATE = [
        0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512
    ]

    
    def __init__(self, COM_port = 8):
        self.COM_port = COM_port
        self.rm = pyvisa.ResourceManager()
        self.sr830_instance = self.rm.open_resource(f'ASRL{self.COM_port}::INSTR', 
                                                    read_termination='\r', 
                                                    write_termination='\n',
                                                    baud_rate=4800,
                                                    data_bits=8,
                                                    stop_bits=StopBits.one,
                                                    parity=Parity.odd)
        
        self.sr830_instance.timeout = 5000 # Change the default timeout to 5 seconds (5000 ms) to accommodate longer response times
        
        self.sr830_instance.write('OUTX 0')  # Required at the beginning of every program
        print(self.sr830_instance.query('*IDN?'))  # Query the instrument identification
    
    def query(self, command):
        return self.sr830_instance.query(command).strip()  # Strip whitespace from the response
    
    def write(self, command):
        self.sr830_instance.write(command)

    def reset(self):
        self.sr830_instance.write('*RST')  # Reset the instrument to default settings
        time.sleep(1)  # Wait for a second to ensure the reset is complete
        print("SR830 has been reset to default settings.")

    def close(self):
        try:
            self.sr830_instance.close()
        finally:
            self.rm.close()

    def measure(self):
        response = self.query('SNAP? 1,2') # Query the X and Y values simultaneously
        x_value, y_value = (float(v) for v in response.split(','))
        return np.array([x_value, y_value])
    
    def measure_r_theta(self):
        response = self.query('SNAP? 3,4') # Query the R and Theta values simultaneously
        r_value, theta_value = (float(v) for v in response.split(','))
        return np.array([r_value, theta_value])
    
    def read_output(self, which='X'):
        # Used to read a single output value (X, Y, R, or THETA)
        codes = {'X': 1, 'Y': 2, 'R': 3, 'THETA': 4}
        code = codes[str(which).upper()]
        return float(self.query(f'OUTP? {code}'))
    
    def phaseWrite(self, phase_value):
        # Set the reference phase shift (degrees, -360.00 to 729.99, wrapped to +/-180)
        if not -360.0 <= phase_value <= 729.99:
            raise ValueError("Phase must be between -360.00 and 729.99 degrees.")
        self.sr830_instance.write(f'PHAS {phase_value}')
        print(f"Phase set to {phase_value}.")
 
    def phaseRead(self):
        # Query the reference phase shift in degrees
        return float(self.query('PHAS?'))
 
    def referenceSourceWrite(self, internal=True):
        # Select internal (True) or external (False) reference
        self.sr830_instance.write(f'FMOD {1 if internal else 0}')
        print(f"Reference source set to {'internal' if internal else 'external'}.")
 
    def frequencyWrite(self, frequency_hz):
        # Set internal oscillator frequency in Hz (0.001 to 102000), only allowed when the reference source is internal
        if not 0.001 <= frequency_hz <= 102000:
            raise ValueError("Frequency must be between 0.001 and 102000 Hz.")
        self.sr830_instance.write(f'FREQ {frequency_hz}')
        print(f"Reference frequency set to {frequency_hz} Hz.")
 
    def frequencyRead(self):
        # Query the internal oscillator frequency in Hz
        return float(self.query('FREQ?'))
 
    def harmonicWrite(self, harmonic):
        # Set the detection harmonic (1 to 19999, limited by n*f<=102kHz)
        self.sr830_instance.write(f'HARM {int(harmonic)}')
        print(f"Detection harmonic set to {int(harmonic)}.")
 
    def harmonicRead(self):
        # Query the detection harmonic
        return int(float(self.query('HARM?')))
 
    def amplitudeWrite(self, amplitude_volts):
        # Set the internal sine output amplitude in Volts (0.004 to 5.000)
        if not 0.004 <= amplitude_volts <= 5.0:
            raise ValueError("Sine amplitude must be between 0.004 and 5.000 V.")
        self.sr830_instance.write(f'SLVL {amplitude_volts}')
        print(f"Sine output amplitude set to {amplitude_volts} V.")

    def amplitudeRead(self):
        # Query the internal sine output amplitude in Volts
        return float(self.query('SLVL?'))
    
    def inputConfigWrite(self, config):
        # Input configuration: 'A', 'A-B', 'I1M' (I 1 MOhm) or 'I100M' (I 100 MOhm)
        mapping = {'A': 0, 'A-B': 1, 'I1M': 2, 'I100M': 3}
        self.sr830_instance.write(f'ISRC {mapping[config.upper()]}')
        print(f"Input configuration set to {config}.")
 
    def inputCouplingWrite(self, coupling='AC'):
        # Input coupling: 'AC' or 'DC'
        self.sr830_instance.write(f'ICPL {0 if coupling.upper() == "AC" else 1}')
        print(f"Input coupling set to {coupling}.")
 
    def inputGroundingWrite(self, ground=True):
        # Input shield grounding: True=Ground, False=Float
        self.sr830_instance.write(f'IGND {1 if ground else 0}')
        print(f"Input shield set to {'Ground' if ground else 'Float'}.")

    def sensitivityWrite(self, sensitivity_index):
        # Set sensitivity by index (0-26). See SENSITIVITY table
        if not 0 <= int(sensitivity_index) <= 26:
            raise ValueError("Sensitivity index must be between 0 and 26.")
        self.sr830_instance.write(f'SENS {int(sensitivity_index)}')
        print(f"Sensitivity set to index {sensitivity_index} " 
              f"({self.SENSITIVITY[int(sensitivity_index)]} V).")
 
    def sensitivityRead(self):
        # Return the sensitivity index (integer 0-26)
        return int(float(self.query('SENS?')))
 
    def sensitivityValue(self):
        # Return the full-scale sensitivity in Volts (or Amps for current input)
        return self.SENSITIVITY[self.sensitivityRead()]
 
    def setSensitivityValue(self, value_volts):
        # Set sensitivity to the smallest range >= value_volts (best resolution)
        for index, fs in enumerate(self.SENSITIVITY):
            if fs >= value_volts:
                self.sensitivityWrite(index)
                return index
        # value exceeds full scale of the largest range -> use the largest
        self.sensitivityWrite(len(self.SENSITIVITY) - 1)
        return len(self.SENSITIVITY) - 1
 
    def timeConstantWrite(self, time_constant_index):
        # Set time constant by index (0-19). See TIME_CONSTANT table
        if not 0 <= int(time_constant_index) <= 19:
            raise ValueError("Time constant index must be between 0 and 19.")
        self.sr830_instance.write(f'OFLT {int(time_constant_index)}')
        print(f"Time constant set to index {time_constant_index} "
              f"({self.TIME_CONSTANT[int(time_constant_index)]} s).")
 
    def timeConstantRead(self):
        # Return the time constant index (integer 0-19)
        return int(float(self.query('OFLT?')))
 
    def timeConstantValue(self):
        # Return the time constant in seconds
        return self.TIME_CONSTANT[self.timeConstantRead()]
 
    def filterSlopeWrite(self, slope_db_oct):
        # Set low-pass filter slope: 6, 12, 18 or 24 dB/oct.
        index = self.FILTER_SLOPE.index(slope_db_oct)
        self.sr830_instance.write(f'OFSL {index}')
        print(f"Filter slope set to {slope_db_oct} dB/oct.")
 
    def reserveModeWrite(self, mode='normal'):
        # Reserve mode: 'high', 'normal' or 'low' (low noise)
        mapping = {'HIGH': 0, 'NORMAL': 1, 'LOW': 2}
        self.sr830_instance.write(f'RMOD {mapping[mode.upper()]}')
        print(f"Reserve mode set to {mode}.")
 
    def syncFilterWrite(self, on=False):
        # Synchronous filter on/off (active only below 200 Hz detection).
        self.sr830_instance.write(f'SYNC {1 if on else 0}')
        print(f"Synchronous filter {'on' if on else 'off'}.")

    def autoGain(self):
        # Auto gain. Does nothing if the time constant exceeds 1 s. Blocks the lock-in until finished.
        self.sr830_instance.write('AGAN')
        self._wait_for_idle()
        print("Auto gain completed.")
 
    def autoReserve(self):
        # Auto reserve. Blocks until finished.
        self.sr830_instance.write('ARSV')
        self._wait_for_idle()
        print("Auto reserve completed.")
 
    def autoPhase(self):
        # Auto phase. Waits for ~10 time constants before returning. Blocks the lock-in until finished. Do NOT send APHS again before the outputs have settled.
        self.sr830_instance.write('APHS')
        settle = 10 * self.timeConstantValue()
        time.sleep(min(max(settle, 1.0), 60.0))  # clamp to [1 s, 60 s]
        print("Auto phase completed.")
 
    def autoOffset(self, quantity='X'):
        # Auto-offset X, Y or R to zero
        codes = {'X': 1, 'Y': 2, 'R': 3}
        self.sr830_instance.write(f'AOFF {codes[quantity.upper()]}')
        print(f"Auto offset applied to {quantity}.")

    def _wait_for_idle(self, poll=0.05, timeout=30.0):
        # Block until the 'no command in progress' bit (serial-poll bit 1) is set
        deadline = time.time() + timeout
        while time.time() < deadline:
            if int(float(self.query('*STB? 1'))) == 1:
                return
            time.sleep(poll)
        raise TimeoutError("Timed out waiting for the SR830 to finish a command.")
 
    def errorStatus(self):
        # Read and clear the error status byte (decimal 0-255)
        return int(float(self.query('ERRS?')))