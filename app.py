import streamlit as st
import pandas as pd
from utils.google_sheets import get_google_sheets_data
from utils.data_processor import process_chess_data, calculate_statistics
from components.charts import create_rating_progression
from components.filters import create_filters, apply_filters

# Page configuration
st.set_page_config(
    page_title="Chess Analytics Dashboard",
    page_icon="♟️",
    layout="wide"
)

# Load custom CSS
with open('assets/chess_style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# App header
st.markdown("""
    <div class='chess-header'>
        <h1>♟️ Chess Analytics Dashboard</h1>
        <p>Track and analyze your chess performance</p>
    </div>
""", unsafe_allow_html=True)

# Load and process data
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def load_data():
    df = get_google_sheets_data()
    if df is not None:
        return process_chess_data(df)
    return None

# Main app
def main():
    # Load data
    with st.spinner('Fetching chess data...'):
        df = load_data()

    if df is None:
        st.error("Failed to load chess data. Please check the connection and try again.")
        return

    # Create filters
    filters = create_filters(df)
    filtered_df = apply_filters(df, filters)

    # Calculate statistics
    stats = calculate_statistics(filtered_df)

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Games", stats['total_games'])
    with col2:
        st.metric("Average Rating", f"{stats['avg_rating']:.0f}")
    with col3:
        st.metric("Tournament Performance", f"{stats['tournament_performance']:.0f}")

    # Create charts
    st.subheader("Rating Progression")
    st.plotly_chart(create_rating_progression(filtered_df), use_container_width=True)

if __name__ == "__main__":
    main()