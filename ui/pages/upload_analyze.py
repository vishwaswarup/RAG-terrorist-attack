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
            if doc.metadata.get("image_embedding"):
                st.write("✓ Visual Embedding Generated (OpenCLIP)")
            st.write("✓ Document Object Created")
            st.write(f"Debug: source_type={doc.source_type}, extractor={doc.metadata.get('extractor')}")
            st.session_state.document_text = doc.raw_text
            st.session_state.document_obj = doc
            
            # 2. Process Document (Extract incidents or Image Asset)
            st.write("⚙ Extracting intelligence objects...")
            incidents = process_document(doc)
            st.session_state.extracted_incidents = incidents
            
            st.write("✓ Extraction Complete")
            
            status.update(label="Extraction Complete!", state="complete", expanded=False)
            st.session_state.extraction_complete = True

if st.session_state.extraction_complete and st.session_state.extracted_incidents is not None:
    incidents = st.session_state.extracted_incidents
    
    from models.image_asset import ImageAsset
    incidents_only = [inc for inc in incidents if not isinstance(inc, ImageAsset)]
    assets_only = [inc for inc in incidents if isinstance(inc, ImageAsset)]
    
    if assets_only and incidents_only:
        st.success(f"Successfully processed 1 image asset and extracted **{len(incidents_only)}** incident(s).")
    elif assets_only:
        st.success("Successfully processed image asset.")
    else:
        st.success(f"Successfully extracted **{len(incidents_only)}** incident(s).")
    
    with st.expander("Show Extracted Raw Text"):
        st.code(st.session_state.document_text, language="text")
        
    st.markdown("### Extracted Intelligence")
    for i, inc in enumerate(incidents):
        if isinstance(inc, ImageAsset):
            with st.container(border=True):
                st.markdown(f"**Image Asset Created**")
                st.markdown(f"**Filename:** {inc.filename}")
                st.markdown("**Generated Caption:**")
                st.info(inc.caption)
                st.markdown("**OCR Text:**")
                st.markdown(inc.ocr_text if inc.ocr_text else "*(No text detected)*")
        else:
            with st.container(border=True):
                st.markdown(f"**Incident #{i+1}**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Date:** {inc.date or 'Unknown'}")
                    st.markdown(f"**Location:** {inc.city or 'Unknown'}, {inc.state or 'Unknown'}, {inc.country or 'Unknown'}")
                    st.markdown(f"**Attack Types:** {', '.join(inc.attack_types) if inc.attack_types else 'Unknown'}")
                    st.markdown(f"**Target Types:** {', '.join(inc.target_types) if inc.target_types else 'Unknown'}")
                with col2:
                    st.markdown(f"**Responsible Groups:** {', '.join(inc.responsible_groups) if inc.responsible_groups else 'Unknown'}")
                    st.markdown(f"**Weapon Types:** {', '.join(inc.weapon_types) if inc.weapon_types else 'Unknown'}")
                    st.markdown(f"**Casualties:** Killed: {inc.killed} | Injured: {inc.injured}")
                
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
                incidents_only = [inc for inc in incidents if not isinstance(inc, ImageAsset)]
                assets_only = [inc for inc in incidents if isinstance(inc, ImageAsset)]
                
                if incidents_only:
                    documents = [inc.retrieval_text for inc in incidents_only]
                    embeddings = embedder.embed_documents(documents)
                    db.add_incidents(incidents_only, embeddings)
                
                if assets_only:
                    for asset in assets_only:
                        # Create text embedding for the asset's retrieval text
                        text_emb = embedder.embed_documents([asset.retrieval_text])[0]
                        # Assume image embedding is already in the asset from ingestion
                        db.add_image_asset(asset, text_emb, asset.image_embedding)
                
                st.success("Successfully added to Knowledge Base!")
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
                    candidates.append(RetrievalResult(payload=self.incidents[i], score=float(sim)))
                    
                candidates.sort(key=lambda x: x.score, reverse=True)
                
                # Apply absolute threshold to avoid returning completely irrelevant garbage
                candidates = [c for c in candidates if c.score > 0.25]
                candidates = candidates[:top_k]
                
                if similarity_window is not None and candidates:
                    best = candidates[0].score
                    candidates = [c for c in candidates if c.score >= best - similarity_window]
                    
                return candidates

        # Determine which RAGEngine to use based on scope
        if retrieval_scope == "Uploaded Document Only":
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
        
        def set_query(q):
            st.session_state.temp_query = q

        temp_query = st.text_input("Enter your custom query:", key="temp_query", placeholder="e.g. Summarize this report")
        
        st.markdown("<small><b>💡 Example Queries:</b></small>", unsafe_allow_html=True)
        qcols = st.columns(4)
        qcols[0].button("Summarize this report", use_container_width=True, on_click=set_query, args=("Summarize this report",))
        qcols[1].button("Who was targeted?", use_container_width=True, on_click=set_query, args=("Who was targeted?",))
        qcols[2].button("What attack type was used?", use_container_width=True, on_click=set_query, args=("What attack type was used?",))
        qcols[3].button("What casualties were reported?", use_container_width=True, on_click=set_query, args=("What casualties were reported?",))

        if st.button("Analyze Document", type="primary", use_container_width=True):
            if temp_query.strip():
                with st.status("Analyzing Intelligence...", expanded=True) as status:
                    st.write(f"🔍 Understanding query (Scope: {retrieval_scope})...")
                    import time
                    time.sleep(0.2)
                    st.write("📚 Searching document context...")
                    time.sleep(0.2)
                    st.write("📊 Ranking incidents...")
                    start_time = time.time()
                    answer, results = active_rag.query(temp_query)
                    st.write("📝 Generating response...")
                    elapsed = time.time() - start_time
                    status.update(label="Analysis Complete!", state="complete", expanded=False)
                    
                st.success("✅ Document Analysis completed successfully!")
                
                # Query Summary Card
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Query", temp_query[:25] + "..." if len(temp_query) > 25 else temp_query)
                    col2.metric("Incidents Retrieved", len(results))
                    col3.metric("Response Time", f"{elapsed:.2f}s")
                
                st.markdown("### Document Analysis Report")
                st.info(answer)
                
                if results:
                    st.markdown("### Retrieved Data")
                    from models.image_asset import ImageAsset
                    for res in results:
                        if isinstance(res.payload, ImageAsset):
                            with st.expander(f"Image Asset: {res.payload.filename} (Score: {res.score:.2f})"):
                                st.write(f"**Caption:** {res.payload.caption}")
                        else:
                            inc = res.payload
                            score_badge = f"High Match ({res.score:.2f})" if res.score > 0.8 else f"Match ({res.score:.2f})"
                            with st.expander(f"{inc.date or 'Unknown'} | {inc.city or 'Unknown'}, {inc.state or 'Unknown'} | {score_badge}"):
                                colA, colB = st.columns(2)
                                with colA:
                                    st.markdown(f"**Date:** {inc.date or 'Unknown'}")
                                    st.markdown(f"**Location:** {inc.city or 'Unknown'}, {inc.state or 'Unknown'}, {inc.country or 'Unknown'}")
                                    st.markdown(f"**Attack Type:** {', '.join(inc.attack_types) if inc.attack_types else 'Unknown'}")
                                with colB:
                                    st.markdown(f"**Responsible Group:** {', '.join(inc.responsible_groups) if inc.responsible_groups else 'Unknown'}")
                                    st.markdown(f"**Weapon Type:** {', '.join(inc.weapon_types) if inc.weapon_types else 'Unknown'}")
                                    st.markdown(f"**Similarity Score:** {res.score:.4f}")
                                
                                st.markdown("**Summary:**")
                                st.info(inc.summary)
            else:
                st.warning("Please enter a query.")
