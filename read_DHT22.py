import Adafruit_DHT as dht
from time import sleep

#print(dht.DHT22)

#for i in range(1, 5):
while True:
    h1, t1 = dht.read_retry(dht.DHT22, 5)
    h2, t2 = dht.read_retry(dht.DHT22, 6)
    h3, t3 = dht.read_retry(dht.DHT22, 16)
    h4, t4 = dht.read_retry(dht.DHT22, 26)
    print("{0:0.3f}, {1:0.3f}, {2:0.3f}, {3:0.3f}, {4:0.3f}, {5:0.3f}, {6:0.3f}, {7:0.3f}".format(h1, t1, h2, t2, h3, t3, h4, t4),
          end="\r", flush=True)
    #print('Temp = {0:0.1f}*C Humidity = {1:0.1f)%'.format(t,h))
    sleep(1)
