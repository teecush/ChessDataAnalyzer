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
    
    # Show opening stats table with win rates directly (not in nested expander)
    st.subheader("Opening Statistics Table")
    # Create a more detailed table with all stats
    create_opening_stats_table(opening_stats_main, opening_stats_full)

def create_sunburst_chart(opening_df, side_filter):
    """Create sunburst charts showing opening hierarchy and performance for both White and Black"""
    
    # If we're filtering by a single side, show only one sunburst
    if side_filter in ["White Pieces", "Black Pieces"]:
        create_single_sunburst(opening_df, side_filter)
        return
    
    # Otherwise, split into two charts - White and Black
    st.subheader("Opening Sunburst Charts (By Color)")
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### White Pieces")
        white_df = opening_df[opening_df['Side'].str.lower().isin(['w', 'white'])]
        if len(white_df) > 0:
            create_single_sunburst(white_df, "White Pieces", show_title=False)
        else:
            st.info("No games found playing White.")
    
    with col2:
        st.write("### Black Pieces")
        black_df = opening_df[opening_df['Side'].str.lower().isin(['b', 'black'])]
        if len(black_df) > 0:
            create_single_sunburst(black_df, "Black Pieces", show_title=False)
        else:
            st.info("No games found playing Black.")
            
def create_single_sunburst(opening_df, side_filter, show_title=True):
    """Create a single sunburst chart showing opening hierarchy and performance"""
    if show_title:
        st.subheader(f"Opening Sunburst Chart ({side_filter})")
    
    # Prepare data for the sunburst chart
    # We need: labels (all hierarchy levels), parents (parent of each node), and values (size)
    
    # Create a list of all labels, parents, and values
    labels = []
    parents = []
    values = []
    colors = []
    
    # Add "All Openings" as the root with color based on side_filter
    labels.append("All Openings")
    parents.append("")  # Root has no parent
    values.append(len(opening_df))
    
    # Choose root color based on side filter
    if side_filter == "White Pieces":
        root_color = "rgba(255, 255, 255, 0.8)"  # White for white pieces
    elif side_filter == "Black Pieces":
        root_color = "rgba(128, 128, 128, 0.8)"  # Light gray for black pieces
    else:
        root_color = "rgba(180, 180, 220, 0.8)"  # Light purple for all games
        
    colors.append(root_color)
    
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
    
    # Prepare custom text labels with win percentages
    custom_text = []
    for i, label in enumerate(labels):
        if i == 0:  # Root node
            custom_text.append("All Openings")
            continue
        
        # Format longer labels to wrap on multiple lines
        formatted_label = label
        if len(label) > 15:
            # Split long names at logical points (spaces, hyphens)
            split_points = [' ', '-', ':']
            for split_char in split_points:
                if split_char in label and len(label) > 15:
                    parts = label.split(split_char, 1)
                    if len(parts[0]) > 5:  # Only split if first part is reasonably long
                        formatted_label = parts[0] + split_char + "<br>" + parts[1]
                        break
            
        # Get win data for this node
        if label in main_openings.index.tolist():
            # This is a main opening
            win_count = main_openings.loc[label, "wins"]
            total_count = main_openings.loc[label, "count"]
            win_pct = round(win_count / total_count * 100) if total_count > 0 else 0
            custom_text.append(f"{formatted_label}<br>{win_pct}% Win")
        else:
            # Check if this is a variation (full opening)
            if label in opening_df["OpeningFull"].values:
                games = opening_df[opening_df["OpeningFull"] == label]
                total_count = len(games)
                win_count = len(games[games["Result"] == "win"])
                win_pct = round(win_count / total_count * 100) if total_count > 0 else 0
                custom_text.append(f"{formatted_label}<br>{win_pct}% Win")
            else:
                # Catch-all for any other nodes
                custom_text.append(f"{formatted_label}")
    
    # Create the sunburst chart
    # Set border color based on side filter
    if side_filter == "White Pieces":
        border_color = "rgba(200, 200, 200, 0.8)"  # Light gray for white pieces
    elif side_filter == "Black Pieces":
        border_color = "rgba(100, 100, 100, 0.8)"  # Dark gray for black pieces
    else:
        border_color = "rgba(150, 150, 200, 0.8)"  # Purple-ish for all games
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(
            colors=colors,
            line=dict(width=0.5, color=border_color)
        ),
        # Hover template shows games played and win percentage
        hovertemplate='<b>%{label}</b><br>Games: %{value}<br>',
        # Ensure we see labels for most segments
        insidetextorientation='radial',
        text=custom_text,
        textinfo="text",
        maxdepth=3,  # Limit depth for better readability
        # Improved text size for better readability
        textfont=dict(
            size=11  # Slightly larger font
        )
    ))
    
    fig.update_layout(
        title="Opening Repertoire Breakdown",
        width=800,
        height=800,
        margin=dict(t=30, l=0, r=0, b=0),
        uniformtext=dict(minsize=10, mode='show')  # Show as many labels as possible with slightly larger font
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: -20px;">
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
        <div style='background-color:rgba(128, 0, 32, 0.8);color:white;padding:5px;border-radius:3px;text-align:center;'>
        ≤20%<br>Deep Red
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background-color:rgba(255, 105, 180, 0.8);color:white;padding:5px;border-radius:3px;text-align:center;'>
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
