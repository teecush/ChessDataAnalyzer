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
    """Create a single sunburst chart showing opening hierarchy and performance"""
    if show_title:
        st.subheader(f"Opening Results ({side_filter})")
        
    # Color legend for better understanding
    st.markdown("""
    <div style="text-align: center; color: #666; margin-bottom: 10px;">
        <small>Colors indicate win rate: red (poor) → yellow (average) → green (good)</small>
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
        <div style='background-color:rgba(0, 206, 209, 0.8);color:black;padding:5px;border-radius:3px;text-align:center;'>
        >95%<br>Turquoise
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<p style='text-align:center;font-size:0.8em;'><i>Color represents win percentage</i></p>", unsafe_allow_html=True)

def create_single_treemap(opening_df, side_filter):
    """Create a single treemap visualization for the given data and side filter"""
    st.subheader(f"Opening Treemap ({side_filter})")
    
    # Display instructions and color legend
    display_treemap_instructions()
    
    # Ensure DataFrame is a copy to avoid modification warnings
    opening_df = opening_df.copy()
    
    # Debug info kept in comments for future reference
    # Creating treemap with opening_df games
    if len(opening_df) == 0:
        st.warning("No data available for this filter")
        return
        
    # Ensure we have OpeningMain values
    if opening_df['OpeningMain'].isnull().sum() > 0:
        # Fill NaN values with "Unknown"
        opening_df['OpeningMain'] = opening_df['OpeningMain'].fillna("Unknown")
    
    # Group by main openings to get stats
    main_openings = opening_df.groupby(["OpeningMain"]).agg(
        count=("OpeningMain", "count"),
        wins=("Result", lambda x: (x == "win").sum()),
        losses=("Result", lambda x: (x == "loss").sum()),
        draws=("Result", lambda x: (x == "draw").sum())
    ).reset_index()
    
    # Initialize treemap data
    treemap_labels = ["Tony's Openings"]  # Root node
    treemap_parents = [""]
    
    # Set root node color based on side
    if side_filter == "White Pieces":
        root_color = "rgba(255, 255, 255, 0.9)"  # White for white pieces
    elif side_filter == "Black Pieces":
        root_color = "rgba(128, 128, 128, 0.9)"  # Light gray for black pieces
    else:
        root_color = "rgba(180, 180, 220, 0.9)"  # Light purple for all games
        
    treemap_values = [len(opening_df)]
    treemap_colors = [root_color]
    treemap_text = [f"Total Games: {len(opening_df)}"]
    
    # Add main openings
    for _, main in main_openings.iterrows():
        # Skip unknown openings
        if main["OpeningMain"] in ["Unknown", "", None] or pd.isna(main["OpeningMain"]):
            continue
            
        # Get win percentage
        win_pct = round(main["wins"] / main["count"] * 100, 1) if main["count"] > 0 else 0
        
        # Add to treemap with win percentage in brackets
        win_pct_display = int(round(win_pct, 0))
        treemap_labels.append(f"{main['OpeningMain']} ({win_pct_display}%)")
        treemap_parents.append("Tony's Openings")
        treemap_values.append(main["count"])
        
        # Color based on win rate with updated color scheme
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
            color = "rgba(0, 206, 209, 0.8)"  # Turquoise/blue
            
        treemap_colors.append(color)
        treemap_text.append(f"Games: {main['count']}<br>Win: {main['wins']} ({win_pct}%)<br>Loss: {main['losses']}<br>Draw: {main['draws']}")
    
    # Process sub-openings data (variations)
    for _, row in opening_df.iterrows():
        main_opening = row["OpeningMain"]
        full_opening = row["OpeningFull"]
        
        # Skip if equal (no sub-variation) or if missing data
        if pd.isna(main_opening) or pd.isna(full_opening) or main_opening == full_opening:
            continue
        
        # Skip duplicates
        variation_name = full_opening.replace(f"{main_opening} ", "").strip()
        if not variation_name:
            variation_name = "Main Line"
        
        # Skip if we've already processed this variation
        full_label = f"{variation_name} "
        if full_label in treemap_labels:
            continue
            
        # Count games with this variation
        variation_df = opening_df[opening_df["OpeningFull"] == full_opening]
        games_count = len(variation_df)
        
        if games_count > 0:
            # Get win rate
            wins_count = len(variation_df[variation_df["Result"] == "win"])
            win_pct = round(wins_count / games_count * 100, 1) if games_count > 0 else 0
            win_pct_display = int(round(win_pct, 0))
            
            # Find parent main opening in treemap labels
            parent_idx = -1
            for i, label in enumerate(treemap_labels):
                if label.startswith(main_opening) and treemap_parents[i] == "Tony's Openings":
                    parent_idx = i
                    break
                    
            if parent_idx >= 0:
                # Add to treemap
                treemap_labels.append(f"{variation_name} ({win_pct_display}%)")
                treemap_parents.append(treemap_labels[parent_idx])
                treemap_values.append(games_count)
                
                # Set color using the same scheme as main openings
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
                    color = "rgba(0, 206, 209, 0.8)"  # Turquoise/blue
                    
                treemap_colors.append(color)
                treemap_text.append(f"Games: {games_count}<br>Wins: {wins_count} ({win_pct}%)")
    
    # Create the treemap visualization
    fig = go.Figure(go.Treemap(
        labels=treemap_labels,
        parents=treemap_parents,
        values=treemap_values,
        marker=dict(
            colors=treemap_colors,
            # Create custom line widths - thicker for main openings
            line=dict(color="rgba(150, 150, 150, 0.8)"),
            line_width=[2.5 if parent == "Tony's Openings" and label != "Tony's Openings" else 0.8 
                       for label, parent in zip(treemap_labels, treemap_parents)]
        ),
        text=treemap_text,
        hovertemplate='<b>%{label}</b><br>%{text}<extra></extra>',
        maxdepth=3,  # Allow deeper zoom levels
        # Start with just main pieces, reveal segments on first click, zoom on second
        visible=True,
        level=0,  # Only show the root level initially
        tiling=dict(
            packing="squarify",  # Use squarify to fill the entire box
            pad=0  # No padding between tiles
        ),
        branchvalues="total"  # Set to total to make children fill parent area
    ))
    
    fig.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        height=700,
        uniformtext=dict(mode="hide", minsize=10)  # Hide text that doesn't fit
    )
    
    st.plotly_chart(fig, use_container_width=True)

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
    st.warning("This feature is unavailable at the moment")

def create_opening_stats_table(main_stats, full_stats):
    """Create a detailed table with opening statistics"""
    st.warning("This feature is unavailable at the moment")