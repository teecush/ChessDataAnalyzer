import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.pgn_analyzer import get_opening_performance

def create_opening_explorer(df):
    """Create an opening explorer section for the dashboard"""
    if df is None or 'PGN' not in df.columns:
        st.warning("PGN data not available. Cannot display opening explorer.")
        return
    
    st.subheader("Opening Explorer")
    
    # Get opening performance statistics
    opening_stats = get_opening_performance(df)
    
    if opening_stats.empty:
        st.info("No opening data available.")
        return
    
    # Display opening statistics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create opening distribution chart
        fig = go.Figure()
        
        # Add bars for each result type (stacked)
        fig.add_trace(go.Bar(
            y=opening_stats['Opening'],
            x=opening_stats['wins'],
            name='Wins',
            orientation='h',
            marker=dict(color='#4CAF50'),
            hovertemplate='%{x} wins<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            y=opening_stats['Opening'],
            x=opening_stats['losses'],
            name='Losses',
            orientation='h',
            marker=dict(color='#f44336'),
            hovertemplate='%{x} losses<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            y=opening_stats['Opening'],
            x=opening_stats['draws'],
            name='Draws',
            orientation='h',
            marker=dict(color='#2196F3'),
            hovertemplate='%{x} draws<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Opening Performance',
            barmode='stack',
            height=400,
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
        # Show win percentages
        st.write("Win Percentages by Opening")
        
        # Create win percentage table
        win_pct_df = opening_stats[['Opening', 'total', 'win_pct']].copy()
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
    
    # Add opening details section
    st.subheader("Opening Details")
    
    # Create opening selector
    selected_opening = st.selectbox(
        "Select an opening to explore:",
        options=opening_stats['Opening'].tolist(),
        index=0
    )
    
    # Get variations for the selected opening
    opening_rows = df[df['PGN'].apply(
        lambda x: selected_opening in x if pd.notna(x) and x else False
    )]
    
    if len(opening_rows) > 0:
        # Show statistics for this opening
        opening_data = opening_stats[opening_stats['Opening'] == selected_opening].iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Games", int(opening_data['total']))
        with col2:
            st.metric("Wins", int(opening_data['wins']))
        with col3:
            st.metric("Losses", int(opening_data['losses']))
        with col4:
            st.metric("Win %", f"{opening_data['win_pct']}%")
        
        # Show games with this opening
        st.write(f"Games played with {selected_opening}:")
        
        # Add option to filter by side
        side_filter = st.radio(
            "Filter by side:",
            options=["All", "White", "Black"],
            horizontal=True
        )
        
        # Apply side filter
        if side_filter != "All":
            opening_rows = opening_rows[opening_rows['Side'] == side_filter]
        
        # Format the date to show only the date part (no time)
        display_df = opening_rows.copy()
        display_df['Date'] = display_df['Date'].dt.date
        
        # Sort by date (most recent first)
        display_df = display_df.sort_values('Date', ascending=False)
        
        # Show relevant columns only
        if not display_df.empty:
            columns_to_show = ['Date', 'Side', 'Result', 'Opponent Name', 'Opp. ELO', 'Accuracy %', 'ACL']
            st.dataframe(
                display_df[columns_to_show], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(f"No games found with {selected_opening} as {side_filter}.")
    else:
        st.info(f"No games found with the opening: {selected_opening}")