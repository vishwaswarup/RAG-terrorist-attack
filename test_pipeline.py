import sys
import os
import uuid
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipeline import ingest
from incident_pipeline import process_document
file_path = '/Users/vishwaswaruprath/.gemini/antigravity-ide/brain/e2d0b8e7-3250-458d-9738-df92afc088b5/.tempmediaStorage/media_e2d0b8e7-3250-458d-9738-df92afc088b5_1782296159089.png'
doc = ingest(file_path)
print("Doc:", doc)
print("Doc source_type:", doc.source_type)
res = process_document(doc)
print("Process Result:", res)
