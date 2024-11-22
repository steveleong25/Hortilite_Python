import time
import platform
import json
from SerialDevice import SerialDevice
from readBytes import get_inst, read_value, get_dev_id

with open("SoilSensorInstructions.json", "r") as file:
    instructions = json.load(file)

# Access a specific instruction set
inst, inst_type = get_inst()

# CRC Calculations
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

# Windows testing, else Raspberry Pi
if platform.system() == "Windows":
    port_name = 'COM7'
else:
    port_name = '/dev/ttyUSB0'

# Initialize the serial device
serial_device = SerialDevice.init_port(port_name=port_name, baudRate=9600, timeOut=2, verbose=False)

try:
    for i in range(4, 10):
        a = [i, 0x03] + [int(value, 16) for value in inst.split()]
        trig_hex = bytearray(a)

        ##calculate checksum and append data to be sent
        crc = modbus_crc_16(trig_hex)
        a = trig_hex + bytearray(crc)
        serial_device.write(a)

        data = serial_device.read(size=13)  # Adjust size based on expected response
        if data:
            device_id = get_dev_id(data.hex())
            true_val = read_value(data.hex(), inst_type)
            print("Device ID:", device_id)
            print(f"Received Data: {true_val}")
        
        time.sleep(1)  # Delay to avoid flooding the device

except KeyboardInterrupt:
    # Ctrl+C Exit
    print("Terminating the connection.")
    serial_device.disconnect()
