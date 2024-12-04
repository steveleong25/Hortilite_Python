from read_SoilSensors import read_soil_by_addr
from read_Cameras import capture_interval
from read_DHT22 import read_DHT22_by_addr

read_soil_by_addr(5, 8)
read_DHT22_by_addr((5, 6, 16, 26))
#capture_interval()