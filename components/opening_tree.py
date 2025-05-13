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
        horizontal=True
    )
    
    # Extract openings data
    opening_df = get_opening_performance(df)
    
    # Apply side filtering if needed
    if side_filter == "White Pieces":
        filtered_df = df[df["Side"].str.lower().isin(["w", "white"])]
        opening_df = get_opening_performance(filtered_df)
    elif side_filter == "Black Pieces":
        filtered_df = df[df["Side"].str.lower().isin(["b", "black"])]
        opening_df = get_opening_performance(filtered_df)
    else:
        filtered_df = df
    
    # If no data after filtering, show a message
    if len(filtered_df) == 0:
        st.info(f"No games found for {side_filter}")
        return
    
    # Process the openings data
    opening_results = get_opening_performance(filtered_df)
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
        # Create a Sankey diagram showing flow between openings and results
        create_sankey_diagram(opening_df, side_filter)
    
    # Display table of opening stats
    st.subheader("Opening Statistics")
    create_opening_stats_table(opening_stats_main, opening_stats_full)

def create_sunburst_chart(opening_df, side_filter):
    """Create sunburst charts showing opening hierarchy and performance for both White and Black"""
    
    # If we're filtering by a single side, show only one sunburst
    if side_filter in ["White Pieces", "Black Pieces"]:
        create_single_sunburst(opening_df, side_filter)
        return
    
    # Otherwise, split into two tabs - White and Black
    sunburst_tabs = st.tabs(["All Games", "White Pieces", "Black Pieces"])
    
    # Fix to ensure side filtering works correctly
    opening_df = opening_df.copy()
    
    with sunburst_tabs[0]:
        create_single_sunburst(opening_df, "All Games")
        
    with sunburst_tabs[1]:
        white_df = opening_df[opening_df['Side'].str.lower().isin(['w', 'white'])]
        if len(white_df) > 0:
            create_single_sunburst(white_df, "White Pieces")
        else:
            st.info("No games found where you played White.")
            
    with sunburst_tabs[2]:
        black_df = opening_df[opening_df['Side'].str.lower().isin(['b', 'black'])]
        if len(black_df) > 0:
            create_single_sunburst(black_df, "Black Pieces")
        else:
            st.info("No games found where you played Black.")

def create_single_sunburst(opening_df, side_filter, show_title=True):
    """Create a simple sunburst chart showing opening hierarchy and performance"""
    if show_title:
        st.subheader(f"Opening Results ({side_filter})")
    
    # We'll display the legend at the bottom, after the visualization
    
    # Check if we have data
    if len(opening_df) == 0:
        st.warning("No data available for this filter")
        return
    
    # Make a copy of the dataframe
    opening_df = opening_df.copy()
    
    # Ensure we have OpeningMain values
    opening_df['OpeningMain'] = opening_df['OpeningMain'].fillna("Unknown")
    
    # Calculate stats for main openings
    main_stats = opening_df.groupby('OpeningMain').agg(
        count=('OpeningMain', 'count'),
        wins=('Result', lambda x: (x == 'win').sum()),
        losses=('Result', lambda x: (x == 'loss').sum()),
        draws=('Result', lambda x: (x == 'draw').sum())
    ).reset_index()
    
    # Calculate win rates
    main_stats['win_pct'] = main_stats.apply(
        lambda row: (row['wins'] / row['count'] * 100) if row['count'] > 0 else 0, 
        axis=1
    )
    
    # Basic sunburst data structure
    labels = ["All Openings"]
    parents = [""]
    values = [len(opening_df)]
    
    # Color for the root node based on side
    if side_filter == "White Pieces":
        root_color = "rgba(255, 255, 255, 0.9)"  # White
    elif side_filter == "Black Pieces":
        root_color = "rgba(128, 128, 128, 0.9)"  # Gray
    else:
        root_color = "rgba(180, 180, 220, 0.9)"  # Purple
        
    colors = [root_color]
    hover_texts = [f"Total Games: {len(opening_df)}"]
    
    # Add main openings as first level
    for _, row in main_stats.iterrows():
        if row['OpeningMain'] == "Unknown":
            continue
            
        # Calculate win percentage for display
        win_pct = row['win_pct']
        win_pct_display = int(round(win_pct, 0))
        
        # Add to sunburst
        label = f"{row['OpeningMain']} ({win_pct_display}%)"
        labels.append(label)
        parents.append("All Openings")
        values.append(row['count'])
        
        # Determine color based on win percentage
        if win_pct <= 20:
            color = "#f23628"  # Deep red
        elif win_pct <= 35:
            color = "#f2cbdc"  # Pink
        elif win_pct <= 65:
            color = "rgba(255, 215, 0, 0.8)"  # Yellow
        elif win_pct <= 80:
            color = "rgba(144, 238, 144, 0.8)"  # Light green
        elif win_pct <= 95:
            color = "rgba(0, 128, 0, 0.8)"  # Dark green
        else:
            color = "#389ae4"  # Blue
            
        colors.append(color)
        hover_texts.append(f"Games: {row['count']}<br>Wins: {row['wins']}<br>Draws: {row['draws']}<br>Losses: {row['losses']}")
    
    # Add variations for each main opening
    # Get unique full openings that aren't the same as main openings
    variations = opening_df[opening_df['OpeningFull'] != opening_df['OpeningMain']]
    
    # Group variations by both main and full opening
    var_stats = variations.groupby(['OpeningMain', 'OpeningFull']).agg(
        count=('OpeningFull', 'count'),
        wins=('Result', lambda x: (x == 'win').sum()),
        losses=('Result', lambda x: (x == 'loss').sum()),
        draws=('Result', lambda x: (x == 'draw').sum())
    ).reset_index()
    
    # Add each variation
    for _, row in var_stats.iterrows():
        main_opening = row['OpeningMain']
        full_opening = row['OpeningFull']
        
        if pd.isna(main_opening) or pd.isna(full_opening):
            continue
            
        # Get variation name by removing main opening
        variation = full_opening.replace(f"{main_opening} ", "").strip()
        if not variation:
            variation = "Main Line"
            
        # Find parent in labels list
        parent_idx = -1
        for i, label in enumerate(labels):
            # Check if this is the parent main opening (strip off the win % for comparison)
            if label.startswith(main_opening) and parents[i] == "All Openings":
                parent_idx = i
                break
                
        if parent_idx < 0:
            continue  # Skip if parent not found
            
        # Calculate win percentage
        # Calculate win percentage, counting draws as 0.5 wins
        win_pct = ((row['wins'] + 0.5 * row['draws']) / row['count'] * 100) if row['count'] > 0 else 0
        win_pct_display = int(round(win_pct, 0))
        
        # Add to sunburst
        labels.append(f"{variation} ({win_pct_display}%)")
        parents.append(labels[parent_idx])
        values.append(row['count'])
        
        # Determine color using same scheme
        if win_pct <= 20:
            color = "#f23628"  # Deep red
        elif win_pct <= 35:
            color = "#f2cbdc"  # Pink
        elif win_pct <= 65:
            color = "rgba(255, 215, 0, 0.8)"  # Yellow
        elif win_pct <= 80:
            color = "rgba(144, 238, 144, 0.8)"  # Light green
        elif win_pct <= 95:
            color = "rgba(0, 128, 0, 0.8)"  # Dark green
        else:
            color = "#389ae4"  # Blue
            
        colors.append(color)
        hover_texts.append(f"Games: {row['count']}<br>Wins: {row['wins']}<br>Draws: {row['draws']}<br>Losses: {row['losses']}")
    
    # Create simple sunburst visualization
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(color="white", width=1)
        ),
        text=hover_texts,
        hovertemplate='<b>%{label}</b><br>%{text}<extra></extra>',
        branchvalues="total"  # Use total so children add up to parent
    ))
    
    fig.update_layout(
        margin=dict(t=30, l=0, r=0, b=0),
        height=700
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display a smaller color legend at the bottom
    st.markdown("<p style='text-align:center;font-size:0.7em;'><i>Win Rate Color Legend</i></p>", unsafe_allow_html=True)
    cols = st.columns(12)
    
    with cols[0]:
        st.markdown("""
        <div style='background-color:#f23628;color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        ≤20%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("""
        <div style='background-color:#f2cbdc;color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        20-35%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("""
        <div style='background-color:rgba(255, 215, 0, 0.8);color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        35-65%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown("""
        <div style='background-color:rgba(144, 238, 144, 0.8);color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        65-80%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[4]:
        st.markdown("""
        <div style='background-color:rgba(0, 128, 0, 0.8);color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        80-95%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[5]:
        st.markdown("""
        <div style='background-color:#389ae4;color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        >95%
        </div>
        """, unsafe_allow_html=True)
        
    # Add a note about Main Line at the end
        st.markdown("""
        <div style='padding:2px;text-align:center;font-size:0.7em;'>
        </div>
        """, unsafe_allow_html=True)

def display_treemap_instructions():
    """Display common instructions for the treemaps"""
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: -20px;">
        <small><i>Click on an opening to zoom in and see variations. Double-click to zoom out.</i></small>
    </div>
    """, unsafe_allow_html=True)
    
    # Display color legend in 6 columns
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown("""
        <div style='background-color:#f23628;color:white;padding:5px;border-radius:3px;text-align:center;'>
        ≤20%<br>Deep Red
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background-color:#f2cbdc;color:black;padding:5px;border-radius:3px;text-align:center;'>
        20-35%<br>Pink
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background-color:rgba(255, 215, 0, 0.8);color:black;padding:5px;border-radius:3px;text-align:center;'>
        35-65%<br>Yellow
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style='background-color:rgba(144, 238, 144, 0.8);color:black;padding:5px;border-radius:3px;text-align:center;'>
        65-80%<br>Light Green
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
        <div style='background-color:rgba(0, 128, 0, 0.8);color:white;padding:5px;border-radius:3px;text-align:center;'>
        80-95%<br>Dark Green
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown("""
        <div style='background-color:#389ae4;color:white;padding:5px;border-radius:3px;text-align:center;'>
        >95%<br>Blue
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<p style='text-align:center;font-size:0.8em;'><i>Color represents win percentage</i></p>", unsafe_allow_html=True)

def create_single_treemap(opening_df, side_filter):
    """Create a simple treemap visualization for the given data and side filter"""
    st.subheader(f"Opening Treemap ({side_filter})")
    
    # We'll display the legend at the bottom, after the visualization
    
    # Check if we have data
    if len(opening_df) == 0:
        st.warning("No data available for this filter")
        return
    
    # Make a copy of the dataframe
    opening_df = opening_df.copy()
    
    # Ensure we have OpeningMain values
    opening_df['OpeningMain'] = opening_df['OpeningMain'].fillna("Unknown")
    
    # Calculate stats for main openings
    main_stats = opening_df.groupby('OpeningMain').agg(
        count=('OpeningMain', 'count'),
        wins=('Result', lambda x: (x == 'win').sum()),
        losses=('Result', lambda x: (x == 'loss').sum()),
        draws=('Result', lambda x: (x == 'draw').sum())
    ).reset_index()
    
    # Calculate win rates
    main_stats['win_pct'] = main_stats.apply(
        lambda row: (row['wins'] / row['count'] * 100) if row['count'] > 0 else 0, 
        axis=1
    )
    
    # Basic treemap data structure
    labels = ["All Openings"]
    parents = [""]
    values = [len(opening_df)]
    
    # Color for the root node based on side
    if side_filter == "White Pieces":
        root_color = "rgba(255, 255, 255, 0.9)"  # White
    elif side_filter == "Black Pieces":
        root_color = "rgba(128, 128, 128, 0.9)"  # Gray
    else:
        root_color = "rgba(180, 180, 220, 0.9)"  # Purple
        
    colors = [root_color]
    hover_texts = [f"Total Games: {len(opening_df)}"]
    
    # Add main openings as first level
    for _, row in main_stats.iterrows():
        if row['OpeningMain'] == "Unknown":
            continue
            
        # Calculate win percentage for display
        win_pct = row['win_pct']
        win_pct_display = int(round(win_pct, 0))
        
        # Add to treemap
        label = f"{row['OpeningMain']} ({win_pct_display}%)"
        labels.append(label)
        parents.append("All Openings")
        values.append(row['count'])
        
        # Determine color based on win percentage
        if win_pct <= 20:
            color = "#f23628"  # Deep red
        elif win_pct <= 35:
            color = "#f2cbdc"  # Pink
        elif win_pct <= 65:
            color = "rgba(255, 215, 0, 0.8)"  # Yellow
        elif win_pct <= 80:
            color = "rgba(144, 238, 144, 0.8)"  # Light green
        elif win_pct <= 95:
            color = "rgba(0, 128, 0, 0.8)"  # Dark green
        else:
            color = "#389ae4"  # Blue
            
        colors.append(color)
        hover_texts.append(f"Games: {row['count']}<br>Wins: {row['wins']}<br>Draws: {row['draws']}<br>Losses: {row['losses']}")
    
    # Add variations for each main opening
    # Get unique full openings that aren't the same as main openings
    variations = opening_df[opening_df['OpeningFull'] != opening_df['OpeningMain']]
    
    # Group variations by both main and full opening
    var_stats = variations.groupby(['OpeningMain', 'OpeningFull']).agg(
        count=('OpeningFull', 'count'),
        wins=('Result', lambda x: (x == 'win').sum()),
        losses=('Result', lambda x: (x == 'loss').sum()),
        draws=('Result', lambda x: (x == 'draw').sum())
    ).reset_index()
    
    # Add each variation
    for _, row in var_stats.iterrows():
        main_opening = row['OpeningMain']
        full_opening = row['OpeningFull']
        
        if pd.isna(main_opening) or pd.isna(full_opening):
            continue
            
        # Get variation name by removing main opening
        variation = full_opening.replace(f"{main_opening} ", "").strip()
        if not variation:
            variation = "Main Line"
            
        # Find parent in labels list
        parent_idx = -1
        for i, label in enumerate(labels):
            # Check if this is the parent main opening (strip off the win % for comparison)
            if label.startswith(main_opening) and parents[i] == "All Openings":
                parent_idx = i
                break
                
        if parent_idx < 0:
            continue  # Skip if parent not found
            
        # Calculate win percentage
        win_pct = (row['wins'] / row['count'] * 100) if row['count'] > 0 else 0
        win_pct_display = int(round(win_pct, 0))
        
        # Add to treemap
        labels.append(f"{variation} ({win_pct_display}%)")
        parents.append(labels[parent_idx])
        values.append(row['count'])
        
        # Determine color using same scheme
        if win_pct <= 20:
            color = "#f23628"  # Deep red
        elif win_pct <= 35:
            color = "#f2cbdc"  # Pink
        elif win_pct <= 65:
            color = "rgba(255, 215, 0, 0.8)"  # Yellow
        elif win_pct <= 80:
            color = "rgba(144, 238, 144, 0.8)"  # Light green
        elif win_pct <= 95:
            color = "rgba(0, 128, 0, 0.8)"  # Dark green
        else:
            color = "#389ae4"  # Blue
            
        colors.append(color)
        hover_texts.append(f"Games: {row['count']}<br>Wins: {row['wins']}<br>Draws: {row['draws']}<br>Losses: {row['losses']}")
    
    # Create simple treemap visualization
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(color="rgba(150, 150, 150, 0.8)", width=0.5)
        ),
        text=hover_texts,
        hovertemplate='<b>%{label}</b><br>%{text}<extra></extra>',
        branchvalues="total"  # Use total so children add up to parent
    ))
    
    fig.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        height=700
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display a smaller color legend at the bottom
    st.markdown("<p style='text-align:center;font-size:0.7em;'><i>Win Rate Color Legend</i></p>", unsafe_allow_html=True)
    cols = st.columns(12)
    
    with cols[0]:
        st.markdown("""
        <div style='background-color:#f23628;color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        ≤20%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("""
        <div style='background-color:#f2cbdc;color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        20-35%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("""
        <div style='background-color:rgba(255, 215, 0, 0.8);color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        35-65%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown("""
        <div style='background-color:rgba(144, 238, 144, 0.8);color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        65-80%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[4]:
        st.markdown("""
        <div style='background-color:rgba(0, 128, 0, 0.8);color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        80-95%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[5]:
        st.markdown("""
        <div style='background-color:#389ae4;color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        >95%
        </div>
        """, unsafe_allow_html=True)
        
    # Add a note about Main Line at the end
        st.markdown("""
        <div style='padding:2px;text-align:center;font-size:0.7em;'>
        </div>
        """, unsafe_allow_html=True)

def create_treemap_visualization(opening_df, side_filter):
    """Create a treemap visualization of opening performance"""
    # If we're filtering by a single side, show only one treemap
    if side_filter in ["White Pieces", "Black Pieces"]:
        create_single_treemap(opening_df, side_filter)
        return
    
    # Otherwise, split into three tabs - All, White, and Black
    st.subheader("Opening Treemaps (By Color)")
    treemap_tabs = st.tabs(["All Games", "White Pieces", "Black Pieces"])
    
    # Make a copy to avoid SettingWithCopyWarning
    opening_df = opening_df.copy()
    
    with treemap_tabs[0]:
        # All games
        create_single_treemap(opening_df, "All Games")
        
    with treemap_tabs[1]:
        # White pieces
        white_df = opening_df[opening_df['Side'].str.lower().isin(['w', 'white'])]
        
        if len(white_df) > 0:
            create_single_treemap(white_df, "White Pieces")
        else:
            st.info("No games found where you played White.")
            
    with treemap_tabs[2]:
        # Black pieces
        black_df = opening_df[opening_df['Side'].str.lower().isin(['b', 'black'])]
        
        if len(black_df) > 0:
            create_single_treemap(black_df, "Black Pieces")
        else:
            st.info("No games found where you played Black.")

def create_sankey_diagram(opening_df, side_filter):
    """Create Sankey diagrams showing flow from main openings to results"""
    
    # Display title
    st.markdown("<p style='text-align:center;font-size:0.9em;'><b>Opening Flow Diagram</b></p>", unsafe_allow_html=True)
    # We'll display the legend at the bottom, after the visualization
    
    # Ensure we have data
    if len(opening_df) == 0:
        st.warning("No data available for this filter")
        return
        
    # Handle missing values
    opening_df = opening_df.copy()
    opening_df['OpeningMain'] = opening_df['OpeningMain'].fillna("Unknown")
    
    # Group data
    main_openings = opening_df.groupby(['OpeningMain', 'Result']).size().reset_index(name='count')
    
    # Prepare nodes and links
    nodes = []
    node_colors = []
    
    # Starting nodes
    if side_filter == "White Pieces":
        start_node = "White Pieces"
        node_color = "rgba(255, 255, 255, 0.8)"  # White color
    elif side_filter == "Black Pieces":
        start_node = "Black Pieces"
        node_color = "rgba(128, 128, 128, 0.8)"  # Gray color
    else:
        start_node = "All Games"
        node_color = "rgba(180, 180, 220, 0.8)"  # Purple-ish for all games
    
    nodes.append(start_node)
    node_colors.append(node_color)
    
    # Add opening nodes
    unique_openings = opening_df['OpeningMain'].unique()
    for opening in unique_openings:
        if pd.isna(opening) or opening == "Unknown":
            continue
            
        # Get win rate for this opening
        opening_games = opening_df[opening_df['OpeningMain'] == opening]
        win_count = len(opening_games[opening_games['Result'].str.lower() == 'win'])
        draw_count = len(opening_games[opening_games['Result'].str.lower() == 'draw'])
        total_count = len(opening_games)
        # Calculate win percentage, counting draws as 0.5 wins
        win_pct = ((win_count + 0.5 * draw_count) / total_count * 100) if total_count > 0 else 0
        
        # Determine color based on win rate
        if win_pct <= 20:
            color = "#f23628"  # Deep red
        elif win_pct <= 35:
            color = "#f2cbdc"  # Pink
        elif win_pct <= 65:
            color = "rgba(255, 215, 0, 0.8)"  # Yellow
        elif win_pct <= 80:
            color = "rgba(144, 238, 144, 0.8)"  # Light green
        elif win_pct <= 95:
            color = "rgba(0, 128, 0, 0.8)"  # Dark green
        else:
            color = "#389ae4"  # Blue
            
        nodes.append(opening)
        node_colors.append(color)
    
    # Add result nodes
    nodes.extend(["Win", "Loss", "Draw"])
    node_colors.extend(["rgba(0, 180, 0, 0.8)", "rgba(220, 20, 20, 0.8)", "rgba(120, 120, 200, 0.8)"])
    
    # Create node indices
    node_indices = {node: i for i, node in enumerate(nodes)}
    
    # Prepare links from start to openings
    opening_counts = opening_df.groupby('OpeningMain').size().reset_index(name='count')
    
    sources = []
    targets = []
    values = []
    link_colors = []
    
    for _, row in opening_counts.iterrows():
        opening = row['OpeningMain']
        count = row['count']
        
        if opening in node_indices:
            sources.append(node_indices[start_node])
            targets.append(node_indices[opening])
            values.append(count)
            
            # Get color from the node colors
            opening_idx = nodes.index(opening)
            link_colors.append(node_colors[opening_idx])
    
    # Prepare links from openings to results
    for _, row in main_openings.iterrows():
        opening = row['OpeningMain']
        result = row['Result'].capitalize()
        count = row['count']
        
        if opening in node_indices and result in node_indices:
            sources.append(node_indices[opening])
            targets.append(node_indices[result])
            values.append(count)
            
            # Use result colors for these links
            if result == "Win":
                link_colors.append("rgba(0, 180, 0, 0.6)")
            elif result == "Loss":
                link_colors.append("rgba(220, 20, 20, 0.6)")
            else:
                link_colors.append("rgba(120, 120, 200, 0.6)")
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = nodes,
            color = node_colors
        ),
        link = dict(
            source = sources,
            target = targets,
            value = values,
            color = link_colors
        )
    )])
    
    fig.update_layout(
        title_text=f"Opening Flow ({side_filter})",
        font_size=12,
        height=700
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display a smaller color legend at the bottom
    st.markdown("<p style='text-align:center;font-size:0.7em;'><i>Win Rate Color Legend</i></p>", unsafe_allow_html=True)
    cols = st.columns(12)
    
    with cols[0]:
        st.markdown("""
        <div style='background-color:#f23628;color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        ≤20%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown("""
        <div style='background-color:#f2cbdc;color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        20-35%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("""
        <div style='background-color:rgba(255, 215, 0, 0.8);color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        35-65%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown("""
        <div style='background-color:rgba(144, 238, 144, 0.8);color:black;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        65-80%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[4]:
        st.markdown("""
        <div style='background-color:rgba(0, 128, 0, 0.8);color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        80-95%
        </div>
        """, unsafe_allow_html=True)
    
    with cols[5]:
        st.markdown("""
        <div style='background-color:#389ae4;color:white;padding:2px;border-radius:3px;text-align:center;font-size:0.6em;'>
        >95%
        </div>
        """, unsafe_allow_html=True)
        
    # Add a note about Main Line at the end
        st.markdown("""
        <div style='padding:2px;text-align:center;font-size:0.7em;'>
        </div>
        """, unsafe_allow_html=True)

def create_opening_stats_table(main_stats, full_stats):
    """Create a detailed table with opening statistics"""
    # Handle empty data
    if main_stats is None or full_stats is None or len(main_stats) == 0:
        st.warning("No opening statistics available")
        return
    
    # Create two tabs for main openings and variations
    stats_tabs = st.tabs(["Main Openings", "Opening Variations"])
    
    with stats_tabs[0]:
        # Process main opening stats
        main_df = pd.DataFrame(main_stats)
        
        # Format columns - use win_pct instead of win_rate
        main_df['Win %'] = main_df['win_pct'].apply(lambda x: f"{x:.1f}%")
        main_df['White Games'] = main_df['white']
        main_df['Black Games'] = main_df['black']
        
        # Select columns to display
        display_main = main_df[['OpeningMain', 'total', 'wins', 'losses', 'draws', 'Win %', 'White Games', 'Black Games']]
        display_main.columns = ['Opening', 'Games', 'Wins', 'Losses', 'Draws', 'Win %', 'White', 'Black']
        
        # Apply color styling based on win rate
        def style_win_rate(val):
            """Style the win percentage column"""
            # Parse percentage value
            try:
                pct = float(val.replace("%", ""))
                
                # Apply color scheme consistent with charts
                if pct <= 20:
                    return f'background-color: {rgb_to_rgba("#f23628", 0.3)}; color: black'
                elif pct <= 35:
                    return f'background-color: {rgb_to_rgba("#f2cbdc", 0.6)}; color: black'
                elif pct <= 65:
                    return f'background-color: rgba(255, 215, 0, 0.3); color: black'
                elif pct <= 80:
                    return f'background-color: rgba(144, 238, 144, 0.4); color: black'
                elif pct <= 95:
                    return f'background-color: rgba(0, 128, 0, 0.3); color: black'
                else:
                    return f'background-color: #389ae4; color: black'
            except:
                return ''
        
        # Sort by total games descending
        display_main = display_main.sort_values('Games', ascending=False)
        
        # Style the dataframe
        styled_main = display_main.style.applymap(
            style_win_rate, 
            subset=['Win %']
        )
        
        # Show table
        st.write("### Main Opening Statistics")
        st.dataframe(styled_main, use_container_width=True)
    
    with stats_tabs[1]:
        # Process variation stats
        full_df = pd.DataFrame(full_stats)
        
        # Format columns - use win_pct instead of win_rate
        full_df['Win %'] = full_df['win_pct'].apply(lambda x: f"{x:.1f}%")
        full_df['White Games'] = full_df['white']
        full_df['Black Games'] = full_df['black']
        
        # Select columns to display
        display_full = full_df[['OpeningFull', 'total', 'wins', 'losses', 'draws', 'Win %', 'White Games', 'Black Games']]
        display_full.columns = ['Opening', 'Games', 'Wins', 'Losses', 'Draws', 'Win %', 'White', 'Black']
        
        # Sort by total games descending
        display_full = display_full.sort_values('Games', ascending=False)
        
        # Style the dataframe
        styled_full = display_full.style.applymap(
            style_win_rate, 
            subset=['Win %']
        )
        
        # Show table
        st.write("### Opening Variations Statistics")
        st.dataframe(styled_full, use_container_width=True)

def rgb_to_rgba(rgb_color, alpha=1.0):
    """Convert RGB hex to rgba string for styling"""
    # Handle different input formats
    if rgb_color.startswith("#"):
        # Hex color
        r = int(rgb_color[1:3], 16)
        g = int(rgb_color[3:5], 16)
        b = int(rgb_color[5:7], 16)
    else:
        # Already rgba, just return it
        return rgb_color
    
    return f"rgba({r}, {g}, {b}, {alpha})"