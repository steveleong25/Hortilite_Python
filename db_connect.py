import pytz
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

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
        if 'temperature' in doc_data:
            print(f'Temperature => {doc_data['temperature']} \u00B0C')
        if 'humidity' in doc_data:
            print(f'Humidity => {doc_data['humidity']}%')
        if 'moisture' in doc_data:
            print(f'Soil Moisture => {doc_data['moisture']}%')
        if 'EC' in doc_data:
            print(f'Electric Conductivity => {doc_data['EC']} us/cm')
        if 'pH' in doc_data:
            print(f'Soil pH => {doc_data['pH']}')
        if 'nitrogen' in doc_data:
            print(f'Nitrogen => {doc_data['nitrogen']} mg/kg')
        if 'phosphorus' in doc_data:
            print(f'Phosphorus => {doc_data['phosphorus']} mg/kg')
        if 'potassium' in doc_data:
            print(f'Potassium => {doc_data['potassium']} mg/kg')

# Write to Firebase
def add_new_record(sensor_name, sensor_id, data):
    doc_ref = db.collection(sensor_name).document(sensor_id)

    # Ensure the document exists
    if not doc_ref.get().exists:
        doc_ref.set({"active": True})  

    data_ref = doc_ref.collection("Data")
    
    docs = data_ref.stream()
    latest_record_number = max([int(doc.id) for doc in docs] or [0]) + 1

    data_ref.document(str(latest_record_number)).set({
        **data,
        "date_time": firestore.SERVER_TIMESTAMP,
    })


#read_all_from_collection("Soil", 1)