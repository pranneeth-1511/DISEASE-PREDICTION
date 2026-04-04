import appwrite_utils as a
from appwrite.services.storage import Storage

s = Storage(a.get_server_client())
s.update_bucket('scans_bucket', name='Medical Scans', permissions=['read("any")'], file_security=False, enabled=True)
print("Bucket updated!")
