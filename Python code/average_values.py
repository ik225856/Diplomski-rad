import os
import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askdirectory

def select_directory():
    Tk().withdraw()  
    return askdirectory(title="Odaberite glavnu mapu s CSV datotekama")

def calculate_force_temp_and_drill_time(main_dir):
  
    total_max_force_sum = 0
    total_temp_rise_sum = 0
    total_max_temp_sum = 0
    total_drill_time_sum = 0
    total_csv_files = 0

    
    csv_files = [f for f in os.listdir(main_dir) if f.endswith('.csv')]
    for file in csv_files:
        filepath = os.path.join(main_dir, file)
        try:
            df = pd.read_csv(filepath, encoding="ISO-8859-1")  
        except UnicodeDecodeError:
            print(f"Greška kodiranja u datoteci: {filepath}")
            continue  

        
        max_force = df.iloc[:, 1].max()
        total_max_force_sum += max_force

        
        force_column = df.iloc[:, 1]
        timestamp_column = df.iloc[:, 0]
        signal_column = df.iloc[:, 4]  

        
        start_time = None
        end_time = None
        for i in range(len(force_column)):
            if start_time is None and force_column[i] > 0.5:
                start_time = timestamp_column[i]
            if start_time is not None and signal_column[i] == "False Signal Received":
                end_time = timestamp_column[i]
                break  

        if start_time and end_time:
            drill_time = end_time - start_time
            total_drill_time_sum += drill_time

       
        temp_column = df.iloc[:, 2].dropna()
        if not temp_column.empty:
            initial_temp = temp_column.iloc[0]
            max_temp = temp_column.max()
            temp_rise = max_temp - initial_temp
            total_temp_rise_sum += temp_rise
            total_max_temp_sum += max_temp

        total_csv_files += 1

    
    avg_max_force = round(total_max_force_sum / total_csv_files, 2) if total_csv_files else 0
    avg_temp_rise = round(total_temp_rise_sum / total_csv_files, 2) if total_csv_files else 0
    avg_max_temp = round(total_max_temp_sum / total_csv_files, 2) if total_csv_files else 0
    avg_drill_time = round(total_drill_time_sum / total_csv_files, 2) if total_csv_files else 0

    return avg_max_force, avg_temp_rise, avg_max_temp, avg_drill_time, total_csv_files


main_directory = select_directory()
if main_directory:
    avg_max_force, avg_temp_rise, avg_max_temp, avg_drill_time, file_count = calculate_force_temp_and_drill_time(main_directory)
    print(f"Broj učitanih CSV datoteka: {file_count}")
    print(f"Prosječna najviša aksijalna sila: {avg_max_force}")
    print(f"Prosječno vrijeme bušenja: {avg_drill_time}")
    print(f"Prosječno povišenje temperature: {avg_temp_rise}")
    print(f"Prosječna maksimalna zabilježena temperatura: {avg_max_temp}")
else:
    print("Mapa nije odabrana.")
