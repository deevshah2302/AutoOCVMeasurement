# Automatic Cells OC Voltage Testing Script
#
# Equipment:
# 1x Keithley Digital Multimeter (Benchtop)

import os
from datetime import datetime
from time import sleep
import pyvisa

# ---------------------------- User‑adjustable constants ----------------------------
DC_MEAS_AVERAGE_COUNT = 5  # Number of readings averaged by the DMM’s internal filter
TOTAL_CELLS = 700          # Highest cell index accepted by the logger

# ----------------------------------Constants--------------------------------------
INFO_TEXT = (
    "=" * 79
    + "\n   Battery Cell Open‑Circuit Voltage Logger\n"
    + "=" * 79
    + "\nThis program measures and records the DC voltage of individual cells.\n"
    + "Make sure the DMM leads are connected directly across the cell under test.\n"
    + "Enter the cell number when prompted or ‘c’ to quit.\n"
)

# ---------------------------- Global variables ----------------------------
cell_numbers = [] # All the cell numbers recorded so far. A list of integers

# ---------------------------- Helper functions ----------------------------

def identify_instruments(rm: pyvisa.ResourceManager):
    resources = rm.list_resources()
    print("Detected instruments:")
    print(resources, "\n")

    for idx, resource_name in enumerate(resources, start=1):
        try:
            inst = rm.open_resource(resource_name)
            ident = inst.query("*IDN?").strip()
            print(f"{idx}. {resource_name}\n   {ident}")
            inst.close()
        except Exception:
            print(f"{idx}. {resource_name}\n   ERROR communicating with instrument")

    return resources


def configure_voltmeter_dc(dmm):
    """Put the DMM into auto‑range DC‑voltage mode with averaging enabled."""
    dmm.write("*RST")  # Start from a known state
    dmm.write("CONF:VOLT:DC AUTO")  # Auto‑range, default resolution
    dmm.write("VOLT:DC:RANG:AUTO 1")
    dmm.write("AVER:STAT ON")
    dmm.write("AVER:TCON REP")
    dmm.write(f"AVER:COUN {DC_MEAS_AVERAGE_COUNT}")


def get_int(prompt: str, upper: int) -> int:
    """Prompt until the user supplies an integer in [1, upper]."""
    while True:
        try:
            value = int(input(f"{prompt} (1‑{upper}): "))
            if 1 <= value <= upper:
                return value
        except ValueError:
            pass
        print("Invalid selection. Try again.")


def get_yes_no(prompt: str) -> str:
    while True:
        ans = input(f"{prompt} [y|n]: ").lower()
        if ans in ("y", "n"):
            return ans
        print("Please type 'y' or 'n'.")


def get_cell_or_cancel() -> str | int:
    """Return an int between 1 and TOTAL_CELLS, or the string 'c'."""
    global cell_numbers

    while True:
        num = -1
        raw = input(f"Enter cell number [1‑{TOTAL_CELLS}] or 'c' to quit: ").lower()
        if raw == "c":
            return "c"
        try:
            num = int(raw)
            if not (1 <= num <= TOTAL_CELLS):
                print("Invalid entry. Try again.")
                continue
        except ValueError:
            print("Invalid entry. Try again.")
            continue

        # Warn the user if we've already measured this cell
        if num in cell_numbers:
            s = "This cell number has already been entered. Are you sure you want to measure this one? [y/n]"
            if get_yes_no(s) == "y":
                return num
            print("Okay. Try again:")
        else:
            cell_numbers.append(num)
            return num





# ---------------------------- Main routine ----------------------------

if __name__ == "__main__":
    print(INFO_TEXT)

    rm = pyvisa.ResourceManager()
    resources = identify_instruments(rm)
    if not resources:
        print("ERROR: No VISA instruments found. Check connection and try again.")
        raise SystemExit

    # User selects the DMM
    dmm_idx = get_int("Select the DMM measuring VOLTAGE", len(resources))
    volt_dmm = rm.open_resource(resources[dmm_idx - 1])

    # Optional: show a message on the DMM display (if supported by the model)
    try:
        volt_dmm.write("DISP:TEXT 'VOLTMETER'")
    except Exception:
        pass  # Non‑fatal if the command is unsupported

    if get_yes_no("Does the DMM label match the wiring?") == "n":
        print("Re‑run the program once wiring is corrected.")
        raise SystemExit

    try:
        # Configure meter once; thereafter simply trigger readings
        configure_voltmeter_dc(volt_dmm)

        # Prepare CSV file
        date_str = datetime.now().strftime("%Y‑%m‑%d %H.%M.%S")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        # file_path = os.path.join(data_dir, f"voltages {date_str}.csv")
        file_path = os.path.join(data_dir, "voltages.csv")


        with open(file_path, "r", encoding="utf‑8") as fh:
            fh_data = fh.readlines()

        # This unfortunately clears the file. However, we have its previous contents.
        # Thus, we can restore its contents.
        with open(file_path, "w", encoding="utf‑8") as fh:
            if not fh_data: fh.write("Cell Number,Timestamp,Open‑Circuit Voltage (V)\n")
            for cell_data in fh_data:
                fh.write(cell_data)
                try:
                    cell_num = int(cell_data.split(",")[0])
                    cell_numbers.append(cell_num)
                except Exception as e:
                    print(f"Warning: malformed cell number at csv row \"{cell_data}\".",
                          f"Original error: {e}")
            fh.flush()


            while True:
                cell = get_cell_or_cancel()
                if cell == "c":
                    if get_yes_no("Are you sure you want to exit?") == "y":
                        break
                    continue

                print("Measuring... please wait…")
                volt_dmm.write("READ?")
                sleep(1)  # Allow averaging to complete
                try:
                    voltage = float(volt_dmm.read())
                except ValueError:
                    print("ERROR: Could not parse reading. Retrying…")
                    continue

                if voltage < 0.05:
                    print("ERROR: Voltage ~0V. Is a cell connected?")
                    continue
                if not 2.7 <= voltage <= 4.2:
                    print("WARNING: Voltage out of expected range (2.7‑4.2V).")

                ts = datetime.now().strftime("%Y‑%m‑%d %H:%M:%S")
                print(f"Cell {cell}: {voltage:.6f} V")
                fh.write(f"{cell},{ts},{voltage}\n")
                fh.flush()

    finally:
        # Return DMM to local (front‑panel) control
        try:
            volt_dmm.write("SYST:LOC")
        except Exception:
            pass
        volt_dmm.close()
        rm.close()

    print("All done. Data saved to:")
    print(file_path)
