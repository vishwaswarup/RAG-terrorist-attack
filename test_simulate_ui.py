import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipeline import ingest
from incident_pipeline import process_document
from models.image_asset import ImageAsset

temp_path = '/Users/vishwaswaruprath/.gemini/antigravity-ide/brain/e2d0b8e7-3250-458d-9738-df92afc088b5/.tempmediaStorage/media_e2d0b8e7-3250-458d-9738-df92afc088b5_1782296159089.png'
print("Temp path exists:", os.path.exists(temp_path))

doc = ingest(temp_path)
print("Doc source type:", doc.source_type)

incidents = process_document(doc)
print("Extracted incidents length:", len(incidents))

if len(incidents) > 0:
    inc = incidents[0]
    print("Instance of ImageAsset?", isinstance(inc, ImageAsset))
    print("Type of inc:", type(inc))
    print("ImageAsset type:", ImageAsset)
