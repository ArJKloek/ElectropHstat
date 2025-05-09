#!/usr/bin/env python3
# Conductivity meter for the Raspberri Pi using I2C
import argparse
import sys
from PyQt5.QtWidgets import QApplication, qApp
import main_GUI

# Create the parser
parser = argparse.ArgumentParser(description='Process reactor type and bus address (Decimal).')

# Add the arguments
parser.add_argument('reactor', type=str, help='The reactor type')
parser.add_argument('address', type=int, help='The address value')

# Parse the arguments
args = parser.parse_args()

Reactor = args.reactor
#Reactor = "CSTR"

address = args.address
#address = 100
        
def main(Reactor, address):
    app = QApplication(sys.argv)
    #app = QApplication([])
    main_win = main_GUI.MainWindow(Reactor, address)
    main_win.show()
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main(Reactor,address)



    
    
    
    