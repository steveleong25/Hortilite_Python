import Adafruit_DHT as dht
from time import sleep

def read_DHT22_by_addr(addr_range):
    # loop = True

    # while loop:
    h1, t1 = dht.read_retry(dht.DHT22, addr_range[0])
    h2, t2 = dht.read_retry(dht.DHT22, addr_range[1])
    h3, t3 = dht.read_retry(dht.DHT22, addr_range[2])
    h4, t4 = dht.read_retry(dht.DHT22, addr_range[3])
    print('''{0:0.1f}, {1:0.1f}, {2:0.1f},{3:0.1f}, {4:0.3f}, {5:0.3f}, {6:0.3f}, {7:0.3f}'''.format(h1, t1, h2, t2, h3, t3, h4, t4), end="\r", flush=True)

    #print('Temp = {0:0.1f}*C Humidity = {1:0.1f)%'.format(t,h))
    #sleep(1)

read_DHT22_by_addr((5, 6, 16, 26))