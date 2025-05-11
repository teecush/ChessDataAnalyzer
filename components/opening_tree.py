import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.pgn_analyzer import get_opening_performance
import numpy as np

def create_opening_tree_visualization(df):
    """
    Create a hierarchical visualization of opening performance with tree-like structure
    showing main openings, variations, and game results
    """
    if df is None or 'PGN' not in df.columns:
        st.warning("PGN data not available. Cannot display opening tree visualization.")
        return
    
    st.subheader("Opening Repertoire Tree")
    
    # Add a filter for white or black side games
    side_filter = st.radio(
        "Filter openings by color:",
        ["All Games", "White Pieces", "Black Pieces"],
        horizontal=True,
        key="opening_tree_side_filter"
    )
    
    # Apply the side filter
    if side_filter == "White Pieces":
        filtered_df = df[df['Side'].str.lower().isin(['w', 'white'])]
        if len(filtered_df) == 0:
            st.info("No games found where you played White.")
            return
    elif side_filter == "Black Pieces":
        filtered_df = df[df['Side'].str.lower().isin(['b', 'black'])]
        if len(filtered_df) == 0:
            st.info("No games found where you played Black.")
            return
    else:
        filtered_df = df
    
    # Get opening performance statistics
    opening_results = get_opening_performance(filtered_df)
    
    # Check if we have data
    if not isinstance(opening_results, dict) or 'opening_df' not in opening_results:
        st.info("No opening data available.")
        return
    
    # Extract all the dataframes from the opening_results dictionary
    opening_df = opening_results['opening_df']
    opening_stats_main = opening_results['opening_stats_main']
    opening_stats_full = opening_results['opening_stats_full']
    
    # Show summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Games", len(filtered_df))
    with col2:
        st.metric("Main Opening Types", len(opening_stats_main))
    with col3:
        st.metric("Specific Variations", len(opening_stats_full))
    
    # Create tabs for different visualization types
    sunburst_tab, treemap_tab, sankey_tab = st.tabs([
        "Opening Sunburst", "Opening Treemap", "Opening Flow"
    ])
    
    with sunburst_tab:
        # Create a sunburst chart (hierarchical pie chart)
        create_sunburst_chart(opening_df, side_filter)
    
    with treemap_tab:
        # Create a treemap visualization
        create_treemap_visualization(opening_df, side_filter)
    
    with sankey_tab:
        # Create a Sankey diagram showing opening flow
        create_sankey_diagram(opening_df, side_filter)
    
    # Show opening stats table with win rates
    with st.expander("Opening Statistics Table", expanded=False):
        # Create a more detailed table with all stats
        create_opening_stats_table(opening_stats_main, opening_stats_full)

def create_sunburst_chart(opening_df, side_filter):
    """Create a sunburst chart showing opening hierarchy and performance"""
    st.subheader(f"Opening Sunburst Chart ({side_filter})")
    
    # Prepare data for the sunburst chart
    # We need: labels (all hierarchy levels), parents (parent of each node), and values (size)
    
    # Create a list of all labels, parents, and values
    labels = []
    parents = []
    values = []
    colors = []
    
    # Add "All Openings" as the root
    labels.append("All Openings")
    parents.append("")  # Root has no parent
    values.append(len(opening_df))
    colors.append("#777777")  # Neutral color for root
    
    # Add main openings
    main_openings = opening_df.groupby("OpeningMain").agg(
        count=("OpeningMain", "count"),
        wins=("Result", lambda x: (x == "win").sum()),
        losses=("Result", lambda x: (x == "loss").sum()),
        draws=("Result", lambda x: (x == "draw").sum())
    ).reset_index()
    
    for _, main in main_openings.iterrows():
        # Skip unknown or empty openings
        if main["OpeningMain"] in ["Unknown", "", None] or pd.isna(main["OpeningMain"]):
            continue
            
        # Add main opening as child of root
        labels.append(main["OpeningMain"])
        parents.append("All Openings")
        values.append(main["count"])
        
        # Determine color based on win rate
        win_rate = main["wins"] / main["count"] if main["count"] > 0 else 0
        
        # Color gradient from red (0% wins) to green (100% wins)
        # Light red for poor results, bright green for good results
        if win_rate < 0.33:
            color = f"rgba(255, {int(255 * win_rate * 3)}, 0, 0.8)"  # Red to yellow
        else:
            color = f"rgba({int(255 * (1 - (win_rate - 0.33) * 1.5))}, 255, 0, 0.8)"  # Yellow to green
            
        colors.append(color)
    
    # Add full openings
    for _, row in opening_df.iterrows():
        main_opening = row["OpeningMain"]
        full_opening = row["OpeningFull"]
        
        # Skip if either is unknown/empty
        if (main_opening in ["Unknown", "", None] or pd.isna(main_opening) or
            full_opening in ["Unknown", "", None] or pd.isna(full_opening) or
            main_opening == full_opening):  # Skip if main and full are the same
            continue
            
        # Check if this full opening is already in labels
        if full_opening not in labels:
            labels.append(full_opening)
            parents.append(main_opening)
            
            # Count games with this full opening
            opening_count = len(opening_df[opening_df["OpeningFull"] == full_opening])
            values.append(opening_count)
            
            # Determine color based on result (win/loss/draw)
            wins = len(opening_df[(opening_df["OpeningFull"] == full_opening) & 
                                  (opening_df["Result"] == "win")])
            win_rate = wins / opening_count if opening_count > 0 else 0
            
            # Use same color scheme as main openings
            if win_rate < 0.33:
                color = f"rgba(255, {int(255 * win_rate * 3)}, 0, 0.8)"
            else:
                color = f"rgba({int(255 * (1 - (win_rate - 0.33) * 1.5))}, 255, 0, 0.8)"
                
            colors.append(color)
    
    # Add variations if they exist
    for _, row in opening_df.iterrows():
        full_opening = row["OpeningFull"]
        variation = row["OpeningVariation"]
        
        # Skip if either is unknown/empty
        if (full_opening in ["Unknown", "", None] or pd.isna(full_opening) or
            variation in ["", None] or pd.isna(variation)):
            continue
            
        # Check if this variation is already in labels
        variation_name = f"{full_opening}: {variation}"
        if variation_name not in labels:
            labels.append(variation_name)
            parents.append(full_opening)
            
            # Count games with this variation
            variation_count = len(opening_df[(opening_df["OpeningFull"] == full_opening) & 
                                            (opening_df["OpeningVariation"] == variation)])
            values.append(variation_count)
            
            # Determine color based on result
            wins = len(opening_df[(opening_df["OpeningFull"] == full_opening) & 
                                 (opening_df["OpeningVariation"] == variation) &
                                 (opening_df["Result"] == "win")])
            win_rate = wins / variation_count if variation_count > 0 else 0
            
            # Use same color scheme
            if win_rate < 0.33:
                color = f"rgba(255, {int(255 * win_rate * 3)}, 0, 0.8)"
            else:
                color = f"rgba({int(255 * (1 - (win_rate - 0.33) * 1.5))}, 255, 0, 0.8)"
                
            colors.append(color)
    
    # Create the sunburst chart
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(
            colors=colors,
            line=dict(width=0.5, color="#000000")
        ),
        hovertemplate='<b>%{label}</b><br>Games: %{value}<br>',
        textinfo="label+percent entry",
        maxdepth=3  # Limit depth for better readability
    ))
    
    fig.update_layout(
        title="Opening Repertoire Breakdown",
        width=800,
        height=800,
        margin=dict(t=30, l=0, r=0, b=0),
        uniformtext=dict(minsize=10, mode='hide'),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: -20px;">
        <small>Colors indicate win rate: red (poor) → yellow (average) → green (good)</small>
    </div>
    """, unsafe_allow_html=True)

def create_treemap_visualization(opening_df, side_filter):
    """Create a treemap visualization of opening performance"""
    st.subheader(f"Opening Treemap ({side_filter})")
    
    # Group by hierarchy
    main_openings = opening_df.groupby(["OpeningMain"]).agg(
        count=("OpeningMain", "count"),
        wins=("Result", lambda x: (x == "win").sum()),
        losses=("Result", lambda x: (x == "loss").sum()),
        draws=("Result", lambda x: (x == "draw").sum())
    ).reset_index()
    
    # Prepare data for treemap
    treemap_labels = []
    treemap_parents = []
    treemap_values = []
    treemap_colors = []
    treemap_text = []
    
    # Add root
    treemap_labels.append("Tony's Openings")
    treemap_parents.append("")
    treemap_values.append(len(opening_df))
    treemap_colors.append("#777777")
    treemap_text.append(f"Total Games: {len(opening_df)}")
    
    # Add main openings
    for _, main in main_openings.iterrows():
        # Skip unknown openings
        if main["OpeningMain"] in ["Unknown", "", None] or pd.isna(main["OpeningMain"]):
            continue
            
        # Get win percentage
        win_pct = round(main["wins"] / main["count"] * 100, 1) if main["count"] > 0 else 0
        
        # Add to treemap
        treemap_labels.append(main["OpeningMain"])
        treemap_parents.append("Tony's Openings")
        treemap_values.append(main["count"])
        
        # Color based on win rate
        if win_pct < 33:
            color = f"rgba(255, {int(255 * win_pct / 33)}, 0, 0.8)"
        elif win_pct < 67:
            color = f"rgba({int(255 * (2 - win_pct/33))}, 255, 0, 0.8)"
        else:
            color = f"rgba(0, 255, {int(255 * (win_pct - 67) / 33)}, 0.8)"
            
        treemap_colors.append(color)
        treemap_text.append(f"Games: {main['count']}<br>Win: {main['wins']} ({win_pct}%)<br>Loss: {main['losses']}<br>Draw: {main['draws']}")
    
    # Add full openings under main openings
    for main_opening in main_openings["OpeningMain"]:
        if main_opening in ["Unknown", "", None] or pd.isna(main_opening):
            continue
            
        # Filter for this main opening
        full_openings = opening_df[opening_df["OpeningMain"] == main_opening].groupby("OpeningFull").agg(
            count=("OpeningFull", "count"),
            wins=("Result", lambda x: (x == "win").sum()),
            losses=("Result", lambda x: (x == "loss").sum()),
            draws=("Result", lambda x: (x == "draw").sum())
        ).reset_index()
        
        for _, full in full_openings.iterrows():
            # Skip if same as main or unknown
            if (full["OpeningFull"] == main_opening or 
                full["OpeningFull"] in ["Unknown", "", None] or 
                pd.isna(full["OpeningFull"])):
                continue
                
            # Get win percentage
            win_pct = round(full["wins"] / full["count"] * 100, 1) if full["count"] > 0 else 0
            
            # Add to treemap
            treemap_labels.append(full["OpeningFull"])
            treemap_parents.append(main_opening)
            treemap_values.append(full["count"])
            
            # Color based on win rate
            if win_pct < 33:
                color = f"rgba(255, {int(255 * win_pct / 33)}, 0, 0.8)"
            elif win_pct < 67:
                color = f"rgba({int(255 * (2 - win_pct/33))}, 255, 0, 0.8)"
            else:
                color = f"rgba(0, 255, {int(255 * (win_pct - 67) / 33)}, 0.8)"
                
            treemap_colors.append(color)
            treemap_text.append(f"Games: {full['count']}<br>Win: {full['wins']} ({win_pct}%)<br>Loss: {full['losses']}<br>Draw: {full['draws']}")
    
    # Create the treemap
    fig = go.Figure(go.Treemap(
        labels=treemap_labels,
        parents=treemap_parents,
        values=treemap_values,
        branchvalues="total",
        marker=dict(
            colors=treemap_colors,
            line=dict(width=0.5, color="#000000")
        ),
        text=treemap_text,
        hovertemplate='<b>%{label}</b><br>%{text}<br>',
        textinfo="label+value",
        maxdepth=2  # Limit depth for better readability
    ))
    
    fig.update_layout(
        title="Opening Repertoire by Games Played",
        width=900,
        height=700,
        margin=dict(t=30, l=0, r=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: -20px;">
        <small>Colors indicate win rate: red (poor) → yellow (average) → green (good)</small>
    </div>
    """, unsafe_allow_html=True)

def create_sankey_diagram(opening_df, side_filter):
    """Create a Sankey diagram showing flow from main openings to results"""
    st.subheader(f"Opening Flow Diagram ({side_filter})")
    
    # Create a flow from: Side (White/Black) → Main Opening → Result
    sides = sorted(opening_df["Side"].unique())
    main_openings = sorted([m for m in opening_df["OpeningMain"].unique() 
                          if m not in ["Unknown", "", None] and not pd.isna(m)])
    results = ["win", "loss", "draw"]
    
    # Prepare Sankey data
    # All node labels
    labels = sides + main_openings + results
    
    # Source indices
    source = []
    # From Side to Main Opening
    for side in sides:
        for main in main_openings:
            # Check if this combination exists
            if len(opening_df[(opening_df["Side"] == side) & 
                           (opening_df["OpeningMain"] == main)]) > 0:
                source.append(sides.index(side))
                
    # From Main Opening to Result
    for main in main_openings:
        for result in results:
            # Check if this combination exists
            if len(opening_df[(opening_df["OpeningMain"] == main) & 
                           (opening_df["Result"] == result)]) > 0:
                source.append(len(sides) + main_openings.index(main))
    
    # Target indices
    target = []
    # From Side to Main Opening
    for side in sides:
        for main in main_openings:
            # Check if this combination exists
            if len(opening_df[(opening_df["Side"] == side) & 
                           (opening_df["OpeningMain"] == main)]) > 0:
                target.append(len(sides) + main_openings.index(main))
                
    # From Main Opening to Result
    for main in main_openings:
        for result in results:
            # Check if this combination exists
            if len(opening_df[(opening_df["OpeningMain"] == main) & 
                           (opening_df["Result"] == result)]) > 0:
                target.append(len(sides) + len(main_openings) + results.index(result))
    
    # Values (number of games)
    value = []
    # From Side to Main Opening
    for side in sides:
        for main in main_openings:
            # Count games with this combination
            games = len(opening_df[(opening_df["Side"] == side) & 
                                 (opening_df["OpeningMain"] == main)])
            if games > 0:
                value.append(games)
                
    # From Main Opening to Result
    for main in main_openings:
        for result in results:
            # Count games with this combination
            games = len(opening_df[(opening_df["OpeningMain"] == main) & 
                                 (opening_df["Result"] == result)])
            if games > 0:
                value.append(games)
    
    # Link colors (based on source)
    link_colors = []
    
    # First links: Side to Opening (White = light blue, Black = gray)
    for side in sides:
        for main in main_openings:
            if len(opening_df[(opening_df["Side"] == side) & 
                           (opening_df["OpeningMain"] == main)]) > 0:
                if side.lower() in ["white", "w"]:
                    link_colors.append("rgba(173, 216, 230, 0.4)")  # Light blue for White
                else:
                    link_colors.append("rgba(128, 128, 128, 0.4)")  # Gray for Black
    
    # Second links: Opening to Result (win = green, loss = red, draw = blue)
    for main in main_openings:
        for result in results:
            if len(opening_df[(opening_df["OpeningMain"] == main) & 
                           (opening_df["Result"] == result)]) > 0:
                if result == "win":
                    link_colors.append("rgba(0, 255, 0, 0.4)")      # Green for wins
                elif result == "loss":
                    link_colors.append("rgba(255, 0, 0, 0.4)")      # Red for losses
                else:
                    link_colors.append("rgba(0, 0, 255, 0.4)")      # Blue for draws
    
    # Node colors
    node_colors = []
    # Colors for sides
    for side in sides:
        if side.lower() in ["white", "w"]:
            node_colors.append("rgba(173, 216, 230, 1)")  # Light blue for White
        else:
            node_colors.append("rgba(128, 128, 128, 1)")  # Gray for Black
    
    # Colors for openings (neutral)
    for _ in main_openings:
        node_colors.append("rgba(200, 200, 200, 1)")
    
    # Colors for results
    node_colors.append("rgba(0, 200, 0, 1)")    # Green for win
    node_colors.append("rgba(200, 0, 0, 1)")    # Red for loss
    node_colors.append("rgba(0, 0, 200, 1)")    # Blue for draw
    
    # Create the Sankey diagram
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors
        )
    ))
    
    fig.update_layout(
        title="Opening Flow: Side → Opening → Result",
        font=dict(size=12),
        height=800,
        width=1000
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add a description
    st.markdown("""
    This diagram shows how your games flow from playing White or Black, through different opening types, 
    to your game results (win/loss/draw). Thicker lines indicate more games played.
    """)

def create_opening_stats_table(main_stats, full_stats):
    """Create a detailed table with opening statistics"""
    # Create two tabs for main openings and full openings
    tab1, tab2 = st.tabs(["Main Opening Types", "Specific Openings"])
    
    with tab1:
        # Main openings table with win rate
        main_df = main_stats.copy()
        main_df['Win %'] = main_df['win_pct']
        main_df['White Games'] = main_df['white']
        main_df['Black Games'] = main_df['black']
        
        # Select columns for display
        display_main = main_df[['OpeningMain', 'total', 'wins', 'losses', 'draws', 'Win %', 'White Games', 'Black Games']]
        display_main.columns = ['Opening', 'Games', 'Wins', 'Losses', 'Draws', 'Win %', 'White', 'Black']
        
        # Show dataframe with formatting
        st.dataframe(
            display_main,
            column_config={
                "Win %": st.column_config.NumberColumn(format="%.1f%%"),
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tab2:
        # Full openings table with win rate
        full_df = full_stats.copy()
        full_df['Win %'] = full_df['win_pct']
        full_df['White Games'] = full_df['white']
        full_df['Black Games'] = full_df['black']
        
        # Select columns for display
        display_full = full_df[['OpeningFull', 'total', 'wins', 'losses', 'draws', 'Win %', 'White Games', 'Black Games']]
        display_full.columns = ['Opening', 'Games', 'Wins', 'Losses', 'Draws', 'Win %', 'White', 'Black']
        
        # Show dataframe with formatting
        st.dataframe(
            display_full,
            column_config={
                "Win %": st.column_config.NumberColumn(format="%.1f%%"),
            },
            hide_index=True,
            use_container_width=True
        )