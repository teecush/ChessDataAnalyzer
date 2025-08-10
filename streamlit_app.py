import streamlit as st
import pandas as pd
from utils.google_sheets import get_google_sheets_data
from utils.data_processor import process_chess_data, calculate_statistics, get_opening_stats
from utils.ml_analysis import generate_performance_insights
from components.charts import (create_rating_progression, create_win_loss_pie,
                             create_performance_charts, create_opening_bar)
from components.filters import create_filters, apply_filters
from components.opening_explorer import create_opening_explorer
from components.game_analyzer import create_game_analyzer
from components.opening_tree import create_opening_tree_visualization

# Page configuration
st.set_page_config(
    page_title="TeeCush's Chess Analytics Dashboard",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS
try:
    with open('assets/chess_style.css', 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    # Fallback inline CSS
    st.markdown("""
    <style>
    .chess-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .chess-header h1 {
        margin: 0;
        font-size: 2.5em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .chess-links {
        text-align: center;
        margin: 20px 0;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    .chess-links a {
        color: #007bff;
        text-decoration: none;
        margin: 0 10px;
        font-weight: 500;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

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
        <a href="https://docs.google.com/spreadsheets/d/1Z1zFDzVF0_zxEuH3AwBNy8or2SYmpulRnKn2OYvSo5Q/edit?gid=0#gid=0" target="_blank">Google Sheet</a> | 
        <a href="https://www.chess.ca/en/ratings/p/?id=184535" target="_blank">CFC Ranking</a>
    </div>
""", unsafe_allow_html=True)

# Load and process data
@st.cache_data(ttl=600)
def load_data():
    try:
        df = get_google_sheets_data()
        if df is not None and not df.empty:
            return process_chess_data(df)
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Main app
def main():
    # Load data
    with st.spinner('Fetching chess data...'):
        df = load_data()

    if df is None or df.empty:
        st.error("Failed to load chess data. Please check the connection and try again.")
        st.info("Make sure the Google Sheet is published to the web and publicly accessible.")
        
        # Show some basic info even if data fails
        st.subheader("About This Dashboard")
        st.write("This dashboard analyzes chess performance data from Google Sheets.")
        st.write("To fix the connection issue:")
        st.write("1. Ensure the Google Sheet is published to the web")
        st.write("2. Check that the sheet has the correct column format")
        st.write("3. Verify the sheet ID is correct")
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

    # Create performance metric charts with side filtering
    st.subheader("Performance Metrics")
    performance_charts = create_performance_charts(filtered_df, filters['side_filter'])

    # Display charts in tabs
    tab1, tab2 = st.tabs(["Rating", "Results"])

    with tab1:
        st.plotly_chart(create_rating_progression(filtered_df, filters['side_filter']), use_container_width=True)

    with tab2:
        st.plotly_chart(create_win_loss_pie(filtered_df, filters['side_filter']), use_container_width=True)
    
    # Accuracy metrics section
    st.subheader("Accuracy Metrics")
    accuracy_tab, acl_tab = st.tabs(["Accuracy %", "ACL"])
    
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
    if len(filtered_df) >= 5:
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

    # Opening Tree Visualization section
    if 'PGN' in filtered_df.columns:
        with st.expander("Opening Repertoire Tree", expanded=True):
            create_opening_tree_visualization(filtered_df)
    
    # Opening Explorer section
    if 'PGN' in filtered_df.columns:
        with st.expander("Opening Explorer", expanded=False):
            create_opening_explorer(filtered_df)
            
    # Game Analysis section
    if 'PGN' in filtered_df.columns:
        with st.expander("Game Analysis", expanded=False):
            create_game_analyzer(filtered_df)
    
    # Display raw data table
    with st.expander("Game History", expanded=False):
        if len(filtered_df) > 0:
            display_df = filtered_df.copy()
            
            columns_to_drop = []
            if '#' in display_df.columns:
                columns_to_drop.append('#')
            if 'sparkline data' in display_df.columns:
                columns_to_drop.append('sparkline data')
            if 'RESULT' in display_df.columns:
                columns_to_drop.append('RESULT')
            if 'Performance Rating' in display_df.columns:
                columns_to_drop.append('Performance Rating')
            if 'New Rating' in display_df.columns:
                columns_to_drop.append('New Rating')
            if 'Game Rating' in display_df.columns:
                columns_to_drop.append('Game Rating')
            if 'PGN' in display_df.columns:
                columns_to_drop.append('PGN')
            
            if columns_to_drop:
                display_df = display_df.drop(columns=columns_to_drop)
            
            display_df['Date'] = display_df['Date'].dt.date
            display_df = display_df.sort_values('Date', ascending=False)
            
            column_order = ['Date', 'Side', 'Result', 'ACL', 'Accuracy %', 'Opponent Name', 'Opp. ELO']
            display_df = display_df[column_order]
            
            st.subheader("Search by Opponent")
            opponent_search = st.text_input("Enter opponent name to search", "", key="opponent_search")
            
            if opponent_search:
                display_df = display_df[display_df['Opponent Name'].str.lower().str.contains(opponent_search.lower())]
                st.write(f"Found {len(display_df)} games against opponents matching '{opponent_search}'")
            
            st.dataframe(display_df, use_container_width=True)

if __name__ == "__main__":
    main()