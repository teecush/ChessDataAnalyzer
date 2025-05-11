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
        <small>Win rate colors: red (<33%) → yellow (33-67%) → green (>67%) → blue-green (>80%)</small><br>
        <small><i>Click on an opening to zoom in and see variations. Double-click to zoom out.</i></small>
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
    
    # Fix to ensure side filtering works correctly
    # Copy dataframe to avoid mutations
    opening_df = opening_df.copy()
    
    with treemap_tabs[0]:
        # All games
        create_single_treemap(opening_df, "All Games")
        
    with treemap_tabs[1]:
        # White pieces
        white_df = opening_df[opening_df['Side'].str.lower().isin(['w', 'white'])]
        
        if len(white_df) > 0:
            # Direct implementation instead of calling create_single_treemap
            st.subheader("White Pieces Openings")
            
            # Group by hierarchy
            main_openings = white_df.groupby(["OpeningMain"]).agg(
                count=("OpeningMain", "count"),
                wins=("Result", lambda x: (x == "win").sum()),
                losses=("Result", lambda x: (x == "loss").sum()),
                draws=("Result", lambda x: (x == "draw").sum())
            ).reset_index()
            
            # Prepare data
            treemap_labels = ["White Openings"]  # Root node
            treemap_parents = [""]
            treemap_values = [len(white_df)]
            treemap_colors = ["rgba(255, 255, 255, 0.8)"]  # White for root
            treemap_text = [f"Total White Games: {len(white_df)}"]
            
            # Add main openings
            for _, main in main_openings.iterrows():
                if main["OpeningMain"] in ["Unknown", "", None] or pd.isna(main["OpeningMain"]):
                    continue
                
                win_pct = round(main["wins"] / main["count"] * 100, 1) if main["count"] > 0 else 0
                
                treemap_labels.append(main["OpeningMain"])
                treemap_parents.append("White Openings")
                treemap_values.append(main["count"])
                
                # Color based on win rate
                if win_pct < 33:
                    # Red to yellow gradient for poor win rates
                    color = f"rgba(255, {int(255 * win_pct / 33)}, 0, 0.8)"
                elif win_pct < 67:
                    # Yellow to green gradient for average win rates
                    color = f"rgba({int(255 * (2 - win_pct/33))}, 255, 0, 0.8)"
                else:
                    # Green to blue gradient for excellent win rates
                    # When win_pct is 67, it's fully green; when 100, it adds blue
                    green = 255
                    blue = int(255 * (win_pct - 67) / 33)
                    color = f"rgba(0, {green}, {blue}, 0.8)"
                
                treemap_colors.append(color)
                treemap_text.append(f"Games: {main['count']}<br>Win: {main['wins']} ({win_pct}%)<br>Loss: {main['losses']}<br>Draw: {main['draws']}")
            
            # Add variations to the white treemap
            for _, row in white_df.iterrows():
                main_opening = row["OpeningMain"] 
                full_opening = row["OpeningFull"]
                
                # Skip if they are the same or if any is missing
                if (pd.isna(main_opening) or pd.isna(full_opening) or 
                    main_opening == full_opening or 
                    main_opening in ["Unknown", ""] or
                    full_opening in ["Unknown", ""]):
                    continue
                
                # Only add if this full opening isn't already in the treemap
                if full_opening not in treemap_labels:
                    treemap_labels.append(full_opening)
                    treemap_parents.append(main_opening)  # Parent is the main opening
                    
                    # Count games with this full opening
                    full_games = len(white_df[white_df["OpeningFull"] == full_opening])
                    treemap_values.append(full_games)
                    
                    # Calculate win rate
                    full_wins = len(white_df[(white_df["OpeningFull"] == full_opening) & 
                                            (white_df["Result"] == "win")])
                    win_pct = full_wins / full_games * 100 if full_games > 0 else 0
                    
                    # Determine color based on win rate
                    if win_pct < 33:
                        color = f"rgba(255, {int(255 * win_pct / 33)}, 0, 0.8)"
                    elif win_pct < 67:
                        color = f"rgba({int(255 * (2 - win_pct/33))}, 255, 0, 0.8)"
                    else:
                        green = 255
                        blue = int(255 * (win_pct - 67) / 33) if win_pct > 67 else 0
                        color = f"rgba(0, {green}, {blue}, 0.8)"
                    
                    treemap_colors.append(color)
                    treemap_text.append(f"Games: {full_games}<br>Win: {full_wins} ({round(win_pct, 1)}%)")

            # Create and display the white pieces treemap
            fig = go.Figure(go.Treemap(
                labels=treemap_labels,
                parents=treemap_parents,
                values=treemap_values,
                branchvalues="total",
                marker=dict(
                    colors=treemap_colors,
                    line=dict(width=0.5, color="rgba(200, 200, 200, 0.8)")
                ),
                text=treemap_text,
                hovertemplate='<b>%{label}</b><br>%{text}<br>',
                textinfo="label+value",
                maxdepth=3,  # Allow deeper zoom levels
                root_color="rgba(255, 255, 255, 0.9)",  # Consistent root color
                # Start with only one level visible (hide variations until clicked)
                visible=True,
                level=1  # Only show the first level initially
            ))
            
            fig.update_layout(
                title="White Pieces Opening Repertoire",
                width=900,
                height=700,
                margin=dict(t=30, l=0, r=0, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add color legend with clearer explanation
            st.markdown("""
            <div style="text-align: center; color: #666; margin-top: -20px;">
                <small>Win rate colors: red (<33%) → yellow (33-67%) → green (>67%) → blue-green (>80%)</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No games found where you played White.")
    
    with treemap_tabs[2]:
        # Black pieces
        black_df = opening_df[opening_df['Side'].str.lower().isin(['b', 'black'])].copy()
        
        if len(black_df) > 0:
            # Direct implementation instead of calling create_single_treemap
            st.subheader("Black Pieces Openings")
            
            # Group by hierarchy
            main_openings = black_df.groupby(["OpeningMain"]).agg(
                count=("OpeningMain", "count"),
                wins=("Result", lambda x: (x == "win").sum()),
                losses=("Result", lambda x: (x == "loss").sum()),
                draws=("Result", lambda x: (x == "draw").sum())
            ).reset_index()
            
            # Prepare data
            treemap_labels = ["Black Openings"]  # Root node
            treemap_parents = [""]
            treemap_values = [len(black_df)]
            treemap_colors = ["rgba(128, 128, 128, 0.8)"]  # Gray for root
            treemap_text = [f"Total Black Games: {len(black_df)}"]
            
            # Add main openings
            for _, main in main_openings.iterrows():
                if main["OpeningMain"] in ["Unknown", "", None] or pd.isna(main["OpeningMain"]):
                    continue
                
                win_pct = round(main["wins"] / main["count"] * 100, 1) if main["count"] > 0 else 0
                
                treemap_labels.append(main["OpeningMain"])
                treemap_parents.append("Black Openings")
                treemap_values.append(main["count"])
                
                # Color based on win rate - same as white pieces for consistency
                if win_pct < 33:
                    # Red to yellow gradient for poor win rates
                    color = f"rgba(255, {int(255 * win_pct / 33)}, 0, 0.8)"
                elif win_pct < 67:
                    # Yellow to green gradient for average win rates
                    color = f"rgba({int(255 * (2 - win_pct/33))}, 255, 0, 0.8)"
                else:
                    # Green to blue gradient for excellent win rates
                    # When win_pct is 67, it's fully green; when 100, it adds blue
                    green = 255
                    blue = int(255 * (win_pct - 67) / 33)
                    color = f"rgba(0, {green}, {blue}, 0.8)"
                
                treemap_colors.append(color)
                treemap_text.append(f"Games: {main['count']}<br>Win: {main['wins']} ({win_pct}%)<br>Loss: {main['losses']}<br>Draw: {main['draws']}")
            
            # Add variations to the black treemap
            for _, row in black_df.iterrows():
                main_opening = row["OpeningMain"] 
                full_opening = row["OpeningFull"]
                
                # Skip if they are the same or if any is missing
                if (pd.isna(main_opening) or pd.isna(full_opening) or 
                    main_opening == full_opening or 
                    main_opening in ["Unknown", ""] or
                    full_opening in ["Unknown", ""]):
                    continue
                
                # Only add if this full opening isn't already in the treemap
                if full_opening not in treemap_labels:
                    treemap_labels.append(full_opening)
                    treemap_parents.append(main_opening)  # Parent is the main opening
                    
                    # Count games with this full opening
                    full_games = len(black_df[black_df["OpeningFull"] == full_opening])
                    treemap_values.append(full_games)
                    
                    # Calculate win rate
                    full_wins = len(black_df[(black_df["OpeningFull"] == full_opening) & 
                                            (black_df["Result"] == "win")])
                    win_pct = full_wins / full_games * 100 if full_games > 0 else 0
                    
                    # Determine color based on win rate
                    if win_pct < 33:
                        color = f"rgba(255, {int(255 * win_pct / 33)}, 0, 0.8)"
                    elif win_pct < 67:
                        color = f"rgba({int(255 * (2 - win_pct/33))}, 255, 0, 0.8)"
                    else:
                        green = 255
                        blue = int(255 * (win_pct - 67) / 33) if win_pct > 67 else 0
                        color = f"rgba(0, {green}, {blue}, 0.8)"
                    
                    treemap_colors.append(color)
                    treemap_text.append(f"Games: {full_games}<br>Win: {full_wins} ({round(win_pct, 1)}%)")

            # Create and display the black pieces treemap
            fig = go.Figure(go.Treemap(
                labels=treemap_labels,
                parents=treemap_parents,
                values=treemap_values,
                branchvalues="total",
                marker=dict(
                    colors=treemap_colors,
                    line=dict(width=0.5, color="rgba(100, 100, 100, 0.8)")
                ),
                text=treemap_text,
                hovertemplate='<b>%{label}</b><br>%{text}<br>',
                textinfo="label+value",
                maxdepth=3,  # Allow deeper zoom levels
                root_color="rgba(128, 128, 128, 0.9)",  # Consistent root color for Black
                # Start with only one level visible (hide variations until clicked)
                visible=True,
                level=1  # Only show the first level initially
            ))
            
            fig.update_layout(
                title="Black Pieces Opening Repertoire",
                width=900,
                height=700,
                margin=dict(t=30, l=0, r=0, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add color legend with clearer explanation
            st.markdown("""
            <div style="text-align: center; color: #666; margin-top: -20px;">
                <small>Win rate colors: red (<33%) → yellow (33-67%) → green (>67%) → blue-green (>80%)</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No games found where you played Black.")

def create_single_treemap(opening_df, side_filter):
    """Create a single treemap visualization for the given data and side filter"""
    st.subheader(f"Opening Treemap ({side_filter})")
    
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
        st.write(f"Filled {opening_df['OpeningMain'].isnull().sum()} NaN values in OpeningMain")
    
    # Make sure Result column has proper values
    if 'Result' not in opening_df.columns:
        st.error("Result column is missing")
        return
        
    # Ensure Result has proper values
    if opening_df['Result'].isnull().sum() > 0:
        opening_df['Result'] = opening_df['Result'].fillna("unknown")
        
    # Group by hierarchy
    try:
        main_openings = opening_df.groupby(["OpeningMain"]).agg(
            count=("OpeningMain", "count"),
            wins=("Result", lambda x: (x == "win").sum()),
            losses=("Result", lambda x: (x == "loss").sum()),
            draws=("Result", lambda x: (x == "draw").sum())
        ).reset_index()
        
        # Found main_openings.shape[0] main openings
        
    except Exception as e:
        st.error(f"Error during aggregation: {str(e)}")
        return
    
    # Prepare data for treemap
    treemap_labels = []
    treemap_parents = []
    treemap_values = []
    treemap_colors = []
    treemap_text = []
    
    # Add root with color based on side filter
    treemap_labels.append("Tony's Openings")
    treemap_parents.append("")
    treemap_values.append(len(opening_df))
    
    # Choose color based on side filter
    if side_filter == "White Pieces":
        root_color = "rgba(255, 255, 255, 0.9)"  # White for white pieces
    elif side_filter == "Black Pieces":
        root_color = "rgba(128, 128, 128, 0.9)"  # Light gray for black pieces
    else:
        root_color = "rgba(180, 180, 220, 0.9)"  # Light purple for all games
        
    treemap_colors.append(root_color)
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
        
        # Color based on win rate - consistent with other functions
        if win_pct < 33:
            # Red to yellow gradient for poor win rates
            color = f"rgba(255, {int(255 * win_pct / 33)}, 0, 0.8)"
        elif win_pct < 67:
            # Yellow to green gradient for average win rates
            color = f"rgba({int(255 * (2 - win_pct/33))}, 255, 0, 0.8)"
        else:
            # Green to blue gradient for excellent win rates
            green = 255
            blue = int(255 * (win_pct - 67) / 33)
            color = f"rgba(0, {green}, {blue}, 0.8)"
            
        treemap_colors.append(color)
        treemap_text.append(f"Games: {main['count']}<br>Win: {main['wins']} ({win_pct}%)<br>Loss: {main['losses']}<br>Draw: {main['draws']}")
    
    # Process sub-openings data (variations)
    
    # Add full openings under main openings
    for main_opening in main_openings["OpeningMain"]:
        if main_opening in ["Unknown", "", None] or pd.isna(main_opening):
            continue
            
        # Filter for this main opening
        try:
            # Check if OpeningFull column exists in the filtered dataset
            if 'OpeningFull' not in opening_df.columns:
                # OpeningFull column missing, skipping detailed analysis
                continue
                
            # Get the games for this opening
            opening_games = opening_df[opening_df["OpeningMain"] == main_opening]
            
            # Check if there are any games
            if len(opening_games) == 0:
                # No games found for this opening
                continue
                
            # Group by OpeningFull
            full_openings = opening_games.groupby("OpeningFull").agg(
                count=("OpeningFull", "count"),
                wins=("Result", lambda x: (x == "win").sum()),
                losses=("Result", lambda x: (x == "loss").sum()),
                draws=("Result", lambda x: (x == "draw").sum())
            ).reset_index()
        except Exception as e:
            st.error(f"Error processing sub-openings for {main_opening}: {str(e)}")
            continue
        
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
            
            # Color based on win rate - consistent with other functions
            if win_pct < 33:
                # Red to yellow gradient for poor win rates
                color = f"rgba(255, {int(255 * win_pct / 33)}, 0, 0.8)"
            elif win_pct < 67:
                # Yellow to green gradient for average win rates
                color = f"rgba({int(255 * (2 - win_pct/33))}, 255, 0, 0.8)"
            else:
                # Green to blue gradient for excellent win rates
                green = 255
                blue = int(255 * (win_pct - 67) / 33)
                color = f"rgba(0, {green}, {blue}, 0.8)"
                
            treemap_colors.append(color)
            treemap_text.append(f"Games: {full['count']}<br>Win: {full['wins']} ({win_pct}%)<br>Loss: {full['losses']}<br>Draw: {full['draws']}")
    
    # Create the treemap
    # Set border color based on side filter
    if side_filter == "White Pieces":
        border_color = "rgba(200, 200, 200, 0.8)"  # Light gray for white pieces
    elif side_filter == "Black Pieces":
        border_color = "rgba(100, 100, 100, 0.8)"  # Dark gray for black pieces
    else:
        border_color = "rgba(150, 150, 200, 0.8)"  # Purple-ish for all games
        
    # Add debugging for treemap data
    st.write(f"Treemap data prepared: {len(treemap_labels)} nodes")
    
    # Check if we have data to display
    if len(treemap_labels) <= 1:
        st.error("Not enough data to create a treemap visualization")
        return
        
    try:
        fig = go.Figure(go.Treemap(
            labels=treemap_labels,
            parents=treemap_parents,
            values=treemap_values,
            branchvalues="total",
            marker=dict(
                colors=treemap_colors,
                line=dict(width=0.5, color=border_color)
            ),
            text=treemap_text,
            hovertemplate='<b>%{label}</b><br>%{text}<br>',
            textinfo="label+value",
            maxdepth=3,  # Allow deeper zoom levels for better interactivity
            # Start with only one level visible (hide variations until clicked)
            visible=True,
            level=1  # Only show the first level initially
        ))
    except Exception as e:
        st.error(f"Error creating treemap: {str(e)}")
        return
    
    try:
        fig.update_layout(
            title=f"Opening Repertoire by Games Played ({side_filter})",
            width=900,
            height=700,
            margin=dict(t=30, l=0, r=0, b=0)
        )
        
        # Actually display the chart
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("Treemap visualization created successfully")
    except Exception as e:
        st.error(f"Error displaying treemap: {str(e)}")
    
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: -20px;">
        <small>Colors indicate win rate: red (poor) → yellow (average) → green (good)</small>
    </div>
    """, unsafe_allow_html=True)

def create_sankey_diagram(opening_df, side_filter):
    """Create Sankey diagrams showing flow from main openings to results"""
    st.subheader(f"Opening Flow Diagrams ({side_filter})")
    
    # Create tabs for the two different flow diagrams
    basic_tab, detailed_tab = st.tabs(["Basic Flow", "Detailed Flow with Variations"])
    
    with basic_tab:
        st.write("### Basic Side → Opening → Result Flow")
        create_basic_sankey(opening_df, side_filter)
        
    with detailed_tab:
        st.write("### Detailed Flow with Opening Variations")
        create_detailed_sankey(opening_df, side_filter)
        
def create_basic_sankey(opening_df, side_filter):
    """Create a basic Sankey diagram showing flow from side to main openings to results"""
    
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
    
    **Note:** If there's a flow that doesn't show as white or black, it's because the side information
    is missing or in a non-standard format in the original data.
    """)
    
def create_detailed_sankey(opening_df, side_filter):
    """Create a detailed Sankey diagram showing flow through variations and to results"""
    
    # Create a flow: Side → Main Opening → Full Opening → Result
    sides = sorted(opening_df["Side"].unique())
    
    # Filter main openings (exclude unknown/empty)
    main_openings = sorted([m for m in opening_df["OpeningMain"].unique() 
                          if m not in ["Unknown", "", None] and not pd.isna(m)])
    
    # Get full openings that aren't the same as their main opening
    full_openings = []
    for _, row in opening_df.iterrows():
        main = row["OpeningMain"]
        full = row["OpeningFull"]
        if (full != main and 
            full not in ["Unknown", "", None] and not pd.isna(full) and
            full not in full_openings):
            full_openings.append(full)
    full_openings.sort()
    
    # Results
    results = ["win", "loss", "draw"]
    
    # Prepare Sankey data
    # All node labels
    labels = sides + main_openings + full_openings + results
    
    # For tracking nodes and connections
    sources = []
    targets = []
    values = []
    link_colors = []
    
    # 1. Side to Main Opening links
    side_to_main_idx = {}  # Track indices for faster lookup
    for i, side in enumerate(sides):
        for j, main in enumerate(main_openings):
            # Calculate actual index in the diagram
            main_idx = len(sides) + j
            
            # Check if this combination exists
            games = len(opening_df[(opening_df["Side"] == side) & 
                                 (opening_df["OpeningMain"] == main)])
            if games > 0:
                sources.append(i)
                targets.append(main_idx)
                values.append(games)
                
                # Store this connection for lookup
                if side not in side_to_main_idx:
                    side_to_main_idx[side] = {}
                side_to_main_idx[side][main] = len(sources) - 1
                
                # Color based on side
                if side.lower() in ["white", "w"]:
                    link_colors.append("rgba(173, 216, 230, 0.4)")  # Light blue for White
                else:
                    link_colors.append("rgba(128, 128, 128, 0.4)")  # Gray for Black
    
    # 2. Main Opening to Full Opening links
    main_to_full_idx = {}  # Track indices
    for i, main in enumerate(main_openings):
        main_idx = len(sides) + i
        
        for j, full in enumerate(full_openings):
            full_idx = len(sides) + len(main_openings) + j
            
            # Check if this combination exists
            games = len(opening_df[(opening_df["OpeningMain"] == main) & 
                                 (opening_df["OpeningFull"] == full)])
            if games > 0:
                sources.append(main_idx)
                targets.append(full_idx)
                values.append(games)
                
                # Store this connection
                if main not in main_to_full_idx:
                    main_to_full_idx[main] = {}
                main_to_full_idx[main][full] = len(sources) - 1
                
                # Use a neutral color with some transparency
                link_colors.append("rgba(150, 150, 150, 0.3)")
    
    # 3. Main Opening directly to Result links (for openings without variations)
    for i, main in enumerate(main_openings):
        main_idx = len(sides) + i
        
        # Get all games with this main opening
        main_games = opening_df[opening_df["OpeningMain"] == main]
        
        # Count games that go directly to results (not through variations)
        direct_games = main_games[main_games["OpeningMain"] == main_games["OpeningFull"]]
        
        for j, result in enumerate(results):
            result_idx = len(sides) + len(main_openings) + len(full_openings) + j
            
            # Count games with this result
            games = len(direct_games[direct_games["Result"] == result])
            if games > 0:
                sources.append(main_idx)
                targets.append(result_idx)
                values.append(games)
                
                # Color based on result
                if result == "win":
                    link_colors.append("rgba(0, 255, 0, 0.4)")      # Green for wins
                elif result == "loss":
                    link_colors.append("rgba(255, 0, 0, 0.4)")      # Red for losses
                else:
                    link_colors.append("rgba(0, 0, 255, 0.4)")      # Blue for draws
    
    # 4. Full Opening to Result links
    for i, full in enumerate(full_openings):
        full_idx = len(sides) + len(main_openings) + i
        
        for j, result in enumerate(results):
            result_idx = len(sides) + len(main_openings) + len(full_openings) + j
            
            # Count games with this combination
            games = len(opening_df[(opening_df["OpeningFull"] == full) & 
                                 (opening_df["Result"] == result)])
            if games > 0:
                sources.append(full_idx)
                targets.append(result_idx)
                values.append(games)
                
                # Color based on result
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
        elif side.lower() in ["black", "b"]:
            node_colors.append("rgba(128, 128, 128, 1)")  # Gray for Black
        else:
            node_colors.append("rgba(200, 150, 100, 1)")  # Tan for unknown/other
    
    # Colors for main openings (light purple)
    for _ in main_openings:
        node_colors.append("rgba(180, 180, 220, 1)")
    
    # Colors for full openings (light green)
    for _ in full_openings:
        node_colors.append("rgba(180, 220, 180, 1)")
    
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
            source=sources,
            target=targets,
            value=values,
            color=link_colors
        )
    ))
    
    fig.update_layout(
        title="Detailed Opening Flow with Variations",
        font=dict(size=10),  # Smaller font for more detailed diagram
        height=1000,  # Taller for more detailed diagram
        width=1000
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add a detailed description
    st.markdown("""
    This more detailed diagram shows the complete flow of your games:
    
    **Side (White/Black)** → **Main Opening Type** → **Specific Opening Variation** → **Result (Win/Loss/Draw)**
    
    Thicker lines indicate more games played along that path. Some games go directly from main opening to result
    when they don't have specific variations identified.
    
    **Note:** If there's a flow that doesn't show as white or black, it's because the side information
    is missing or in a non-standard format in the original data.
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