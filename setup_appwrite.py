import os
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.id import ID
from appwrite.exception import AppwriteException
import time

PROJECT_ID = '69d0b722002958fcb9a9'
API_KEY = 'standard_101ddc32c9fc08a8aed11cafc91863d7c573a5191b630a6445ec7e64b042d30250d23a1d3dcc0d7b149f7b3cc5ec2661a57cc5f23f285b8b91937b709f70cd64903f8addb3127dce47f2bfcf10d7beff9d59894a9a169c3b3cdc7a1b42c559265732fa0a327cef757436c58e19acfbbcc5861fffb2251b2a37ee87cdd25dbd4a'
ENDPOINT = 'https://sgp.cloud.appwrite.io/v1'

client = Client()
client.set_endpoint(ENDPOINT)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)

databases = Databases(client)
storage = Storage(client)

DB_ID = 'mediscan_db'
COLLECTION_ID = 'diagnoses'
BUCKET_ID = 'scans_bucket'

def setup():
    try:
        # 1. Create Database
        try:
            print(f"Creating database {DB_ID}...")
            databases.create(database_id=DB_ID, name='MediScan Database')
        except AppwriteException as e:
            if e.code == 409:
                print("Database already exists.")
            else:
                raise e
            
        # 2. Create Collection
        try:
            print(f"Creating collection {COLLECTION_ID}...")
            databases.create_collection(
                database_id=DB_ID,
                collection_id=COLLECTION_ID,
                name='Diagnoses',
                document_security=False # We will handle permissions via API, or could enable here
            )
        except AppwriteException as e:
            if e.code == 409:
                print("Collection already exists.")
            else:
                raise e

        # 3. Create Attributes
        print("Creating attributes...")
        try:
            # We wrap in try-except to ignore if already exists
            try: databases.create_string_attribute(DB_ID, COLLECTION_ID, 'user_id', 255, True)
            except AppwriteException as e: pass
            
            try: databases.create_string_attribute(DB_ID, COLLECTION_ID, 'type', 128, True)
            except AppwriteException as e: pass

            try: databases.create_string_attribute(DB_ID, COLLECTION_ID, 'diagnosis', 255, True)
            except AppwriteException as e: pass

            try: databases.create_float_attribute(DB_ID, COLLECTION_ID, 'confidence', True)
            except AppwriteException as e: pass

            try: databases.create_string_attribute(DB_ID, COLLECTION_ID, 'image_url', 1000, False)
            except AppwriteException as e: pass

            try: databases.create_integer_attribute(DB_ID, COLLECTION_ID, 'scan_count', False)
            except AppwriteException as e: pass
            
            try: databases.create_string_attribute(DB_ID, COLLECTION_ID, 'notes', 5000, False)
            except AppwriteException as e: pass

            try: databases.create_datetime_attribute(DB_ID, COLLECTION_ID, 'timestamp', True)
            except AppwriteException as e: pass
            
        except Exception as e:
            print(f"Error creating attributes: {e}")

        # 4. Create Storage Bucket
        try:
            print(f"Creating bucket {BUCKET_ID}...")
            storage.create_bucket(
                bucket_id=BUCKET_ID,
                name='Medical Scans',
                permissions=[],
                file_security=False,
                enabled=True,
                maximum_file_size=20000000, # 20MB
                allowed_file_extensions=['jpg', 'jpeg', 'png']
            )
        except AppwriteException as e:
            if e.code == 409:
                print("Bucket already exists.")
            else:
                raise e

        # Write config to .streamlit/secrets.toml
        os.makedirs(".streamlit", exist_ok=True)
        secrets_content = f"""
# Appwrite Config
APPWRITE_ENDPOINT = "{ENDPOINT}"
APPWRITE_PROJECT_ID = "{PROJECT_ID}"
APPWRITE_API_KEY = "{API_KEY}"
APPWRITE_DB_ID = "{DB_ID}"
APPWRITE_COL_ID = "{COLLECTION_ID}"
APPWRITE_BUCKET_ID = "{BUCKET_ID}"
"""
        with open(".streamlit/secrets.toml", "w") as f:
            f.write(secrets_content)
        print("Setup complete and secrets.toml written.")

    except Exception as e:
        print(f"Failed to setup: {e}")

if __name__ == "__main__":
    setup()
