import time
import platform
import json
import datetime
from lib.SerialDevice import SerialDevice
from readBytes import get_inst, read_value, get_dev_id
from db_connect import add_new_record

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

def read_soil_by_addr(start_addr=1, end_addr=12):
    # Windows testing, else Raspberry Pi
    if platform.system() == "Windows":
        port_name = 'COM7'
    else:
        port_name = '/dev/ttyUSB0'

    # Initialize the serial device
    serial_device = SerialDevice.init_port(port_name=port_name, baudRate=9600, timeOut=2, verbose=False)

    collected_data = {}

    try:
        for i in range(start_addr, end_addr+1):
            a = [i, 0x03]
            for key in map(str, range(1, 6)):
                if key in instructions['instructions']:
                    byte_inst = [int(value, 16) for value in instructions['instructions']['bytes'].split()]
                    a = a + byte_inst
                trig_hex = bytearray(a)

                ##calculate checksum and append data to be sent
                crc = modbus_crc_16(trig_hex)
                a = trig_hex + bytearray(crc)
                serial_device.write(a)

                data = serial_device.read(size=13)  # Adjust size based on expected response
                if data:
                    device_id = get_dev_id(data.hex())
                    true_val = read_value(data.hex(), inst_type)
                    collected_data.update(true_val)
                    #print("Device ID:", device_id)
                    #print(f"Received Data: {collected_data}")
                    #add_new_record("Soil", device_id, true_val)
                
                with open('test_sensor_autolog.txt', 'a') as file:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    file.write(f"Timestamp: {current_time}\n")
                    file.write(f"Sensor Data: {collected_data}\n")
                    file.write("-" * 40 + "\n")
                    
                time.sleep(1)  # Delay to avoid flooding the device

    except KeyboardInterrupt:
        # Ctrl+C Exit
        print("Terminating the connection.")
        serial_device.disconnect()
