# Auto OC Voltage Measurement Script
Semi-automated script for Open Circuit Voltage Measurements of Cells for UBC Solar's Battery Pack Cell Characterization

## Equipment and Setup

1x Keithley 2110 Benchtop Multimeter
1x Cell Holders
700x Cells
1x USB A Cable

## Dependencies

- A VISA implementation on the host computer. NI-VISA is a popular one. Download it from https://www.ni.com/support/downloads/drivers/download.ni-visa.html#442805.
  - For Linux/Mac: note that only the runtime is strictly required for this program, but you can install the full suite if you wish
- PyVISA library, for interfacing with VISA-enabled instruments from Python.

## Program Setup

First time setup to run the program is as follows:

1. Install a VISA Implementation such as NI-VISA
2. Create a python virtual environment
```shell
python -m venv venv
```
3. Install python dependencies
```shell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Program Use

1. Activate virtual environment
```shell
. venv/bin/activate # Linux / Mac
venv/Scripts/activate # Windows
```
2. Make sure instruments are connected
3. Run the script
```shell
python main.py
```
4. Follow the instructions given by the program to identify the instruments, confirm the instrument identification and run the test.

The script will save all of the measurements to a new file in the `data` folder called 'voltages.csv' .

Any time the program prints an ERROR during the measurement routine, it will not save the measurement. If this occurs, make sure the problem is corrected and re-run the test on the battery cell. If a WARNING is printed, it will still save a measurement.

Don't worry about measuring the same cell twice. The program will never overwrite existing data, and a timestamp is saved with each entry of data from a run of the test.

