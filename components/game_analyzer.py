import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import chess
import chess.svg
from utils.pgn_analyzer import analyze_game, parse_pgn
import streamlit.components.v1 as components

def create_game_analyzer(df):
    """Create a game analyzer section for the dashboard"""
    if df is None or 'PGN' not in df.columns:
        st.warning("PGN data not available. Cannot display game analyzer.")
        return
    
    st.subheader("Game Analysis")
    
    # Create game selector - show games with date, opponent, and result
    games_with_pgn = df[df['PGN'].notna() & (df['PGN'] != '')].copy()
    
    if len(games_with_pgn) == 0:
        st.info("No games with PGN data found.")
        return
    
    # Format the date and create a readable option for the selectbox
    games_with_pgn['Date_Formatted'] = games_with_pgn['Date'].dt.strftime('%Y-%m-%d')
    games_with_pgn['Game_Label'] = games_with_pgn.apply(
        lambda row: f"{row['Date_Formatted']} - {row['Side']} vs {row['Opponent Name']} ({row['Result']})",
        axis=1
    )
    
    # Sort by date in descending order (most recent first)
    games_with_pgn = games_with_pgn.sort_values('Date', ascending=False)
    
    selected_game_label = st.selectbox(
        "Select a game to analyze:",
        options=games_with_pgn['Game_Label'].tolist(),
        index=0,
        key="game_analyzer_select"
    )
    
    # Get the selected game
    selected_game = games_with_pgn[games_with_pgn['Game_Label'] == selected_game_label].iloc[0]
    pgn_text = selected_game['PGN']
    
    # Analyze the game
    analysis = analyze_game(pgn_text)
    
    if 'error' in analysis:
        st.error(f"Error analyzing game: {analysis['error']}")
        return
    
    # Display game information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("White", analysis['basic_info']['white'])
    with col2:
        st.metric("Black", analysis['basic_info']['black'])
    with col3:
        result_map = {"1-0": "White wins", "0-1": "Black wins", "1/2-1/2": "Draw", "*": "Unknown"}
        result_text = result_map.get(analysis['basic_info']['result'], analysis['basic_info']['result'])
        st.metric("Result", result_text)
    
    # Display opening information
    st.write(f"**Opening:** {analysis['opening_info']['opening_full']}")
    if 'opening_variation' in analysis['opening_info'] and analysis['opening_info']['opening_variation']:
        st.write(f"**Variation:** {analysis['opening_info']['opening_variation']}")
    if 'eco' in analysis['opening_info'] and analysis['opening_info']['eco']:
        st.write(f"**ECO Code:** {analysis['opening_info']['eco']}")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs(["Game Insights", "Move List", "Game Visualization"])
    
    with tab1:
        # AI Insights about the game
        st.subheader("Game Insights")
        
        for insight in analysis['insights']:
            st.info(insight)
        
        # Show mistake analysis
        if analysis['mistakes']:
            st.subheader("Potential Mistakes")
            
            for mistake in analysis['mistakes']:
                move_text = f"Move {mistake['move_number']}: {mistake['move']} ({'White' if mistake['side'] == 'White' else 'Black'})"
                st.warning(f"{move_text}\n\n{mistake['comment']}")
        else:
            st.success("No significant mistakes detected in this game.")
    
    with tab2:
        # Move list with comments
        st.subheader("Move List")
        
        # Create a more readable move list
        moves_df = pd.DataFrame(analysis['moves'])
        
        # Group by move number to show white and black moves together
        move_dict = {}
        for _, move in moves_df.iterrows():
            move_num = move['move_number']
            side = move['side']
            san = move['move']
            comment = move['comment']
            
            if move_num not in move_dict:
                move_dict[move_num] = {'move_number': move_num, 'white_move': '', 'white_comment': '', 'black_move': '', 'black_comment': ''}
            
            if side == 'White':
                move_dict[move_num]['white_move'] = san
                move_dict[move_num]['white_comment'] = comment
            else:
                move_dict[move_num]['black_move'] = san
                move_dict[move_num]['black_comment'] = comment
        
        # Convert to dataframe
        moves_display = pd.DataFrame(list(move_dict.values()))
        moves_display = moves_display.sort_values('move_number')
        
        # Display move list
        st.dataframe(
            moves_display[['move_number', 'white_move', 'white_comment', 'black_move', 'black_comment']],
            use_container_width=True,
            column_config={
                "move_number": st.column_config.NumberColumn(
                    "Move #",
                    width="small",
                ),
                "white_move": st.column_config.TextColumn(
                    "White",
                    width="small",
                ),
                "white_comment": "White Comment",
                "black_move": st.column_config.TextColumn(
                    "Black",
                    width="small",
                ),
                "black_comment": "Black Comment",
            },
            hide_index=True
        )
    
    with tab3:
        # Game visualization (starting position)
        st.subheader("Game Visualization")
        
        # Parse the PGN to get the game
        game = parse_pgn(pgn_text)
        
        # Create move slider
        moves = list(game.mainline_moves())
        move_count = len(moves)
        
        selected_move = st.slider(
            "Move", 
            min_value=0, 
            max_value=move_count, 
            value=0,
            help="Slide to see the position after each move.",
            key=f"move_slider_{selected_game_label.replace(' ', '_')}"
        )
        
        # Display current position
        board = game.board()
        
        # Apply moves up to the selected move
        for i in range(selected_move):
            if i < len(moves):
                board.push(moves[i])
        
        # Convert to SVG and display
        svg = chess.svg.board(
            board=board,
            size=400,
            lastmove=moves[selected_move-1] if selected_move > 0 else None,
            check=board.king(board.turn) if board.is_check() else None
        )
        
        # Create navigation buttons (avoid duplicated keys by making them unique with game label)
        prev_col, position_text_col, next_col = st.columns([1, 4, 1])
        
        with prev_col:
            if selected_move > 0:
                st.button("◀ Prev", key=f"prev_move_{selected_game_label.replace(' ', '_')}", on_click=lambda: None)
        
        with position_text_col:
            move_number = selected_move//2 + (1 if selected_move % 2 else 0)
            side = 'Black' if selected_move % 2 else 'White'
            st.write(f"Position after move {move_number}: {side}")
            
        with next_col:
            if selected_move < move_count:
                st.button("Next ▶", key=f"next_move_{selected_game_label.replace(' ', '_')}", on_click=lambda: None)
        
        # Display SVG
        st.image(svg, use_container_width=False)
        
        # Add JavaScript for keyboard navigation with better selectors
        js_code = """
        <script>
        // Function to wait for an element to exist
        function waitForElement(selector, callback) {
            if (document.querySelector(selector)) {
                callback();
            } else {
                setTimeout(function() {
                    waitForElement(selector, callback);
                }, 100);
            }
        }

        // Handle keyboard navigation
        document.addEventListener('keydown', function(event) {
            // Get the current slider
            const slider = document.querySelector('div[data-testid="stSlider"] input[type="range"]');
            if (!slider) return;
            
            const currentValue = parseInt(slider.value);
            const min = parseInt(slider.min);
            const max = parseInt(slider.max);
            
            // Handle left arrow key - move backward
            if (event.key === 'ArrowLeft' && currentValue > min) {
                // Set slider value directly
                slider.value = currentValue - 1;
                slider.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            // Handle right arrow key - move forward
            if (event.key === 'ArrowRight' && currentValue < max) {
                // Set slider value directly
                slider.value = currentValue + 1;
                slider.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // Add click handlers for the prev/next buttons once they're loaded
        waitForElement('button[data-testid*="prev_move_"]', function() {
            const prevButtons = document.querySelectorAll('button[data-testid*="prev_move_"]');
            prevButtons.forEach(function(button) {
                button.addEventListener('click', function() {
                    const slider = document.querySelector('div[data-testid="stSlider"] input[type="range"]');
                    if (slider) {
                        const currentValue = parseInt(slider.value);
                        if (currentValue > parseInt(slider.min)) {
                            slider.value = currentValue - 1;
                            slider.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                });
            });
        });

        waitForElement('button[data-testid*="next_move_"]', function() {
            const nextButtons = document.querySelectorAll('button[data-testid*="next_move_"]');
            nextButtons.forEach(function(button) {
                button.addEventListener('click', function() {
                    const slider = document.querySelector('div[data-testid="stSlider"] input[type="range"]');
                    if (slider) {
                        const currentValue = parseInt(slider.value);
                        if (currentValue < parseInt(slider.max)) {
                            slider.value = currentValue + 1;
                            slider.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                });
            });
        });
        </script>
        """
        
        st.components.v1.html(js_code, height=0)