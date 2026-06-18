import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.chroma_manager import ChromaManager

db = ChromaManager()

print("Collection:", db.collection.name)
print("Count:", db.collection.count())
print(db.collection.peek())

