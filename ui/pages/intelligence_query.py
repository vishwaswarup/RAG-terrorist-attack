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
with st.spinner(f"Initializing offline models (BGE Embeddings & {os.environ.get('LLM_MODEL', 'qwen3:8b').upper()} LLM)..."):
    rag_engine = load_engines()

# Setup query state
if "current_query" not in st.session_state:
    st.session_state.current_query = ""

def set_query(q):
    st.session_state.current_query = q

query = st.text_input("Enter your query:", value=st.session_state.current_query, placeholder="e.g. JeM attacks in Kashmir")

# Example queries beneath the input box
st.markdown("<small><b>Example Queries:</b></small>", unsafe_allow_html=True)
cols = st.columns(3)
if cols[0].button("JeM attacks in Kashmir", use_container_width=True):
    st.session_state.current_query = "JeM attacks in Kashmir"
    st.rerun()
if cols[1].button("Maoist attacks in Chhattisgarh", use_container_width=True):
    st.session_state.current_query = "Maoist attacks in Chhattisgarh"
    st.rerun()
if cols[2].button("2008 Mumbai attacks", use_container_width=True):
    st.session_state.current_query = "2008 Mumbai attacks"
    st.rerun()

st.markdown("---")

if "has_results" not in st.session_state:
    st.session_state.has_results = False
    st.session_state.answer = ""
    st.session_state.results = []
    st.session_state.elapsed = 0.0

if st.button("Analyze", type="primary", use_container_width=True):
    if query.strip():
        with st.status("Analyzing Intelligence...", expanded=True) as status:
            st.write("Understanding query...")
            time.sleep(0.2)
            st.write("Searching knowledge base...")
            time.sleep(0.2)
            st.write("Ranking incidents...")
            start_time = time.time()
            answer, results = rag_engine.query(query)
            st.write("Generating response...")
            st.session_state.elapsed = time.time() - start_time
            st.session_state.answer = answer
            st.session_state.results = results
            st.session_state.has_results = True
            st.session_state.last_query = query
            status.update(label="Analysis Complete", state="complete", expanded=False)
            st.rerun()
    else:
        st.warning("Please enter a query to analyze.")
        st.session_state.has_results = False

if st.session_state.has_results:
    st.success("Analysis completed successfully.")
    
    # Query Summary Card
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Query", st.session_state.last_query[:25] + "..." if len(st.session_state.last_query) > 25 else st.session_state.last_query)
        col2.metric("Incidents Retrieved", len(st.session_state.results))
        col3.metric("Response Time", f"{st.session_state.elapsed:.2f}s")
        
    st.markdown("### Analysis Report")
    st.info(st.session_state.answer)
    
    if st.session_state.results:
        st.markdown("### Retrieved Incidents")
        for r in st.session_state.results:
            inc = r.incident
            score_badge = f"High Match ({r.score:.2f})" if r.score > 0.8 else f"Match ({r.score:.2f})"
            with st.expander(f"{inc.date or 'Unknown'} | {inc.city or 'Unknown'}, {inc.state or 'Unknown'} | {score_badge}"):
                colA, colB = st.columns(2)
                with colA:
                    st.markdown(f"**Date:** {inc.date or 'Unknown'}")
                    st.markdown(f"**Location:** {inc.city or 'Unknown'}, {inc.state or 'Unknown'}, {inc.country or 'Unknown'}")
                    st.markdown(f"**Attack Type:** {', '.join(inc.attack_types) if inc.attack_types else 'Unknown'}")
                with colB:
                    st.markdown(f"**Responsible Group:** {', '.join(inc.responsible_groups) if inc.responsible_groups else 'Unknown'}")
                    st.markdown(f"**Weapon Type:** {', '.join(inc.weapon_types) if inc.weapon_types else 'Unknown'}")
                    st.markdown(f"**Similarity Score:** {r.score:.4f}")
                
                st.markdown("**Retrieval Text:**")
                st.code(inc.retrieval_text, language="text")
