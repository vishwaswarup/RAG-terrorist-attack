import streamlit as st
import os

st.title("⚙️ System Dashboard")

st.markdown("""
This dashboard provides a technical overview of the Offline Multimodal Intelligence Analysis System architecture and its current operational status.
""")

# --- Architecture Overview Diagram ---
st.header("Architecture Overview")
st.markdown("""
```mermaid
graph TD
    subgraph Storage
        SQLite[(SQLite DB)]
        Chroma[(ChromaDB Vector Store)]
    end
    
    subgraph Processing Pipeline
        OCR[Tesseract OCR]
        DocX[python-docx]
        PDF[pdfplumber]
        LLM[Ollama phi3]
        Embedder[BAAI/bge-small-en-v1.5]
    end
    
    subgraph UI
        Streamlit[Streamlit Frontend]
    end

    Streamlit -->|Query| Embedder
    Embedder -->|Vector Search| Chroma
    Chroma -->|Top K Results| LLM
    Streamlit -->|Document Upload| OCR
    Streamlit -->|Document Upload| DocX
    Streamlit -->|Document Upload| PDF
    OCR --> LLM
    PDF --> LLM
    LLM -->|Metadata Extraction| SQLite
    LLM -->|Embeddings| Chroma
```
""")

# --- System Status Metrics ---
st.header("System Telemetry")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Offline Mode Status", "✅ Active")
    st.metric("LLM Model", "Ollama (phi3)")
    st.metric("Embedding Model", "BAAI/bge-small-en-v1.5")

with col2:
    # Check SQLite Status
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage", "incidents.db")
    if os.path.exists(db_path):
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM incidents")
            total_sql = c.fetchone()[0]
            conn.close()
            st.metric("SQLite DB", "✅ Accessible")
            st.metric("SQLite Indexed Records", total_sql)
        except:
            st.metric("SQLite DB", "❌ Error")
            st.metric("SQLite Indexed Records", 0)
    else:
        st.metric("SQLite DB", "❌ Missing")
        st.metric("SQLite Indexed Records", 0)

with col3:
    # ChromaDB logic
    try:
        from retrieval.chroma_manager import ChromaManager
        gtd_db = ChromaManager("incidents")
        gtd_count = gtd_db.collection.count()
        st.metric("Chroma Collection: incidents", f"✅ Accessible ({gtd_count} vectors)")
        
        up_db = ChromaManager("uploaded_incidents")
        up_count = up_db.collection.count()
        st.metric("Chroma Collection: uploaded", f"✅ Accessible ({up_count} vectors)")
        
        st.metric("Total Vector Count", gtd_count + up_count)
    except Exception as e:
        st.error(f"ChromaDB Error: {e}")
        st.metric("Chroma Collections", "❌ Error")

# --- Dataset Information ---
st.header("Dataset Information")
st.info("""
**Global Terrorism Database (GTD) - India Subset**
- Sourced from the START Consortium GTD open-source dataset.
- Filtered specifically for incidents within the territorial boundaries of India.
- Optimized for offline RAG context retrieval using BGE embeddings.
""")
