import Adafruit_DHT as dht
import subprocess
from db_connect import add_new_record
from time import sleep

def read_DHT22_by_addr(addr_range):
    try:
        ip_addr = subprocess.check_output(["hostname", "-I"]).decode("utf-8").strip()
    except Exception as e:
        return f"Exception: {str(e)}"
    
    h1, t1 = dht.read_retry(dht.DHT22, addr_range[0])
    h2, t2 = dht.read_retry(dht.DHT22, addr_range[1])
    h3, t3 = dht.read_retry(dht.DHT22, addr_range[2])
    h4, t4 = dht.read_retry(dht.DHT22, addr_range[3])
    
    results = [{"Temperature" : round(t1, 2), "Humidity" : round(h1, 2)},
               {"Temperature" : round(t2, 2), "Humidity" : round(h2, 2)},
               {"Temperature" : round(t3, 2), "Humidity" : round(h3, 2)},
               {"Temperature" : round(t4, 2), "Humidity" : round(h4, 2)}
               ]
    
    #print('''{0:0.1f}, {1:0.1f}, {2:0.1f},{3:0.1f}, {4:0.1f}, {5:0.1f}, {6:0.1f}, {7:0.1f}'''.format(h1, t1, h2, t2, h3, t3, h4, t4), end="\r", flush=True)

    if ip_addr == "192.168.1.102":
        device_id = (5, 6, 7, 8)
    else:
        device_id = (1, 2, 3, 4)
    
    for dev_id, result in zip(device_id, results):
        add_new_record("DHT22", dev_id, result)

#read_DHT22_by_addr((5, 6, 16, 26))