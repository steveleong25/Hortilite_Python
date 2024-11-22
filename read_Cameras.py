import serial
import time
import platform
import json

with open("SoilSensorInstructions.json", "r") as file:
    instructions = json.load(file)

# Access a specific instruction set
inst = instructions["instructions"]["temp_humidity"]["bytes"]

# Import your SerialDevice class from the provided file
from SerialDevice import SerialDevice

def modbus_crc_16(data, endian="big"):
    """Checksum based on Modbus CRC-16 coding.

    Parameters
    ----------
    data : bytearray
        data to calculate checksum
    endian : str, optional
        system endian, by default "big"

    Returns
    -------
    first, second : bytes, bytes
        checksum data in two bytes
    """    
    crc = 0xFFFF
    for pos in data:
        crc ^= pos 
        for i in range(8):
            if ((crc & 1) != 0):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    if endian == "little":
        return crc >> 8, crc & 0xff
    elif endian == "big":
        return crc & 0xff, crc >> 8

# Instantiate the SerialDevice for testing on Windows (COM7)
if platform.system() == "Windows":
    port_name = 'COM7'
else:
    port_name = '/dev/ttyUSB0'  # Adjust for Pi later

# Initialize the serial device
serial_device = SerialDevice.init_port(port_name=port_name, baudRate=9600, timeOut=2, verbose=True)


# Testing read/write operations
try:
    for i in range(1, 9):
        #device_addr = '0x0' + i
        a = [i, 0x03] + [int(value, 16) for value in inst.split()]
        trig_hex = bytearray(a)

        ##calculate checksum and append data to be sent
        crc = modbus_crc_16(trig_hex)
        a = trig_hex + bytearray(crc)
        serial_device.write(a)
        #while True:
            # Read sensor data
        data = serial_device.read(size=13)  # Adjust size based on expected response
        if data:
            #byte_val=list(data)
            hex_data = ' '.join(f'{byte:02x}' for byte in data)
            print(f"Received Data: {data.hex()}")
        
        time.sleep(1)  # Delay to avoid flooding the device
except KeyboardInterrupt:
    # Graceful exit on Ctrl+C
    print("Terminating the connection.")
    serial_device.disconnect()
