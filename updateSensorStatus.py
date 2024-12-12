import Adafruit_DHT as dht
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta
from lib.SerialDevice import SerialDevice
from lib.Cameras import HIKROBOTCamera

# Credentials JSON key file
cred = service_account.Credentials.from_service_account_file('db/hortilite-test-firebase-adminsdk-w9s0u-6fdaaf3ee5.json')

# Database init
db = firestore.Client(credentials=cred)

# Addresses
camera_ip_range = ("192.168.1.205", "192.168.1.206", "192.168.1.207", "192.168.1.208")
soil_id = ("05", "06", "07", "08")
dht_id = (5, 6, 16, 26)
dht_device_id = (5, 6, 7, 8)

# Soil Sensors #
def checkSoilStatus(sensor_ids):
    for sensor_id in sensor_ids:
        try:
            serial_device = SerialDevice.init_port(port_name="/dev/ttyUSB0", baudRate=9600, timeOut=2, verbose=False)
            active_ref = db.collection("Soil").document("soil_" + str(sensor_id))
            if serial_device:
                active_ref.update({'active': True})
            else:
                active_ref.update({'active': False})
        except Exception as e:
            print(f"An error occurred: {e}")

# DHT22 Sensors #
def checkDHTStatus(addr_range):
    for dev_id, gpio_id in zip(dht_device_id, addr_range):
        active_ref = db.collection("DHT22").document("dht22_" + str(dev_id))
        for i in range(1, 4):
            h, t = dht.read_retry(dht.DHT22, gpio_id)
            if h is None and t is None:
                active_ref.update({'active': False})
            else:
                active_ref.update({'active': True})
                break

# Camera Sensors #
def checkCamStatus(ip_addr_range):
    for cam_ip in ip_addr_range:
        active_ref = db.collection("Camera").document(str(cam_ip))
        try:
            camera = HIKROBOTCamera(ip_addr=cam_ip, load_settings=True)
            camera.connect()
            active_ref.update({'active': True})

            if not camera.connected():
                active_ref.update({'active': False})
                print(f"Failed to connect to the camera: {cam_ip}")
        except Exception as e:
            print(f"Error connecting to camera {cam_ip}: {e}")

# Function Calls
checkSoilStatus(soil_id)
checkDHTStatus(dht_id)
checkCamStatus(camera_ip_range)
print("done")
