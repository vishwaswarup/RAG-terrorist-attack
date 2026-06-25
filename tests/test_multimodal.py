import sys
import os
import unittest
from PIL import Image

sys.path.insert(0, os.path.abspath("."))
from retrieval.embedding_service import EmbeddingService
from retrieval.chroma_manager import ChromaManager
from retrieval.retrieval_engine import RetrievalEngine
from ingestion.image_ingestor import extract_image_text
from pipeline import ingest
from incident_pipeline import process_document

class TestMultimodal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create dummy image
        cls.img_path = "test_image.jpg"
        img = Image.new('RGB', (224, 224), color = 'red')
        img.save(cls.img_path)
        
        # Init DBs (use a test collection)
        cls.test_col = "test_multimodal"
        cls.db = ChromaManager(cls.test_col)
        
        # Clear collections if they exist
        try:
            cls.db.client.delete_collection(cls.test_col)
            cls.db.client.delete_collection(cls.test_col + "_images")
        except:
            pass
            
        cls.db = ChromaManager(cls.test_col)
        
    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.img_path):
            os.remove(cls.img_path)
        try:
            cls.db.client.delete_collection(cls.test_col)
            cls.db.client.delete_collection(cls.test_col + "_images")
        except:
            pass

    def test_01_extract_image_text(self):
        res = extract_image_text(self.img_path)
        self.assertIn("image_embedding", res)
        self.assertIsNotNone(res["image_embedding"])
        self.assertEqual(len(res["image_embedding"]), 512) # ViT-B-32 dimension

    def test_02_pipeline_ingest(self):
        doc = ingest(self.img_path)
        self.assertIsNotNone(doc)
        self.assertEqual(doc.source_type, "IMAGE")
        self.assertIn("image_embedding", doc.metadata)
        self.assertEqual(len(doc.metadata["image_embedding"]), 512)

    def test_03_store_and_retrieve(self):
        doc = ingest(self.img_path)
        
        # In a real run, incident pipeline extracts text
        incidents = process_document(doc)
        
        # Store multimodal record manually (like UI does)
        self.db.add_multimodal_record(
            record_id=f"{doc.doc_id}_image",
            document="",
            embedding=doc.metadata["image_embedding"],
            metadata={
                "source_document_id": doc.doc_id,
                "modality": "image",
                "embedding_type": "openclip",
                "source_file": doc.source_path
            }
        )
        
        self.assertEqual(self.db.image_collection.count(), 1)
        
        # Test Retrieval Engine
        engine = RetrievalEngine(collection_names=[self.test_col])
        results = engine.search("a red image", top_k=5, similarity_window=None)
        
        self.assertTrue(len(results) > 0)
        
        # We should get back our dummy incident
        first_res = results[0].incident
        self.assertEqual(first_res.source_document_id, doc.doc_id)

if __name__ == "__main__":
    unittest.main()
