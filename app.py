import streamlit as st
import pandas as pd
from utils.google_sheets import get_google_sheets_data
from utils.data_processor import process_chess_data, calculate_statistics
from utils.ml_analysis import generate_performance_insights
from components.charts import (create_rating_progression, create_win_loss_pie,
                             create_performance_charts)
from components.filters import create_filters, apply_filters

# Page configuration
st.set_page_config(
    page_title="TeeCush's Chess Analytics Dashboard",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with collapsed sidebar on mobile
)

# Load custom CSS
with open('assets/chess_style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# App header
st.markdown("""
    <div class='chess-header'>
        <h1>♟️ TeeCush's Chess Analytics Dashboard</h1>
        <p>Track and analyze your chess performance</p>
    </div>
""", unsafe_allow_html=True)

# Add links
st.markdown("""
    <div class='chess-links'>
        <a href="https://lichess.org/study/aatGfpd6/C8WS6Cy8" target="_blank">Lichess Study</a> | 
        <a href="https://www.chess.com/library/collections/tonyc-annex-chess-club-games-H8SCFdtS" target="_blank">Chess.com Library</a> | 
        <a href="https://docs.google.com/spreadsheets/d/1Z1zFDzVF0_zxEuH3AwBNy8or2SYmpulRnKn2OYvSo5Q/edit?gid=0#gid=0" target="_blank">Chess Data Google Sheet</a> | 
        <a href="https://www.chess.ca/en/ratings/p/?id=184535" target="_blank">CFC Ranking</a>
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

    # Display metrics in expander
    with st.expander("Tournament Statistics", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Games", stats['total_games'])
        with col2:
            st.metric("Current Rating", f"{stats['current_rating']:.0f}")
        with col3:
            st.metric("Win Percentage", f"{stats['win_percentage']:.1f}%")

    # Create performance metric charts
    st.subheader("Performance Metrics")
    performance_charts = create_performance_charts(filtered_df)

    # Display charts in tabs
    # Changed tab order per request: Rating, Results, Accuracy, ACL, Game Rating, Performance Rating
    tab1, tab2 = st.tabs(["Rating", "Results"])

    with tab1:
        st.plotly_chart(create_rating_progression(filtered_df), use_container_width=True)

    with tab2:
        st.plotly_chart(create_win_loss_pie(filtered_df), use_container_width=True)
    
    # Accuracy metrics section
    st.subheader("Accuracy Metrics")
    accuracy_tab, acl_tab = st.tabs(["Accuracy %", "Average Centipawn Loss (ACL)"])
    
    with accuracy_tab:
        st.plotly_chart(performance_charts['accuracy'], use_container_width=True)
    
    with acl_tab:
        st.plotly_chart(performance_charts['acl'], use_container_width=True)
        
    # Game ratings section
    st.subheader("Rating Metrics")
    game_tab, perf_tab = st.tabs(["Game Rating", "Performance Rating"])
    
    with game_tab:
        st.plotly_chart(performance_charts['game_rating'], use_container_width=True)
        
    with perf_tab:
        st.plotly_chart(performance_charts['performance_rating'], use_container_width=True)

    # ML-based Analysis Section
    if len(filtered_df) >= 5:  # Only show ML analysis if we have enough games
        with st.expander("AI Performance Analysis", expanded=False):
            with st.spinner("Generating AI insights..."):
                insights = generate_performance_insights(filtered_df)

                tab1, tab2, tab3 = st.tabs(["Insights", "Analysis", "Tips"])

                with tab1:
                    for insight in insights['text_insights']:
                        if insight.startswith(('📈', '📊', '🎯', '⚖️')):
                            st.info(insight)
                        elif insight.startswith(('⚔️', '🧮', '🏰')):
                            st.warning(insight)
                        else:
                            st.success(insight)

                with tab2:
                    st.dataframe(insights['performance_clusters'], use_container_width=True)

                with tab3:
                    recommendations = [
                        insight for insight in insights['text_insights'] 
                        if any(insight.startswith(emoji) for emoji in ['🎯', '⚔️', '🧮', '🏰', '🧘‍♂️', '⏰', '🌟'])
                    ]
                    for rec in recommendations:
                        st.success(rec)
    else:
        st.info("Need at least 5 games for AI analysis")

    # Display raw data table - show all games, reverse order, and hide # column
    with st.expander("Game History", expanded=False):
        if len(filtered_df) > 0:
            # Create a copy of the dataframe to avoid modifying the original
            display_df = filtered_df.copy()
            
            # Drop the # column since we don't need to show it
            if '#' in display_df.columns:
                display_df = display_df.drop(columns=['#'])
            
            # Sort by Date in descending order (most recent first)
            display_df = display_df.sort_values('Date', ascending=False)
            
            # Show all games at once
            st.dataframe(display_df, use_container_width=True)

if __name__ == "__main__":
    main()