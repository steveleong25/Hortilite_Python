import firebase_admin
from firebase_admin import credentials, firestore

# Credentials JSON key file
cred = credentials.Certificate('db/hortilite-test-firebase-adminsdk-w9s0u-6fdaaf3ee5.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

## Sensor Type > Sensor ID > Data ==FIXED== > num_of_records

# Read from Firebase
docs = db.collection('Soil').document('soil1').collection('Data').stream()

for doc in docs:
    print(f'{doc.id} => {doc.to_dict()}')

# Write to Firebase
doc_ref = db.collection('Temperature').document('temp2').collection('Data').document('1')
doc_ref.set({
    'date_time': firestore.SERVER_TIMESTAMP,
    'humidity': 80.8,
    'temperature': 31.3,
})

