import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.pgn_analyzer import get_opening_performance, analyze_game
import re

def create_opening_explorer(df):
    """Create an opening explorer section for the dashboard with hierarchical display"""
    if df is None or 'PGN' not in df.columns:
        st.warning("PGN data not available. Cannot display opening explorer.")
        return
    
    st.subheader("Opening Explorer")
    
    # Get opening performance statistics with the new hierarchical structure
    opening_results = get_opening_performance(df)
    
    # Check if we have data
    if not isinstance(opening_results, dict) or 'opening_df' not in opening_results:
        st.info("No opening data available.")
        return
    
    # Extract all the dataframes from the opening_results dictionary
    opening_df = opening_results['opening_df']
    opening_stats_main = opening_results['opening_stats_main']
    opening_stats_full = opening_results['opening_stats_full']
    
    # Create tabs for different views
    overview_tab, main_openings_tab, detailed_tab = st.tabs(["Overview", "Main Openings", "Full Openings"])
    
    with overview_tab:
        # Add a summary of most played openings in a tile format
        st.subheader("Most Played Openings")
        
        # Get top 5 openings for a summary
        top_openings = opening_stats_main.head(5)
        
        # Create tiles for top openings
        for i in range(min(len(top_openings), 5)):
            with st.container():
                st.markdown(f"""
                <div style="
                    border: 1px solid #ddd; 
                    border-radius: 5px; 
                    padding: 10px; 
                    margin-bottom: 10px;
                    background-color: #f8f9fa;
                    ">
                    <h3 style="margin-top: 0;">{top_openings.iloc[i]['OpeningMain']}</h3>
                    <div style="display: flex; justify-content: space-between;">
                        <div><strong>Games:</strong> {int(top_openings.iloc[i]['total'])}</div>
                        <div><strong>Win %:</strong> {top_openings.iloc[i]['win_pct']}%</div>
                        <div style="color: #4CAF50;"><strong>W:</strong> {int(top_openings.iloc[i]['wins'])}</div>
                        <div style="color: #f44336;"><strong>L:</strong> {int(top_openings.iloc[i]['losses'])}</div>
                        <div style="color: #2196F3;"><strong>D:</strong> {int(top_openings.iloc[i]['draws'])}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Overall opening summary
        st.subheader("Opening Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Unique Openings", len(opening_stats_full))
        with col2:
            st.metric("Main Opening Types", len(opening_stats_main))
        with col3:
            # Find side balance
            white_games = opening_df['Side'].str.lower().isin(['white', 'w']).sum()
            black_games = opening_df['Side'].str.lower().isin(['black', 'b']).sum()
            side_balance = f"White: {white_games}, Black: {black_games}"
            st.metric("Side Balance", side_balance)
    
    with main_openings_tab:
        # Display main opening statistics (using the categorized openings)
        st.subheader("Main Opening Types")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create opening distribution chart for main openings
            fig = go.Figure()
            
            # Add bars for each result type (stacked)
            fig.add_trace(go.Bar(
                y=opening_stats_main['OpeningMain'],
                x=opening_stats_main['wins'],
                name='Wins',
                orientation='h',
                marker=dict(color='#4CAF50'),
                hovertemplate='%{x} wins<extra></extra>'
            ))
            
            fig.add_trace(go.Bar(
                y=opening_stats_main['OpeningMain'],
                x=opening_stats_main['losses'],
                name='Losses',
                orientation='h',
                marker=dict(color='#f44336'),
                hovertemplate='%{x} losses<extra></extra>'
            ))
            
            fig.add_trace(go.Bar(
                y=opening_stats_main['OpeningMain'],
                x=opening_stats_main['draws'],
                name='Draws',
                orientation='h',
                marker=dict(color='#2196F3'),
                hovertemplate='%{x} draws<extra></extra>'
            ))
            
            # Update layout
            fig.update_layout(
                title='Main Opening Performance',
                barmode='stack',
                height=500,  # Taller to accommodate more openings
                margin=dict(l=10, r=10, t=60, b=10),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis_title="Number of Games",
                yaxis_title=None,
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Show win percentages for main openings
            st.write("Win Percentages")
            
            # Create win percentage table
            win_pct_df = opening_stats_main[['OpeningMain', 'total', 'win_pct']].copy()
            win_pct_df.columns = ['Opening', 'Games', 'Win %']
            
            # Use Streamlit's dataframe with formatting
            st.dataframe(
                win_pct_df,
                column_config={
                    "Win %": st.column_config.NumberColumn(
                        format="%.1f%%",
                    ),
                },
                hide_index=True,
                use_container_width=True
            )
    
    with detailed_tab:
        # Display full opening statistics
        st.subheader("Full Opening Details")
        
        # Create full opening distribution chart
        fig = go.Figure()
        
        # Limit to top 15 openings for readability
        top_openings = opening_stats_full.head(15)
        
        # Add bars for each result type (stacked)
        fig.add_trace(go.Bar(
            y=top_openings['OpeningFull'],
            x=top_openings['wins'],
            name='Wins',
            orientation='h',
            marker=dict(color='#4CAF50'),
            hovertemplate='%{x} wins<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            y=top_openings['OpeningFull'],
            x=top_openings['losses'],
            name='Losses',
            orientation='h',
            marker=dict(color='#f44336'),
            hovertemplate='%{x} losses<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            y=top_openings['OpeningFull'],
            x=top_openings['draws'],
            name='Draws',
            orientation='h',
            marker=dict(color='#2196F3'),
            hovertemplate='%{x} draws<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Top 15 Specific Openings',
            barmode='stack',
            height=600,  # Taller to accommodate more openings
            margin=dict(l=10, r=10, t=60, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis_title="Number of Games",
            yaxis_title=None,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Interactive opening analysis section
    st.subheader("Opening Analysis")
    
    # Create tabs for different selection methods
    select_tab, browse_tab = st.tabs(["Select Opening", "Browse By Category"])
    
    with select_tab:
        # Two-level selection: first main opening, then specific
        main_options = ["All"] + sorted(opening_stats_main['OpeningMain'].tolist())
        selected_main = st.selectbox(
            "Select main opening type:",
            options=main_options,
            index=0
        )
        
        # Filter specific openings based on the main selection
        if selected_main == "All":
            specific_openings = sorted(opening_stats_full['OpeningFull'].tolist())
        else:
            specific_openings = sorted(opening_df[opening_df['OpeningMain'] == selected_main]['OpeningFull'].unique().tolist())
        
        if not specific_openings:
            st.info(f"No specific variations found for {selected_main}.")
            return
            
        selected_opening = st.selectbox(
            "Select specific opening:",
            options=specific_openings,
            index=0
        )
        
        # Process the selection to find games
        analyze_opening(df, opening_df, selected_opening)
    
    with browse_tab:
        # Organize openings by ECO code if available, otherwise by first letter
        openings_by_category = {}
        
        for idx, row in opening_df.iterrows():
            if pd.notna(row['ECO']) and row['ECO']:
                category = row['ECO'][0]  # Use first letter of ECO code (A-E)
            else:
                # Use first letter of opening name
                category = row['OpeningMain'][0] if pd.notna(row['OpeningMain']) and row['OpeningMain'] else '?'
            
            if category not in openings_by_category:
                openings_by_category[category] = set()
            
            openings_by_category[category].add(row['OpeningFull'])
        
        # Create category tabs if we have meaningful categories
        if openings_by_category:
            categories = sorted(openings_by_category.keys())
            
            # Create a selectbox for categories
            selected_category = st.selectbox(
                "Select opening category:",
                options=categories
            )
            
            # Show openings in that category
            if selected_category:
                openings_in_category = sorted(list(openings_by_category[selected_category]))
                
                selected_cat_opening = st.selectbox(
                    f"Openings in category {selected_category}:",
                    options=openings_in_category
                )
                
                # Process the selection
                analyze_opening(df, opening_df, selected_cat_opening)
        else:
            st.info("No category information available for openings.")
            
def analyze_opening(df, opening_df, selected_opening):
    """Analyze a specific opening and show detailed information"""
    if not selected_opening:
        return
    
    # Get games with this opening
    opening_rows = df[df['PGN'].apply(
        lambda x: re.search(rf'\[Opening\s+"{re.escape(selected_opening)}"\]', x) is not None if pd.notna(x) else False
    )]
    
    if len(opening_rows) == 0:
        st.info(f"No games found with the opening: {selected_opening}")
        return
    
    # Show opening statistics
    games_with_opening = opening_df[opening_df['OpeningFull'] == selected_opening]
    
    # Calculate statistics for this opening
    total_games = len(games_with_opening)
    wins = (games_with_opening['Result'] == 'win').sum()
    losses = (games_with_opening['Result'] == 'loss').sum()
    draws = (games_with_opening['Result'] == 'draw').sum()
    win_pct = round(wins / total_games * 100, 1) if total_games > 0 else 0
    
    # Display metrics for the opening
    st.subheader(f"Analysis: {selected_opening}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Games", total_games)
    with col2:
        st.metric("Wins", wins)
    with col3:
        st.metric("Losses", losses)
    with col4:
        st.metric("Win %", f"{win_pct}%")
    
    # Side distribution for this opening
    white_games = (games_with_opening['Side'].str.lower().isin(['white', 'w'])).sum()
    black_games = (games_with_opening['Side'].str.lower().isin(['black', 'b'])).sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("As White", white_games)
    with col2:
        st.metric("As Black", black_games)
    
    # Add option to filter by side
    side_filter = st.radio(
        "Filter by side:",
        options=["All", "White", "Black"],
        horizontal=True
    )
    
    # Apply side filter - ensure case-insensitive matching
    filtered_rows = opening_rows
    if side_filter != "All":
        filtered_rows = opening_rows[opening_rows['Side'].str.lower() == side_filter.lower()]
        if len(filtered_rows) == 0:
            # Try with initial letter only (W/B)
            filtered_rows = opening_rows[opening_rows['Side'].str.lower() == side_filter[0].lower()]
    
    # Show game list
    if len(filtered_rows) > 0:
        st.subheader(f"Games with {selected_opening}")
        
        # Format the date to show only the date part (no time)
        display_df = filtered_rows.copy()
        display_df['Date'] = display_df['Date'].dt.date
        
        # Sort by date (most recent first)
        display_df = display_df.sort_values('Date', ascending=False)
        
        # Show relevant columns only
        columns_to_show = ['Date', 'Side', 'Result', 'Opponent Name', 'Opp. ELO', 'Accuracy %', 'ACL']
        
        st.dataframe(
            display_df[columns_to_show], 
            use_container_width=True,
            hide_index=True
        )
        
        # Allow selecting a game for detailed analysis
        game_dates = display_df['Date'].astype(str).tolist()
        opponents = display_df['Opponent Name'].tolist()
        game_options = [f"{date} vs {opp}" for date, opp in zip(game_dates, opponents)]
        
        selected_game_idx = st.selectbox(
            "Select a game to analyze:",
            options=range(len(game_options)),
            format_func=lambda x: game_options[x]
        )
        
        # Analyze the selected game
        if selected_game_idx is not None:
            selected_game = display_df.iloc[selected_game_idx]
            pgn = selected_game['PGN']
            
            if pd.notna(pgn) and pgn:
                # Use the player's side from the game data
                player_side = selected_game['Side']
                if player_side == 'W':
                    player_side = 'White'
                elif player_side == 'B':
                    player_side = 'Black'
                
                # Analyze the game
                st.subheader(f"Opening Analysis for Game on {display_df.iloc[selected_game_idx]['Date']} vs {display_df.iloc[selected_game_idx]['Opponent Name']}")
                
                analysis = analyze_game(pgn, player_side)
                if 'error' not in analysis:
                    # Show key insights
                    st.subheader("Key Insights")
                    for insight in analysis['insights']:
                        st.info(insight)
                    
                    # Show opening information
                    st.subheader("Opening Information")
                    eco = analysis['opening_info']['eco']
                    st.write(f"**ECO Code:** {eco if eco else 'Not available'}")
                    
                    # Show the first few moves
                    if len(analysis['moves']) > 0:
                        st.subheader("Key Opening Moves")
                        moves_to_show = min(12, len(analysis['moves']))
                        move_data = []
                        
                        for i in range(moves_to_show):
                            move = analysis['moves'][i]
                            move_data.append({
                                "Move #": move['move_number'],
                                "Side": move['side'],
                                "Move": move['move'],
                                "Comment": move['comment'] if move['comment'] else ""
                            })
                        
                        # Display moves
                        st.dataframe(
                            pd.DataFrame(move_data),
                            use_container_width=True,
                            hide_index=True
                        )
                else:
                    st.error(f"Error analyzing game: {analysis.get('error', 'Unknown error')}")
            else:
                st.warning("PGN data not available for this game.")
    else:
        st.info(f"No games found with {selected_opening} as {side_filter}.")