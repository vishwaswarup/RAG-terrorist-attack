import streamlit as st
import time
import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.retrieval_engine import RetrievalEngine
from rag.rag_engine import RAGEngine

st.title("Intelligence Query")
st.markdown("Execute intelligence queries against the offline knowledge base.")

@st.cache_resource
def load_engines():
    retrieval = RetrievalEngine()
    rag = RAGEngine(retrieval)
    return rag

# Initialize backend models (cached)
with st.spinner("Initializing offline models (BGE Embeddings & Phi3 LLM)..."):
    rag_engine = load_engines()

# Setup query state
if "current_query" not in st.session_state:
    st.session_state.current_query = ""

def set_query(q):
    st.session_state.current_query = q

query = st.text_input("Enter your query:", value=st.session_state.current_query, placeholder="e.g. JeM attacks in Kashmir")

# Example queries beneath the input box
st.markdown("<small><b>Examples:</b></small>", unsafe_allow_html=True)
cols = st.columns(3)
if cols[0].button("JeM attacks in Kashmir"):
    st.session_state.current_query = "JeM attacks in Kashmir"
    st.rerun()
if cols[1].button("Maoist attacks in Chhattisgarh"):
    st.session_state.current_query = "Maoist attacks in Chhattisgarh"
    st.rerun()
if cols[2].button("2008 Mumbai attacks"):
    st.session_state.current_query = "2008 Mumbai attacks"
    st.rerun()

st.markdown("---")

if "has_results" not in st.session_state:
    st.session_state.has_results = False
    st.session_state.answer = ""
    st.session_state.results = []
    st.session_state.elapsed = 0.0

if st.button("Analyze", type="primary"):
    if query.strip():
        with st.spinner("Running retrieval and generating intelligence summary..."):
            start_time = time.time()
            answer, results = rag_engine.query(query)
            st.session_state.elapsed = time.time() - start_time
            st.session_state.answer = answer
            st.session_state.results = results
            st.session_state.has_results = True
    else:
        st.warning("Please enter a query to analyze.")
        st.session_state.has_results = False

if st.session_state.has_results:
    st.markdown("### Analysis")
    st.info(st.session_state.answer)
    
    if st.session_state.results:
        st.caption(f"⏱️ Completed in {st.session_state.elapsed:.2f}s | Retrieved {len(st.session_state.results)} incidents")
        
        show_incidents = st.checkbox("Show Retrieved Incidents", value=False)
        if show_incidents:
            st.markdown("#### Retrieved Incidents")
            for r in st.session_state.results:
                inc = r.incident
                with st.expander(f"{inc.date} - {inc.city}, {inc.state} (Score: {r.score:.3f})"):
                    st.markdown(f"**Date:** {inc.date}")
                    st.markdown(f"**Location:** {inc.city}, {inc.state}, {inc.country}")
                    st.markdown(f"**Attack Type:** {', '.join(inc.attack_types) if inc.attack_types else 'Unknown'}")
                    st.markdown(f"**Responsible Group:** {', '.join(inc.responsible_groups) if inc.responsible_groups else 'Unknown'}")
                    st.markdown("**Retrieval Text:**")
                    st.code(inc.retrieval_text, language="text")
