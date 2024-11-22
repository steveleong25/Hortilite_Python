import json

with open("SoilSensorInstructions.json", "r") as file:
    instructions = json.load(file)

def hex_to_signed(value):
    value = int(value, 16)
    
    # Check if it's a negative value in 16-bit two's complement
    if value >= 0x8000:
        value -= 0x10000  # Convert to negative by subtracting 0x10000
    
    return value

def get_inst():
    print("Read")
    for key, values in instructions["instructions"].items():
        print(f"{key}: {values['description']}")
        
    inst_type = input("Data to read: ")
    return instructions["instructions"][inst_type]["bytes"], inst_type

def get_dev_id(result):
    # remove CRC value (last two pairs of hex)
    result = result[:-4]
    device_id = result[0:2]
    return device_id

def read_value(result, inst_type):
    # remove CRC value (last two pairs of hex)
    result = result[:-4]

    #device_id = result[0:2]
    eff_bytes = result[4:4 + 2]
    data = result[6:6 + int(eff_bytes) * 2]
    convert_rate = instructions["instructions"][inst_type]["convert_rate"]
    
    
    if inst_type == '1': # temp + hum
        temp, hum = [data[i:i+4] for i in range(0, len(data), 4)]
        temp = hex_to_signed(temp) / convert_rate
        hum = hex_to_signed(hum) / convert_rate
        return temp, hum
    elif inst_type == '2': # soil moisture
        mst = hex_to_signed(data) / convert_rate
        return mst
    elif inst_type == '3': # conductivity
        cdt = hex_to_signed(data) / convert_rate
        return cdt   
    elif inst_type == '4': # pH
        ph = hex_to_signed(data) / convert_rate
        return ph
    elif inst_type == '5': # NPK
        n, p, k = [data[i:i+4] for i in range(0, len(data), 4)]
        n = hex_to_signed(n) / convert_rate
        p = hex_to_signed(p) / convert_rate
        k = hex_to_signed(k) / convert_rate
        return n, p, k
    elif inst_type == '6' or inst_type == '7' or inst_type == '8': # nitrogen, phosphorus, potassium
        return hex_to_signed(data) / convert_rate
        
