import datetime
from lib.Cameras import HIKROBOTCamera
from google.cloud import storage
from google.oauth2 import service_account
import numpy as np
import os
import cv2

def initialize_firebase():
    cred = service_account.Credentials.from_service_account_file('db/hortilite-test-firebase-adminsdk-w9s0u-6fdaaf3ee5.json')
    #cred = credentials.Certificate("db/hortilite-test-firebase-adminsdk-w9s0u-6fdaaf3ee5.json")
    #firebase_admin.initialize_app(cred, {'storageBucket': 'hortilite-test.firebasestorage.app'})
    storage_client = storage.Client(credentials=cred, project="hortilite-test")
    return storage_client.bucket('hortilite-test.firebasestorage.app')

def upload_image_to_firebase(bucket, image, file_name):
    cv2.imwrite(file_name, image)
    blob = bucket.blob(file_name)
    with open(file_name, "rb") as image_file:
        blob.upload_from_file(image_file, content_type="image/jpeg")
    blob.make_public()
    os.remove(file_name)
    return blob.public_url

def capture_and_upload(camera_ip="192.168.1.205"):
    try:
        bucket = initialize_firebase()
        camera = HIKROBOTCamera(ip_addr=camera_ip, load_settings=True)
        camera.connect()

        if not camera.connected():
            print("Failed to connect to the camera.")
            return

        print("Camera connected successfully.")
        camera.stream()
        print("Camera streaming started.")

        camera_name = camera_ip.replace('.', '_')
        image_data = camera.capture_one()
        if image_data is not None:
            file_name = f"{camera_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            public_url = upload_image_to_firebase(bucket, image_data, file_name)
            print(f"Image uploaded successfully. Public URL: {public_url}")
        else:
            print("Failed to capture image.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if camera.connected():
            camera.stop()
            print("Camera streaming stopped.")
        camera.close()
        print("Camera disconnected.")

if __name__ == "__main__":
    capture_and_upload()


