import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables (e.g. LLM_MODEL)
load_dotenv()

st.set_page_config(
    page_title="Intelligence Analysis System",
    page_icon="🛡️",
    layout="wide"
)

# Setup paths using __file__ to ensure robust relative routing
current_dir = os.path.dirname(os.path.abspath(__file__))

pages = {
    "Intelligence": [
        st.Page(os.path.join(current_dir, "pages", "intelligence_query.py"), title="Intelligence Query", icon="🔍"),
        st.Page(os.path.join(current_dir, "pages", "upload_analyze.py"), title="Upload & Analyze", icon="📄")
    ],
    "System Overview": [
        st.Page(os.path.join(current_dir, "pages", "database_explorer.py"), title="Database Explorer", icon="🗄️"),
        st.Page(os.path.join(current_dir, "pages", "system_dashboard.py"), title="System Dashboard", icon="⚙️")
    ]
}

pg = st.navigation(pages)
pg.run()
