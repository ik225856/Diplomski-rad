In this project, three drilling modes for animal bones and synthetic samples were examined: drilling at a constant feed rate, interval drilling, and drilling with a constant axial force (applied to single-layer and three-layer structures). The files in this project are named to correspond to the drilling mode they represent.

The main components of the experimental setup include a Siemens S71200 PLC, an ATI NET F/T force sensor, and a Pico Technology USB TC08 temperature measurement device. The packages required to run the Python scripts from this project can be found here: https://github.com/CameronDevine/NetFT and here: https://github.com/picotech/picosdk-python-wrappers.

The scripts constant_shear_velocity.py and regulation.py can be executed in the terminal using the following command:
python <file_name> -c IP
(where -c enables continuous reading from the force sensor, and the current IP address of the sensor is 192.168.1.1).
