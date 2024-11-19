#!/usr/bin/env python

from __future__ import print_function
import NetFT
import argparse
import time
import socket
import struct
import threading
import csv
import os
import ctypes
from picosdk.usbtc08 import usbtc08 as tc08
from picosdk.functions import assert_pico2000_ok

# Definicije za server i direktorijum za CSV fajlove
SERVER_HOST = '192.168.0.2'
PORT_FORCE = 2000
BASE_CSV_DIR = r'C:\Users\Ivan\Desktop\data logging'

running = True
logging_active = False
start_time = None
file = None
writer = None
temp_chandle = None  # Temperaturni senzor

# Dodajte zaključavanje za sigurno rukovanje datotekom
file_lock = threading.Lock()

# Funkcija za osiguranje direktorija
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory created: {directory}")
    else:
        print(f"Directory exists: {directory}")

# Funkcija za inicijalizaciju senzora sile
def initialize_sensor(ip_address):
    sensor = NetFT.Sensor(ip_address)
    return sensor

# Funkcija za povezivanje sa serverom na određenom portu
def connect_to_server(port):
    """Connect to a server at a given port."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, port))
    client_socket.settimeout(5)  # Postavljanje timeouta za socket
    print(f'Connected to server {SERVER_HOST}:{port}')
    return client_socket

# Funkcija za inicijalizaciju temperaturnog senzora na kanalima 1 i 2
def initialize_temperature_sensor():
    global temp_chandle
    temp_chandle = ctypes.c_int16()
    status = {}

    # Otvori TC-08 jedinicu
    status["open_unit"] = tc08.usb_tc08_open_unit()
    assert_pico2000_ok(status["open_unit"])
    temp_chandle = status["open_unit"]

    # Podesi glavno odbacivanje na 50 Hz
    status["set_mains"] = tc08.usb_tc08_set_mains(temp_chandle, 0)
    assert_pico2000_ok(status["set_mains"])

    # Postavke za kanale 1 i 2 na termoelement tip K
    typeK = ctypes.c_int8(75)  # Thermocouple type K
    status["set_channel_1"] = tc08.usb_tc08_set_channel(temp_chandle, 1, typeK)
    status["set_channel_2"] = tc08.usb_tc08_set_channel(temp_chandle, 2, typeK)
    assert_pico2000_ok(status["set_channel_1"])
    assert_pico2000_ok(status["set_channel_2"])

    return status

# Funkcija za očitavanje temperature sa kanala 1 i 2
def get_temperatures():
    temp_buffer = (ctypes.c_float * 9)()  # Buffer za 9 očitavanja
    overflow = ctypes.c_int16(0)
    units = tc08.USBTC08_UNITS["USBTC08_UNITS_CENTIGRADE"]

    # Dobavi očitavanja temperature
    status = {}
    status["get_single"] = tc08.usb_tc08_get_single(temp_chandle, ctypes.byref(temp_buffer), ctypes.byref(overflow), units)
    assert_pico2000_ok(status["get_single"])

    return temp_buffer[1], temp_buffer[2]  # Kanali 1 i 2

# Funkcija za generisanje jedinstvenog naziva CSV fajla
def get_unique_csv_file_path(base_dir):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(base_dir, f'output_{timestamp}.csv')

# Funkcija za logiranje aksijalne sile
def log_axial_force(sensor, nula, continuous):
    global logging_active, start_time, file, writer

    try:
        while running:
            if logging_active:
                if file is None:
                    with file_lock:
                        csv_file_path = get_unique_csv_file_path(BASE_CSV_DIR)
                        print(f"Logging data to {csv_file_path}")

                        file = open(csv_file_path, mode='a', newline='')
                        writer = csv.writer(file)
                        writer.writerow(['Vrijeme (s)', 'Aksijalna sila (N)', 'Temperatura Ch1 (°C)', 'Temperatura Ch2 (°C)', 'Signal OFF Received'])

                # Pročitaj podatke sile
                sensor.getForce()
                sensor_data = sensor.force()

                if len(sensor_data) > 2:
                    if start_time is None:
                        start_time = time.time()

                    elapsed_time = time.time() - start_time
                    Z_sila = (nula - sensor_data[2]) / 1000000

                    # Upis podataka u CSV datoteku
                    with file_lock:
                        if writer:
                            writer.writerow([elapsed_time, Z_sila, '', '', ''])
                            file.flush()

                    # Ispisuje očitanja sile ako je aktiviran `--continuous`
                    if continuous:
                        print(f"Vrijeme: {elapsed_time:.2f} s, Aksijalna sila: {Z_sila:.6f} N")

            time.sleep(0.01)  # 100 Hz
    except KeyboardInterrupt:
        print("Exiting axial force logging.")
    finally:
        finalize_csv_logging()

# Funkcija za logiranje temperature sa oba kanala
def log_temperature():
    global logging_active, start_time, file, writer

    try:
        while running:
            if logging_active:
                elapsed_time = time.time() - start_time
                temp_ch1, temp_ch2 = get_temperatures()

                with file_lock:
                    if writer:
                        writer.writerow([elapsed_time, '', temp_ch1, temp_ch2, ''])
                        file.flush()

            time.sleep(0.01)  # 10 Hz
    except KeyboardInterrupt:
        print("Exiting temperature logging.")
    finally:
        finalize_csv_logging()

# Funkcija za slanje podataka sile PLC-u
def send_data_to_plc(client_socket, sensor, nula):
    global running
    try:
        while running:
            sensor.getForce()
            a = sensor.force()
            if len(a) > 2:
                Z_sila = (nula - a[2]) / 1000000
                message = struct.pack('>f', Z_sila)
                client_socket.sendall(message)
            time.sleep(0.01538)  # 65 Hz
    except KeyboardInterrupt:
        print('Exiting send_data_to_plc thread')
    finally:
        client_socket.close()

# Funkcija za zatvaranje CSV fajla
def finalize_csv_logging():
    global file, writer
    with file_lock:
        if file:
            print("Finalizing CSV logging...")
            file.flush()
            os.fsync(file.fileno())
            file.close()
            file = None
            writer = None

# Funkcija za primanje podataka sa PLC-a
def receive_plc_data(client_socket):
    global logging_active, start_time, writer, file
    try:
        while running:
            try:
                data = client_socket.recv(2)
                if data:
                    if data == b'\x01\x00':  # Primitak True signala
                        print("PLC Start Logging Signal Received (True)")
                        logging_active = True
                        start_time = time.time()
                    elif data == b'\x00\x00':  # Primitak False signala
                        print("PLC Stop Logging Signal Received (False)")

                        # Zabilježite timestamp za signal "False"
                        false_signal_time = time.time() - start_time if start_time else 0
                        with file_lock:
                            if writer and file:
                                writer.writerow([false_signal_time, '', '', '', "False Signal Received"])
                                file.flush()

                        # Nastavi logiranje još 11 sekundi nakon primanja signala "False"
                        time.sleep(11)
                        logging_active = False
                        finalize_csv_logging()
            except socket.timeout:
                print("Socket timeout, continuing...")
            time.sleep(0.001)
    except socket.error as e:
        print(f"Error receiving PLC data: {e}")
    finally:
        try:
            client_socket.close()
        except Exception as close_error:
            print(f"Error closing socket: {close_error}")

# Glavna funkcija
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Read data from ATI NetFT sensors, temperature sensor, and PLC.", add_help=False)
    parser.add_argument('ip', metavar='ip address', type=str, help="The IP address of the sensor")
    parser.add_argument('-c', '--continuous', dest='continuous', action='store_true', help="Print data continuously")
    args = parser.parse_args()

    # Inicijalizacija senzora sile
    sensor = initialize_sensor(args.ip)

    # Dobavi početno očitavanje sile na Z-osi
    sensor.getForce()
    a = sensor.force()
    if len(a) > 2:
        nula = a[2]
    else:
        print("Error: Unable to read initial Z-force")
        exit(1)

    # Inicijalizacija temperaturnog senzora
    initialize_temperature_sensor()

    # Osiguranje da direktorijum za CSV postoji
    ensure_directory_exists(BASE_CSV_DIR)

    try:
        # Konekcija sa serverom (PLC za podatke sile)
        client_socket_force = connect_to_server(PORT_FORCE)

        # Pokretanje niti za prijem signala sa PLC-a
        plc_thread = threading.Thread(target=receive_plc_data, args=(client_socket_force,))
        plc_thread.daemon = True
        plc_thread.start()

        # Pokretanje niti za logiranje sile sa opcijom `continuous`
        force_thread = threading.Thread(target=log_axial_force, args=(sensor, nula, args.continuous))
        force_thread.daemon = True
        force_thread.start()

        # Pokretanje niti za logiranje temperature
        temp_thread = threading.Thread(target=log_temperature)
        temp_thread.daemon = True
        temp_thread.start()

        # Pokretanje niti za slanje podataka PLC-u
        plc_send_thread = threading.Thread(target=send_data_to_plc, args=(client_socket_force, sensor, nula))
        plc_send_thread.daemon = True
        plc_send_thread.start()

        # Glavna petlja
        while running:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nReceived CTRL+C, shutting down...")
        running = False
        # Dodaj timeout za join kako bi izbjegli blokiranje
        force_thread.join(timeout=2)
        temp_thread.join(timeout=2)
        plc_send_thread.join(timeout=2)
        plc_thread.join(timeout=2)
    finally:
        print("Program successfully terminated.")
        time.sleep(0.1)
