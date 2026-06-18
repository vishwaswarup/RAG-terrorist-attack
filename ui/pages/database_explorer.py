import streamlit as st
import pandas as pd
from retrieval.chroma_manager import ChromaManager

st.title("🗄️ Database Explorer")

# --- Initialize Managers ---
try:
    gtd_db = ChromaManager("incidents")
    up_db = ChromaManager("uploaded_incidents")
except Exception as e:
    st.error(f"Error initializing ChromaDB: {e}")
    st.stop()

# --- Collection-level Statistics ---
st.header("Intelligence Collections")

gtd_count = gtd_db.count()
up_count = up_db.count()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Historical GTD Incidents", gtd_count)
with col2:
    st.metric("Uploaded Incidents", up_count)
with col3:
    st.metric("Total Searchable Incidents", gtd_count + up_count)

st.markdown("---")

# --- Recent Uploaded Intelligence Section ---
st.header("Recent Uploaded Intelligence")

try:
    # Fetch all uploaded incidents from ChromaDB
    up_results = up_db.collection.get(include=["metadatas", "documents"])
    
    if not up_results['ids']:
        st.info("No user-uploaded intelligence found in the database. Go to 'Upload & Analyze' to add some.")
    else:
        # Build list of dicts for DataFrame
        data = []
        for i in range(len(up_results['ids'])):
            meta = up_results['metadatas'][i]
            meta['retrieval_text'] = up_results['documents'][i]
            data.append(meta)
            
        df = pd.DataFrame(data)
        
        # Display the DataFrame in an interactive table
        display_cols = ['date', 'city', 'state', 'attack_types', 'responsible_groups', 'summary']
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
        
        st.markdown("### Expandable Detail View")
        
        # Iterate through the rows for detailed view
        for index, row in df.iterrows():
            header_title = f"{row.get('date', 'Unknown Date')} - {row.get('city', 'Unknown City')}, {row.get('state', 'Unknown State')}"
            with st.expander(header_title):
                st.markdown(f"**Responsible Groups:** {row.get('responsible_groups', 'Unknown')}")
                st.markdown(f"**Attack Types:** {row.get('attack_types', 'Unknown')}")
                st.markdown(f"**Casualties:** Killed: {row.get('killed', 0)} | Injured: {row.get('injured', 0)}")
                if 'has_summary' in row and bool(row['has_summary']):
                    st.markdown("**Summary:** (Available via Retrieval Text)")
                
                if 'retrieval_text' in row:
                    st.markdown("**Retrieval Text (Vector Payload):**")
                    st.code(row['retrieval_text'], language='text')

except Exception as e:
    st.error(f"Error reading uploaded collection: {e}")
