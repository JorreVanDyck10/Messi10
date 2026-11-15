"""Open de gedeelde app meteen op Nieuwe analyse met de gekozen uploadinstellingen."""
import os
import runpy
from pathlib import Path
import streamlit as st

st.session_state.setdefault('workspace_view', 'Nieuwe analyse')
st.session_state.setdefault('automatic_analysis', os.environ.get('FOOTBALL_UPLOAD_MODE') == 'automatic')
runpy.run_path(str(Path(__file__).with_name('streamlit_app.py')), run_name='__main__')
