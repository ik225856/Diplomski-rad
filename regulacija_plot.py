import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from io import BytesIO
from PIL import Image
import win32clipboard


def copy_to_clipboard_fullscreen(fig):
    """Kopira dijagram u međuspremnik u punoj veličini."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
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

    print("Diagram copied to clipboard in full resolution!")


def plot_data(csv_file_path):
    try:
        data = pd.read_csv(csv_file_path, encoding='ISO-8859-1')

        # Podaci iz CSV
        time = data['Vrijeme (s)']
        axial_force = data['Aksijalna sila (N)']
        temperature_ch1 = data['Temperatura Ch1 (°C)']
        temperature_ch2 = data['Temperatura Ch2 (°C)']
        shear_velocity = data['Posmicna brzina (mm/s)']

        # Pronađi zadnje vrijeme za svaki temperaturni kanal
        last_temp_ch1_time = data['Vrijeme (s)'][data['Temperatura Ch1 (°C)'].last_valid_index()]
        last_temp_ch2_time = data['Vrijeme (s)'][data['Temperatura Ch2 (°C)'].last_valid_index()]
        last_temp_time = min(last_temp_ch1_time, last_temp_ch2_time)
        filtered_data = data[data['Vrijeme (s)'] <= last_temp_time]

        # Čišćenje podataka
        axial_force_clean = filtered_data.dropna(subset=['Aksijalna sila (N)'])
        temp_ch1_clean = filtered_data.dropna(subset=['Temperatura Ch1 (°C)'])
        temp_ch2_clean = filtered_data.dropna(subset=['Temperatura Ch2 (°C)'])
        shear_velocity_clean = filtered_data.dropna(subset=['Posmicna brzina (mm/s)'])

        # Provjera za detekciju proboja
        detection_index = data[data['Signal Received Time'] == "False Signal Received"].index
        detection_time = None
        if not detection_index.empty:
            detection_time = data.loc[detection_index[0], 'Vrijeme (s)']

        # Font i veličine
        font_properties = {'fontname': 'Times New Roman', 'fontsize': 22}
        tick_label_size = 18

        # Postavljanje dijagrama
        fig, (ax1, ax3) = plt.subplots(2, 1, sharex=True, figsize=(12, 8))

        # Aksijalna sila
        ax1.plot(axial_force_clean['Vrijeme (s)'], axial_force_clean['Aksijalna sila (N)'], color='black', linewidth=3.5, label='Aksijalna sila')
        ax1.axhline(y=40, color='black', linestyle='--', linewidth=3.5, label='Zadana aksijalna sila')
        if detection_time is not None:
            ax1.axvline(x=detection_time, color='gray', linestyle='dashed', linewidth=3.5, label='Detekcija proboja')

        # Postavi granice i intervale na osi aksijalne sile
        min_force = int(axial_force_clean['Aksijalna sila (N)'].min() // 10 * 10)
        max_force = int(axial_force_clean['Aksijalna sila (N)'].max() // 10 * 10 + 10)
        ax1.set_ylim(min_force, max_force)
        ax1.set_yticks(range(min_force, max_force + 10, 10))

        # Grid s punom linijom
        ax1.grid(axis='both', linestyle='-', linewidth=1.0)

        ax1.set_ylabel('Aksijalna sila, N', labelpad=20, **font_properties)
        ax1.tick_params(axis='both', labelsize=tick_label_size)

        # Temperatura
        ax2 = ax1.twinx()
        ax2.plot(temp_ch1_clean['Vrijeme (s)'], temp_ch1_clean['Temperatura Ch1 (°C)'], color='red', linewidth=3.5, label='Temperatura uzorka')
        ax2.plot(temp_ch2_clean['Vrijeme (s)'], temp_ch2_clean['Temperatura Ch2 (°C)'], color='green', linestyle='--', linewidth=3.5, label='Temperatura prostorije')
        min_temp = max(20, int(min(temp_ch1_clean['Temperatura Ch1 (°C)'].min(), temp_ch2_clean['Temperatura Ch2 (°C)'].min()) // 5 * 5))
        max_temp = int(max(temp_ch1_clean['Temperatura Ch1 (°C)'].max(), temp_ch2_clean['Temperatura Ch2 (°C)'].max()) // 5 * 5 + 5)
        ax2.set_ylim(min_temp, max_temp)
        ax2.set_yticks(range(min_temp, max_temp + 5, 5))  # Brojevi na osi svakih 5 stupnjeva
        ax2.set_ylabel('Temperatura, °C', labelpad=20, **font_properties)
        ax2.tick_params(axis='both', labelsize=tick_label_size)

        # Posmična brzina
        ax3.plot(shear_velocity_clean['Vrijeme (s)'], shear_velocity_clean['Posmicna brzina (mm/s)'], color='blue', linewidth=3.5, label='Posmična brzina')
        ax3.set_xlabel('Vrijeme, s', **font_properties)
        ax3.set_ylabel('Posmična brzina, mm/s', labelpad=28, **font_properties)  # Podešen razmak naslova osi
        ax3.tick_params(axis='both', labelsize=tick_label_size)
        ax3.grid(axis='both', linestyle='-', linewidth=1.0)  # Grid s punom linijom

        # Dodavanje legende
        legend_elements = [
            Line2D([0], [0], color='black', lw=3.5, label='Aksijalna sila'),
            Line2D([0], [0], color='black', lw=3.5, linestyle='--', label='Zadana aksijalna sila'),
            Line2D([0], [0], color='red', lw=3.5, label='Temperatura uzorka'),
            Line2D([0], [0], color='green', lw=3.5, linestyle='--', label='Temperatura prostorije'),
            Line2D([0], [0], color='blue', lw=3.5, label='Posmična brzina'),
            Line2D([0], [0], color='gray', lw=3.5, linestyle='dashed', label='Detekcija proboja')
        ]
        fig.legend(handles=legend_elements, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.05), prop={'size': 16})

        fig.tight_layout(rect=[0, 0.05, 1, 0.95])

        # Automatsko kopiranje u međuspremnik u punoj veličini
        copy_to_clipboard_fullscreen(fig)

        # Prikaz dijagrama
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
