import streamlit as st
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipeline import ingest
from incident_pipeline import process_document
from retrieval.embedding_service import EmbeddingService
from retrieval.chroma_manager import ChromaManager

st.title("Upload & Analyze")
st.markdown("Upload documents (PDF, DOCX, TXT, PNG, JPG) to extract and index intelligence incidents.")

@st.cache_resource
def load_upload_backends():
    embedder = EmbeddingService()
    db = ChromaManager(collection_name="uploaded_incidents")
    return embedder, db

embedder, db = load_upload_backends()

TEMP_DIR = os.path.join(PROJECT_ROOT, "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

if "extracted_incidents" not in st.session_state:
    st.session_state.extracted_incidents = None
    st.session_state.document_text = ""
    st.session_state.extraction_complete = False

uploaded_file = st.file_uploader("Select a file for intelligence analysis", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    if st.button("Process File", type="primary"):
        temp_path = os.path.join(TEMP_DIR, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.session_state.extraction_complete = False
        st.session_state.extracted_incidents = None
        
        with st.status("Processing Document...", expanded=True) as status:
            st.write("✓ File Uploaded to internal storage")
            
            # 1. Ingest (Classify + Extract text + Create Document)
            st.write("⚙ Classifying file and extracting text...")
            doc = ingest(temp_path)
            
            if doc is None:
                status.update(label="Processing Failed", state="error", expanded=True)
                st.error("Failed to extract text from the document. Please check the logs.")
                st.stop()
                
            st.write("✓ File Classified & Text Extracted")
            st.write("✓ Document Object Created")
            st.session_state.document_text = doc.raw_text
            
            # 2. Process Document (Extract incidents + Store in SQLite)
            st.write("⚙ Extracting intelligence incidents...")
            incidents = process_document(doc)
            st.session_state.extracted_incidents = incidents
            
            st.write("✓ Incidents Extracted")
            st.write("✓ Stored locally in SQLite")
            
            status.update(label="Extraction Complete!", state="complete", expanded=False)
            st.session_state.extraction_complete = True

if st.session_state.extraction_complete and st.session_state.extracted_incidents is not None:
    incidents = st.session_state.extracted_incidents
    
    st.success(f"Successfully extracted **{len(incidents)}** incident(s).")
    
    with st.expander("Show Extracted Raw Text"):
        st.code(st.session_state.document_text, language="text")
    
    st.markdown("### Extracted Incidents")
    for i, inc in enumerate(incidents):
        with st.container(border=True):
            st.markdown(f"**Incident #{i+1}**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Date:** {inc.date or 'Unknown'}")
                st.markdown(f"**Location:** {inc.city or 'Unknown'}, {inc.state or 'Unknown'}, {inc.country or 'Unknown'}")
                st.markdown(f"**Attack Types:** {', '.join(inc.attack_types) if inc.attack_types else 'Unknown'}")
                st.markdown(f"**Target Types:** {', '.join(inc.target_types) if inc.target_types else 'Unknown'}")
            with col2:
                st.markdown(f"**Weapon Types:** {', '.join(inc.weapon_types) if inc.weapon_types else 'Unknown'}")
                st.markdown(f"**Responsible Groups:** {', '.join(inc.responsible_groups) if inc.responsible_groups else 'Unknown'}")
                st.markdown(f"**Killed:** {inc.killed} | **Injured:** {inc.injured}")
            
            st.markdown("**Summary:**")
            st.info(inc.summary)
            
    st.markdown("---")
    
    # Mode selection
    if "upload_action_mode" not in st.session_state:
        st.session_state.upload_action_mode = None
        
    st.markdown("### Next Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Query This Document", use_container_width=True):
            st.session_state.upload_action_mode = "query"
    with col2:
        if st.button("📚 Add To Knowledge Base", use_container_width=True):
            st.session_state.upload_action_mode = "store"

    if st.session_state.upload_action_mode == "store":
        st.markdown("#### Store to Knowledge Base")
        if st.button("Confirm Storage", type="primary"):
            with st.spinner("Embedding and storing in ChromaDB..."):
                documents = [inc.retrieval_text for inc in incidents]
                embeddings = embedder.embed_documents(documents)
                db.add_incidents(incidents, embeddings)
                st.success(f"Successfully added {len(incidents)} incidents to the 'uploaded_incidents' collection in ChromaDB!")
                st.balloons()
                
                # Reset state after successful storage
                st.session_state.extraction_complete = False
                st.session_state.extracted_incidents = None
                st.session_state.upload_action_mode = None

    elif st.session_state.upload_action_mode == "query":
        st.markdown("#### Analyze Intelligence")
        
        # Retrieval Scope Selection
        retrieval_scope = st.radio(
            "Retrieval Scope",
            options=["Uploaded Document Only", "Historical GTD Only", "Combined Intelligence Database"],
            horizontal=True
        )
        
        # In-memory retrieval engine definition
        import numpy as np
        from retrieval.models.retrieval_result import RetrievalResult
        from rag.rag_engine import RAGEngine
        from retrieval.retrieval_engine import RetrievalEngine
        
        class InMemoryRetrievalEngine:
            def __init__(self, incidents, embedder):
                self.incidents = incidents
                self.embedder = embedder
                self.doc_embeddings = None
                
            def search(self, query: str, top_k: int = 10, similarity_window: float = 0.05):
                if not query.strip() or not self.incidents:
                    return []
                
                # Lazy initialization of doc embeddings
                if self.doc_embeddings is None:
                    docs = [inc.retrieval_text for inc in self.incidents]
                    self.doc_embeddings = np.array(self.embedder.embed_documents(docs))
                    
                q_emb = np.array(self.embedder.embed_queries([query])[0])
                
                # Cosine similarity
                norms_d = np.linalg.norm(self.doc_embeddings, axis=1)
                norm_q = np.linalg.norm(q_emb)
                sims = np.dot(self.doc_embeddings, q_emb) / (norms_d * norm_q + 1e-10)
                
                candidates = []
                for i, sim in enumerate(sims):
                    candidates.append(RetrievalResult(incident=self.incidents[i], score=float(sim)))
                    
                candidates.sort(key=lambda x: x.score, reverse=True)
                candidates = candidates[:top_k]
                
                if similarity_window is not None and candidates:
                    best = candidates[0].score
                    candidates = [c for c in candidates if c.score >= best - similarity_window]
                    
                return candidates

        # Determine which RAGEngine to use based on scope
        if retrieval_scope == "Uploaded Document Only":
            if "temp_rag_engine" not in st.session_state:
                temp_retrieval = InMemoryRetrievalEngine(incidents, embedder)
                st.session_state.temp_rag_engine = RAGEngine(temp_retrieval)
            active_rag = st.session_state.temp_rag_engine
        elif retrieval_scope == "Historical GTD Only":
            if "gtd_rag_engine" not in st.session_state:
                st.session_state.gtd_rag_engine = RAGEngine(RetrievalEngine(collection_names=["incidents"]))
            active_rag = st.session_state.gtd_rag_engine
        else: # Combined
            if "combined_rag_engine" not in st.session_state:
                st.session_state.combined_rag_engine = RAGEngine(RetrievalEngine(collection_names=["incidents", "uploaded_incidents"]))
            active_rag = st.session_state.combined_rag_engine

        st.markdown("---")
        
        # Dedicated "Find Similar Historical Incidents" Button
        if st.button("🌟 Find Similar Historical Incidents", use_container_width=True):
            with st.spinner("Searching GTD for similar historical events..."):
                if "gtd_rag_engine" not in st.session_state:
                    st.session_state.gtd_rag_engine = RAGEngine(RetrievalEngine(collection_names=["incidents"]))
                
                query_text = "\n\n".join([inc.retrieval_text for inc in incidents])
                analysis_prompt = f"Find and generate a concise summary explaining historical events similar to this incident:\n\n{query_text}"
                
                answer, results = st.session_state.gtd_rag_engine.query(analysis_prompt)
                st.markdown("### Similar Historical Incidents Analysis")
                st.info(answer)
                
                if results:
                    with st.expander("Show Retrieved Historical Incidents"):
                        for res in results:
                            st.markdown(f"**Date:** {res.incident.date} | **Location:** {res.incident.city}, {res.incident.state}")
                            st.write(res.incident.summary)
                            st.markdown("---")
        
        st.markdown("---")
        
        # Query UI
        temp_query = st.text_input("Enter your custom query:", key="temp_query", placeholder="e.g. Summarize this report")
        
        st.markdown("<small><b>Examples:</b></small>", unsafe_allow_html=True)
        qcols = st.columns(4)
        if qcols[0].button("Summarize this report"):
            st.session_state.temp_query = "Summarize this report"
            st.rerun()
        if qcols[1].button("Who was targeted?"):
            st.session_state.temp_query = "Who was targeted?"
            st.rerun()
        if qcols[2].button("What attack type was used?"):
            st.session_state.temp_query = "What attack type was used?"
            st.rerun()
        if qcols[3].button("What casualties were reported?"):
            st.session_state.temp_query = "What casualties were reported?"
            st.rerun()

        if st.button("Analyze Document", type="primary"):
            if temp_query.strip():
                with st.spinner(f"Analyzing using scope: {retrieval_scope}..."):
                    answer, results = active_rag.query(temp_query)
                    st.markdown("### Document Analysis")
                    st.info(answer)
                    
                    if results and retrieval_scope != "Uploaded Document Only":
                        with st.expander("Show Retrieved Incidents"):
                            for res in results:
                                st.markdown(f"**Date:** {res.incident.date} | **Location:** {res.incident.city}, {res.incident.state}")
                                st.write(res.incident.summary)
                                st.markdown("---")
            else:
                st.warning("Please enter a query.")
