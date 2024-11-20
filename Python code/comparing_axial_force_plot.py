import matplotlib.pyplot as plt
import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def choose_single_csv(prompt):
        Tk().withdraw()
    file_path = askopenfilename(
        title=prompt,
        filetypes=[("CSV files", "*.csv")]
    )
    if not file_path:
        raise ValueError("No file selected. Operation canceled.")
    return file_path


def plot_data(file_paths):
    try:
        if len(file_paths) != 3:
            raise ValueError("Exactly 3 CSV files must be provided.")

        
        colors = ['red', 'black', 'green']
        labels = ['Teleća lopatična kost', 'PETG materijal', 'Sawbones sintetska kost']

        
        font_properties = {'fontname': 'Times New Roman', 'fontsize': 28}
        tick_label_size = 18

        
        fig, ax1 = plt.subplots(figsize=(12, 8))

        for i, file_path in enumerate(file_paths):
            
            data = pd.read_csv(file_path, encoding='ISO-8859-1')

            
            if 'Vrijeme (s)' not in data.columns or 'Aksijalna sila (N)' not in data.columns or 'Signal Received Time' not in data.columns:
                raise ValueError(f"File {file_path} does not contain the required columns.")

            
            data = data.dropna(subset=['Aksijalna sila (N)'])

            
            if "False Signal Received" in data['Signal Received Time'].values:
                end_index = data[data['Signal Received Time'] == "False Signal Received"].index.min()
                signal_time = data.loc[end_index, 'Vrijeme (s)']  
                data = data[data['Vrijeme (s)'] <= signal_time]  

            
            time = data['Vrijeme (s)']
            axial_force = data['Aksijalna sila (N)']

            
            ax1.plot(time, axial_force, color=colors[i], linewidth=3.5, label=labels[i])

        
        ax1.set_xlabel('Vrijeme, s', labelpad=15, **font_properties)
        ax1.set_ylabel('Aksijalna sila, N', labelpad=15, **font_properties)
        ax1.tick_params(axis='both', labelsize=tick_label_size)
        ax1.grid(axis='both', linestyle='--', linewidth=0.5)

        
        ax1.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.15),
            ncol=3,
            prop={'size': 28, 'family': 'Times New Roman'}
        )

        
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        
        file_paths = []
        file_paths.append(choose_single_csv("Select CSV file for Teleća lopatična kost"))
        file_paths.append(choose_single_csv("Select CSV file for PETG materijal"))
        file_paths.append(choose_single_csv("Select CSV file for Sawbones sintetska kost"))

        
        plot_data(file_paths)

    except Exception as e:
        print(f"Operation failed: {e}")
