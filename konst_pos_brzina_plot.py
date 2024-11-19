import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import pandas as pd
from matplotlib.lines import Line2D
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import win32clipboard


def copy_to_clipboard(fig):
    """Automatski kopira trenutni dijagram u međuspremnik kao PNG."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image = Image.open(buf)

    # Spremanje slike u međuspremnik
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]  # Uklanja BMP zaglavlje
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

    print("Diagram copied to clipboard!")


def plot_data(csv_file_path):
    try:
        data = pd.read_csv(csv_file_path, encoding='ISO-8859-1')

        # Podaci iz CSV
        time = data['Vrijeme (s)']
        axial_force = data['Aksijalna sila (N)']
        temperature_ch1 = data['Temperatura Ch1 (°C)']  # Temperatura uzorka
        temperature_ch2 = data['Temperatura Ch2 (°C)']  # Temperatura prostorije

        # Pronađi zadnje vrijeme za svaki temperaturni kanal
        last_temp_ch1_time = data['Vrijeme (s)'][data['Temperatura Ch1 (°C)'].last_valid_index()]
        last_temp_ch2_time = data['Vrijeme (s)'][data['Temperatura Ch2 (°C)'].last_valid_index()]

        # Odredi najraniji od dva posljednja vremena kao granično vrijeme za prikaz podataka
        last_temp_time = min(last_temp_ch1_time, last_temp_ch2_time)
        filtered_data = data[data['Vrijeme (s)'] <= last_temp_time]

        # Čišćenje podataka - uklanja prazne ćelije za aksijalnu silu i temperature
        axial_force_clean = filtered_data.dropna(subset=['Aksijalna sila (N)'])
        time_axial_clean = axial_force_clean['Vrijeme (s)']
        axial_force_clean_values = axial_force_clean['Aksijalna sila (N)']

        temp_ch1_clean = filtered_data.dropna(subset=['Temperatura Ch1 (°C)'])
        time_temp_ch1_clean = temp_ch1_clean['Vrijeme (s)']
        temperature_ch1_clean = temp_ch1_clean['Temperatura Ch1 (°C)']

        temp_ch2_clean = filtered_data.dropna(subset=['Temperatura Ch2 (°C)'])
        time_temp_ch2_clean = temp_ch2_clean['Vrijeme (s)']
        temperature_ch2_clean = temp_ch2_clean['Temperatura Ch2 (°C)']

        # Font i veličine
        font_properties = {'fontname': 'Times New Roman', 'fontsize': 34}
        tick_label_size = 22

        # Postavljanje dijagrama
        fig, ax1 = plt.subplots(figsize=(12, 8))

        # Pronađi maksimalne vrijednosti za oba skupa podataka
        global_max = max(axial_force_clean_values.max(), temperature_ch1_clean.max(), temperature_ch2_clean.max())

        # Aksijalna sila
        min_force = int(axial_force_clean_values.min() // 10 * 10)
        max_force = int(global_max // 10 * 10 + 10)  # Koristimo globalni maksimum
        ax1.set_ylim(min_force, max_force)
        ax1.set_yticks(range(min_force, max_force + 10, 10))
        ax1.set_ylabel('Aksijalna sila, N', color='black', **font_properties)
        ax1.plot(time_axial_clean, axial_force_clean_values, color='black', linewidth=3.5, label='Aksijalna sila')
        ax1.tick_params(axis='y', labelsize=tick_label_size)
        ax1.tick_params(axis='x', labelsize=tick_label_size)

        # Temperatura
        ax2 = ax1.twinx()
        min_temp = max(20, int(min(temperature_ch1_clean.min(), temperature_ch2_clean.min()) // 10 * 10))
        max_temp = int(global_max // 10 * 10 + 10)  # Koristimo isti maksimum za oba grafa
        ax2.set_ylim(min_temp, max_temp)
        ax2.set_yticks(range(min_temp, max_temp + 5, 5))  # Brojevi na osi svakih 5 stupnjeva
        ax2.set_ylabel('Temperatura, °C', color='black', labelpad=20, **font_properties)  # Povećan razmak
        ax2.plot(time_temp_ch1_clean, temperature_ch1_clean, color='red', linewidth=3.5, label='Temperatura uzorka')
        ax2.plot(time_temp_ch2_clean, temperature_ch2_clean, color='green', linestyle='dashed', linewidth=3.5, label='Temperatura prostorije')
        ax2.tick_params(axis='y', labelsize=tick_label_size)

        # Dodavanje sive linije za Detekciju proboja
        detection_index = data[data['Signal Received Time'] == "False Signal Received"].index
        if not detection_index.empty:
            detection_time = data.loc[detection_index[0], 'Vrijeme (s)']
            ax1.axvline(x=detection_time, color='gray', linestyle='dashed', linewidth=3.5, label='Detekcija proboja')

        ax1.set_xlabel('Vrijeme, s', labelpad=15, **font_properties)
        ax1.grid(True)

        # Povećanje prostora ulijevo i automatsko podešavanje
        fig.tight_layout(rect=[-0.03, 0.2, 1.0, 1.0])  # Povećan prostor ispod dijagrama

        # Prilagođena legenda ispod dijagrama
        legend_elements = [
            Line2D([0], [0], color='black', lw=3.5, label='Aksijalna sila'),
            Line2D([0], [0], color='red', lw=3.5, label='Temperatura uzorka'),
            Line2D([0], [0], color='green', linestyle='dashed', lw=3.5, label='Temperatura prostorije'),
            Line2D([0], [0], color='gray', linestyle='dashed', lw=3.5, label='Detekcija proboja')
        ]

        fig.legend(
            handles=legend_elements,
            loc='lower center',
            ncol=2,
            bbox_to_anchor=(0.49, 0.02),  # Povećan prostor za legendu
            prop={'family': 'Times New Roman', 'size': 28},
        )

        # Automatsko kopiranje u međuspremnik
        copy_to_clipboard(fig)

        # Prikaži dijagram
        plt.show()

    except UnicodeDecodeError as e:
        print(f"Greška pri čitanju CSV datoteke: {e}")
    except Exception as e:
        print(f"Neka druga greška se dogodila: {e}")


def choose_csv_file():
    Tk().withdraw()
    filename = askopenfilename(
        title="Select a CSV file",
        filetypes=[("CSV files", "*.csv")]
    )
    return filename


if __name__ == "__main__":
    csv_file_path = choose_csv_file()
    if csv_file_path:
        plot_data(csv_file_path)
    else:
        print("No file selected. Exiting.")
