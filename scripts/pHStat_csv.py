from datetime import datetime
import os
import os.path
from pathlib import Path
import time
import csv
import locale
import numpy as np
# Set the locale to Dutch (Netherlands)
locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')  # On Windows, try 'Dutch_Netherlands' or 'nl_NL'


def create_csv(self, data, plots, header):
    """
    This function creates a new CSV file to log data with appropriate headers.
    """
    try:
        locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')  # Adjust for your locale if necessary
    except locale.Error:
        print("Locale setting failed. Proceeding with default locale.")

    # Get the current time
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")[:-3] 

    # Set the directory of saving the data
    script_dir = create_folder()
    
    for i, labels in enumerate(plots):
        if self.Log_file[i]:
            return
        # Create the file name using the current time
        file_name = f"{labels}_log_{now.strftime('%d%m%Y_%H%M%S')}.csv"
    
        # Get the absolute file path from the instance variable
        abs_file_path = self.Log_file[i]
        # Set the current time if it's not already set
        if not self.Log_date[i]:
            self.Log_date[i] = time.time()
    
        # Check if the file already exists
        if not os.path.exists(abs_file_path):
            abs_file_path = os.path.join(script_dir, file_name)
            self.Log_file[i] = abs_file_path    
        
            #pre_header_content = [labels, "Date " + now.strftime("%d-%m-%Y") ]
            pre_header_content = [
                labels,
                "Date " + now.strftime("%d-%m-%Y"),
                "Start Time " + now.strftime("%H:%M:%S")
            ]

            # Open the file
            with open(abs_file_path, 'w', newline='') as csvfile:
                # Create a regular writer object for pre-header content
                writer = csv.writer(csvfile, delimiter=';')
                
                # Write the pre-header content
                for line in pre_header_content:
                    writer.writerow([line])
                
                # Create a DictWriter object for the actual data
                fieldnames = ['Reaction time (s)', header[i]]
                dict_writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                
                # Write the header
                dict_writer.writeheader()
                number = locale.format_string("%.3f", data[i], grouping=True)

                initial_row = {
                'Reaction time (s)': 0,  # We start at 0
                header[i]: number if number else 'N/A'  # Example usage, adjust as needed
                }
                dict_writer.writerow(initial_row)

def log_csv(self, data, index, label):
    locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')  # On Windows, try 'Dutch_Netherlands' or 'nl_NL'
    
    #if index == 0: 
    #    number = locale.format_string("%.1f", data, grouping=True)
    #else: 
    if isinstance(data, (int, float)):
        number = locale.format_string("%.3f", data, grouping=True)
    else:
        number = data
    #now = datetime.now()
    #time_count = time.time() - self.Log_date[index]
    time_count = self.logging_timer.elapsed()

    #current_time = now.strftime("%H:%M:%S.%f")[:-3] 
    abs_file_path = self.Log_file[index]
    #time_count_formatted = locale.format_string('%.0f', round(time_count,0)) 
    time_count_formatted = locale.format_string('%.1f', time_count)

    if os.path.exists(abs_file_path):
        append_csv(abs_file_path, time_count_formatted, number, label)

def append_csv(abs_file_path, time_count, data, label):
    locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')  # On Windows, try 'Dutch_Netherlands' or 'nl_NL'

    with open(abs_file_path, 'a', newline='') as csvfile:
        fieldnames = ['Reaction time (s)', label]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writerow({
            #'Time': current_time,
            'Reaction time (s)': time_count,
            label : data
            })

def read_log_data(self, index):
    locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')  # On Windows, try 'Dutch_Netherlands' or 'nl_NL'
    
    abs_file_path = self.Log_file[index]

    if not abs_file_path:
        return [], []

    filedata = csv.reader(open(abs_file_path, 'rt'), delimiter=";")
    #time, cond = [], []
    # Skip the three header rows
    for _ in range(3):
        next(filedata)
    
    next(filedata)

    reaction_times = []
    data_values = []
        
    for row in filedata:
        row = [cell for cell in row if cell]

        # Convert the second and third elements to float
        # Assuming the "Reaction time" is in the second column and the data is in the third
        if len(row) >= 2:  # Make sure the row has enough elements
            reaction_str, data_str = row[:2]
            reaction_time = convert_to_float(reaction_str)
            data = convert_to_float(data_str)
                
            reaction_times.append(reaction_time)
            data_values.append(data)    
    return reaction_times, data_values

def convert_to_float(s):
    try:
        return float(s.replace(',', '.'))
    except ValueError:
        print(f"Error converting {s} to float.")
        
        #return float(s)
        return None

def get_correct_path(sub_path):
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        home_dir = Path(f'/home/{sudo_user}')
    else:
        home_dir = Path.home()
    
    return home_dir / sub_path

def create_folder():
    # Get the current date and time
    now = datetime.now()

    # Format the date as dd_mm_yyyy
    date_string = now.strftime("%d_%m_%Y")
    time_string = now.strftime("%H_%M")
    # Define the base directory where you want to create the folder
    desktop = os.path.expanduser("~/Desktop")
    home_dir = Path.home()
    # Specify the relative path you want to construct
    relative_path = 'Desktop/Data'

    # Get the full path
    base_dir = get_correct_path(relative_path)

    #base_dir = f'{home_dir}/Desktop/Data/'
    #print(full_path)
    #script_path = os.path.abspath(__file__)

    #base_dir = os.path.dirname(script_path)

    # Combine the base directory and the date string to form the full path
    folder_path = os.path.join(base_dir, date_string, time_string)

    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        pass
    return folder_path

def scale_time_data(self, time, data):
        if not time:
            return [0], [0], 'sec', 1
    
        if max(time) > 3600:
            time = np.array(time) / 3600
            time_unit = 'hr'  # Use 'hr' for hours
            scale = 3
        elif max(time) > 60:
            time = np.array(time) / 60
            time_unit = 'min'  # Use 'min' for minutes
            scale = 2
        else:
            time_unit = 'sec'  # Use 'sec' for seconds
            scale = 1
    
        return time, data, time_unit, scale
    