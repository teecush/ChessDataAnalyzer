import io
import chess
import chess.pgn
import pandas as pd
import re

def parse_pgn(pgn_text):
    """Parse PGN text and return a chess.pgn.Game object"""
    if not pgn_text or pd.isna(pgn_text):
        return None
    
    try:
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        return game
    except Exception as e:
        print(f"Error parsing PGN: {e}")
        return None

def extract_player_side(pgn_text, player_names=["Tony", "Tony Cushman"]):
    """Determine which side the player is on based on PGN headers"""
    if not pgn_text or pd.isna(pgn_text):
        return None
    
    # Try to extract player information from PGN headers
    white_pattern = r'\[White\s+"([^"]+)"\]'
    black_pattern = r'\[Black\s+"([^"]+)"\]'
    
    white_match = re.search(white_pattern, pgn_text)
    black_match = re.search(black_pattern, pgn_text)
    
    white_player = white_match.group(1) if white_match else None
    black_player = black_match.group(1) if black_match else None
    
    # Check if player name is in the white or black player fields
    if white_player and any(name in white_player for name in player_names):
        return "White"
    elif black_player and any(name in black_player for name in player_names):
        return "Black"
    
    # If not found in headers, use the Side column data
    return None

def extract_opening_info(pgn_text):
    """Extract opening and variation information from PGN text"""
    if not pgn_text or pd.isna(pgn_text):
        return {"opening": "Unknown", "variation": None}
    
    opening_pattern = r'\[Opening\s+"([^"]+)"\]'
    variation_pattern = r'\[Variation\s+"([^"]+)"\]'
    eco_pattern = r'\[ECO\s+"([^"]+)"\]'
    
    opening_match = re.search(opening_pattern, pgn_text)
    variation_match = re.search(variation_pattern, pgn_text)
    eco_match = re.search(eco_pattern, pgn_text)
    
    opening = opening_match.group(1) if opening_match else "Unknown"
    variation = variation_match.group(1) if variation_match else None
    eco = eco_match.group(1) if eco_match else None
    
    return {
        "opening": opening,
        "variation": variation,
        "eco": eco
    }

def analyze_game(pgn_text, player_side=None):
    """Analyze a chess game from PGN text and return insights"""
    game = parse_pgn(pgn_text)
    if not game:
        return {"error": "Unable to parse PGN"}
    
    # Get basic game information
    headers = dict(game.headers)
    result = headers.get("Result", "*")
    white = headers.get("White", "Unknown")
    black = headers.get("Black", "Unknown")
    
    # Determine player side if not provided
    if not player_side:
        player_side = extract_player_side(pgn_text)
    
    # Get opening information
    opening_info = extract_opening_info(pgn_text)
    
    # Analyze the moves
    board = game.board()
    moves = []
    mistakes = []
    move_count = 0
    
    for node in game.mainline():
        move = node.move
        san = board.san(move)
        
        # Check if there are comments that might indicate mistakes
        comment = node.comment.strip() if hasattr(node, 'comment') else ""
        is_mistake = bool(re.search(r'[?!]{1,2}|mistake|blunder|inaccuracy', comment, re.IGNORECASE))
        
        if is_mistake:
            mistakes.append({
                "move_number": move_count // 2 + 1,
                "side": "White" if board.turn == chess.BLACK else "Black",  # Side that just moved
                "move": san,
                "comment": comment
            })
        
        # Add move to the list
        moves.append({
            "move_number": move_count // 2 + 1,
            "side": "White" if board.turn == chess.BLACK else "Black",  # Side that just moved
            "move": san,
            "comment": comment
        })
        
        board.push(move)
        move_count += 1
    
    # Generate insights based on the game
    insights = []
    
    # Insight based on the number of mistakes
    player_mistakes = [m for m in mistakes if m["side"] == player_side]
    if len(player_mistakes) == 0:
        insights.append("You played a clean game with no obvious mistakes.")
    elif len(player_mistakes) <= 2:
        insights.append(f"You made {len(player_mistakes)} mistake(s), overall a good game.")
    else:
        insights.append(f"You made {len(player_mistakes)} mistakes that affected your position.")
    
    # Insight based on opening
    insights.append(f"Opening played: {opening_info['opening']}")
    if opening_info['variation']:
        insights.append(f"Variation: {opening_info['variation']}")
    
    # Return the analysis results
    return {
        "basic_info": {
            "white": white,
            "black": black,
            "result": result,
            "player_side": player_side,
            "total_moves": move_count
        },
        "opening_info": opening_info,
        "moves": moves,
        "mistakes": mistakes,
        "insights": insights
    }

def get_opening_performance(df):
    """Calculate performance statistics by opening"""
    if df is None or 'PGN' not in df.columns:
        return pd.DataFrame()
    
    # Extract opening information for each game
    openings = []
    variations = []
    results = []
    sides = []
    
    for i, row in df.iterrows():
        pgn = row['PGN']
        result = row['RESULT'].lower() if not pd.isna(row['RESULT']) else 'unknown'
        side = row['Side'] if not pd.isna(row['Side']) else 'unknown'
        
        opening_info = extract_opening_info(pgn)
        openings.append(opening_info['opening'])
        variations.append(opening_info['variation'])
        results.append(result)
        sides.append(side)
    
    # Create a dataframe with all the information
    opening_df = pd.DataFrame({
        'Opening': openings,
        'Variation': variations,
        'Result': results,
        'Side': sides
    })
    
    # Calculate statistics by opening
    opening_stats = opening_df.groupby('Opening').agg(
        total=('Opening', 'count'),
        wins=('Result', lambda x: (x == 'win').sum()),
        losses=('Result', lambda x: (x == 'loss').sum()),
        draws=('Result', lambda x: (x == 'draw').sum()),
        white=('Side', lambda x: (x == 'White').sum()),
        black=('Side', lambda x: (x == 'Black').sum())
    ).reset_index()
    
    # Calculate win percentage
    opening_stats['win_pct'] = round(opening_stats['wins'] / opening_stats['total'] * 100, 1)
    
    # Sort by most played
    opening_stats = opening_stats.sort_values('total', ascending=False)
    
    return opening_stats

def get_common_mistakes(df):
    """Identify common mistake patterns across games"""
    if df is None or 'PGN' not in df.columns:
        return []
    
    all_mistakes = []
    
    for i, row in df.iterrows():
        pgn = row['PGN']
        if pd.isna(pgn) or not pgn:
            continue
            
        side = row['Side'] if not pd.isna(row['Side']) else None
        
        # Analyze the game
        analysis = analyze_game(pgn, side)
        if 'error' in analysis:
            continue
        
        # Extract mistakes made by the player
        player_side = analysis['basic_info']['player_side']
        if player_side:
            player_mistakes = [m for m in analysis['mistakes'] if m['side'] == player_side]
            all_mistakes.extend(player_mistakes)
    
    # Analyze patterns if we have enough mistakes
    if len(all_mistakes) < 3:
        return ["Not enough game data to identify mistake patterns."]
    
    # Count early game (moves 1-10), middle game (11-25), and endgame (26+) mistakes
    early_mistakes = sum(1 for m in all_mistakes if m['move_number'] <= 10)
    middle_mistakes = sum(1 for m in all_mistakes if 10 < m['move_number'] <= 25)
    endgame_mistakes = sum(1 for m in all_mistakes if m['move_number'] > 25)
    
    patterns = []
    
    # Identify where most mistakes happen
    most_mistakes = max(early_mistakes, middle_mistakes, endgame_mistakes)
    if most_mistakes == early_mistakes and early_mistakes > 0:
        patterns.append("You tend to make more mistakes in the opening phase (moves 1-10).")
    elif most_mistakes == middle_mistakes and middle_mistakes > 0:
        patterns.append("Your middle game (moves 11-25) shows the most room for improvement.")
    elif most_mistakes == endgame_mistakes and endgame_mistakes > 0:
        patterns.append("Your endgame play (moves 26+) contains the most mistakes.")
    
    return patterns