import datetime
from read_SoilSensors import read_soil_by_addr
from readCameraUpload import capture_and_upload
from read_DHT22 import read_DHT22_by_addr

print(f"\n ===== {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')} ===== \n")

camera_ip_range = ("192.168.1.205", "192.168.1.206", "192.168.1.207", "192.168.1.208")

read_soil_by_addr(5, 8)
read_DHT22_by_addr((5, 6, 16, 26))

for cam_ip in camera_ip_range:
    try:
        capture_and_upload(cam_ip)
    except Exception as e:
        print(f"Failed to process camera {cam_ip} : {e}")
