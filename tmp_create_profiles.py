import appwrite_utils as aws
from appwrite.services.databases import Databases
from appwrite.id import ID
from appwrite.exception import AppwriteException

db = Databases(aws.get_server_client())
try:
    db.create_collection(aws.DB_ID, 'profiles', 'User Profiles')
    print("Collection created")
except AppwriteException as e:
    print(e)
    if e.code != 409: raise e

try: db.create_string_attribute(aws.DB_ID, 'profiles', 'userid', 255, True)
except: pass

try: db.create_string_attribute(aws.DB_ID, 'profiles', 'email', 255, True)
except: pass

try: db.create_string_attribute(aws.DB_ID, 'profiles', 'role', 50, False, default='user')
except Exception as e: print(e)

print("Profiles configured")
