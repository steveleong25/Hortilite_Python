import pytz
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime, timedelta

# Credentials JSON key file
cred = service_account.Credentials.from_service_account_file('db/hortilite-test-firebase-adminsdk-w9s0u-6fdaaf3ee5.json')

db = firestore.Client(credentials=cred)

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
        print(f"Date => {doc_data['date_time'].astimezone(pytz.timezone('Asia/Kuala_Lumpur')).strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
        if 'temperature' in doc_data:
            print(f"Temperature => {doc_data['temperature']} \u00B0C")
        if 'humidity' in doc_data:
            print(f"Humidity => {doc_data['humidity']}%")
        if 'moisture' in doc_data:
            print(f"Soil Moisture => {doc_data['moisture']}%")
        if 'EC' in doc_data:
            print(f"Electric Conductivity => {doc_data['EC']} us/cm")
        if 'pH' in doc_data:
            print(f"Soil pH => {doc_data['pH']}")
        if 'nitrogen' in doc_data:
            print(f"Nitrogen => {doc_data['nitrogen']} mg/kg")
        if 'phosphorus' in doc_data:
            print(f"Phosphorus => {doc_data['phosphorus']} mg/kg")
        if 'potassium' in doc_data:
            print(f"Potassium => {doc_data['potassium']} mg/kg")

# Write to Firebase
def add_new_record(sensor_name, sensor_id, data):
    active_ref = db.collection(sensor_name).document(sensor_name.lower() + '_' + str(sensor_id))
    data_ref = active_ref.collection("Data")

    active_ref.set({
        'active': True,
        })

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
        **data,
    })
