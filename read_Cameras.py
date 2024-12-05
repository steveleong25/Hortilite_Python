import cv2
import datetime
from lib.Cameras import HIKROBOTCamera

def capture_interval(camera_ip="192.168.1.205", interval_msec=15000):
    try:
        camera = HIKROBOTCamera(ip_addr=camera_ip, load_settings=True)
        camera.connect()

        if not camera.connected():
            print("Failed to connect to the camera.")
            return

        print("Camera connected successfully.")
        camera.stream()
        print("Camera streaming started.")

        next_capture_time = datetime.datetime.now()

        while True:
            if datetime.datetime.now() >= next_capture_time:
                image = camera.capture_one()
                next_capture_time = datetime.datetime.now() + datetime.timedelta(milliseconds=interval_msec)

                if image is not None:
                    cv2.imshow("capture", image)
                    k = cv2.waitKey(interval_msec)
                    cv2.destroyAllWindows()
                    if k == ord('q'):
                        break
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
    capture_interval()
