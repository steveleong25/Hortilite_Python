import pytz
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

# Credentials JSON key file
cred = credentials.Certificate('db/hortilite-test-firebase-adminsdk-w9s0u-6fdaaf3ee5.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

## Sensor Type > Sensor ID > Data ==FIXED== > num_of_records

# Read from Firebase
def read_all_from_collection(collection_name, sensor_id):
    if collection_name == 'Temperature':
        sensor_name = 'temp'
    elif collection_name == 'Soil':
        sensor_name = 'soil'
    elif collection_name == 'Lighting':
        sensor_name = 'light'
    elif collection_name is None:
        raise ValueError("Missing collection name!")        
    
    docs = db.collection(collection_name).document(sensor_name + str(sensor_id)).collection('Data').stream()

    for doc in docs:
        doc_data = doc.to_dict()
        print(f'Date => {doc_data['date_time'].astimezone(pytz.timezone('Asia/Kuala_Lumpur')).strftime('%Y-%m-%d %I:%M:%S %p %Z')}')
        print(f'Temperature => {doc_data['temperature']}')
        print(f'Humidity => {doc_data['humidity']}')

# Write to Firebase
def add_new_record(sensor_name, sensor_id, data):
    data_ref = db.collection(sensor_name).document(sensor_id).collection("Data")

    docs = data_ref.stream()

    latest_record_number = 0
    for doc in docs:
        try:
            record_number = int(doc.id)
            if record_number > latest_record_number:
                latest_record_number = record_number
        except ValueError:
            pass

    new_record_number = latest_record_number + 1

    new_doc_ref = data_ref.document(str(new_record_number))
    new_doc_ref.set({
        'date_time': firestore.SERVER_TIMESTAMP,
        'humidity': 80.8,
        'temperature': 31.3,
    })

    print(f"New record added with ID: {new_record_number}")


read_all_from_collection()