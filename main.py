# Main application entry point.
import os
import sys
import logging
import tkinter as tk

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# These imports are now correct based on the new folder structure
from gui import IGControlGUI

# Placeholder for styles.py, which was not provided
# A simple apply_styles function is needed for the GUI to run
class styles:
    @staticmethod
    def apply_styles(root):
        logging.info("Applying default styles (styles.py not provided).")

def main():
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        root = tk.Tk()
        styles.apply_styles(root)
        IGControlGUI(root)
        root.mainloop()

    except Exception as e:
        logging.critical(f"An unhandled exception occurred: {e}")

if __name__ == "__main__":
    main()
