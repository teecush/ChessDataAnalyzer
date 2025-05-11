import io
import chess
import chess.pgn
import pandas as pd
import re

# Define the player names globally for consistency
PLAYER_NAMES = ["Tony", "Tony Cushman"]

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
    """Extract opening and variation information from PGN text
    Also organizes the opening structure into a more sensible hierarchy"""
    if not pgn_text or pd.isna(pgn_text):
        return {
            "opening_full": "Unknown",
            "opening_main": "Unknown",
            "opening_sub": None,
            "opening_variation": None,
            "eco": None
        }
    
    # Extract raw opening info from PGN
    opening_pattern = r'\[Opening\s+"([^"]+)"\]'
    variation_pattern = r'\[Variation\s+"([^"]+)"\]'
    eco_pattern = r'\[ECO\s+"([^"]+)"\]'
    
    opening_match = re.search(opening_pattern, pgn_text)
    variation_match = re.search(variation_pattern, pgn_text)
    eco_match = re.search(eco_pattern, pgn_text)
    
    opening_full = opening_match.group(1) if opening_match else "Unknown"
    variation_raw = variation_match.group(1) if variation_match else None
    eco = eco_match.group(1) if eco_match else None
    
    # Process the opening string into a structured format using ML-based pattern detection
    # Here we'll use a rule-based approach to split the opening into logical parts
    
    # First check if ":" exists - this often separates main opening from subtype
    opening_parts = []
    opening_main = opening_full
    opening_sub = None
    opening_variation = None
    
    # Only process if we have a real opening name
    if opening_full != "Unknown":
        # Check for special patterns with colons or commas
        if ":" in opening_full:
            # Format: "Main Opening: Subtype"
            main_part, sub_part = opening_full.split(":", 1)
            opening_main = main_part.strip()
            opening_sub = sub_part.strip()
            
            # Check if subtype has a variation separated by a comma
            if "," in opening_sub:
                sub_components = opening_sub.split(",", 1)
                opening_sub = sub_components[0].strip()
                # Only use the comma part if it's substantial (not just a simple modifier)
                if len(sub_components[1].strip()) > 3:
                    opening_variation = sub_components[1].strip()
        
        # If no colon but has a comma, split on comma
        elif "," in opening_full:
            main_part, sub_part = opening_full.split(",", 1)
            opening_main = main_part.strip()
            opening_sub = sub_part.strip()
        
        # Check for Defense/Attack/Gambit patterns without explicit separators
        elif " Defense" in opening_full or " Defence" in opening_full:
            # Try to identify the defense type and name
            for term in ["Defense", "Defence"]:
                if f" {term}" in opening_full:
                    parts = opening_full.split(f" {term}", 1)
                    if len(parts) > 1:
                        # Check if there's a qualifying word after "Defense"
                        if parts[1].strip():
                            opening_main = f"{parts[0]} {term}"
                            opening_sub = parts[1].strip()
                        else:
                            opening_main = opening_full
        
        # Check for Opening + Variation pattern (e.g., "Sicilian Dragon")
        elif len(opening_full.split()) >= 2 and not any(word in opening_full for word in ["Gambit", "Attack", "System"]):
            parts = opening_full.split()
            if len(parts) >= 3:  # If it has at least 3 words, try to split into main + variation
                opening_main = parts[0]
                opening_sub = " ".join(parts[1:])
    
    # If we have a PGN variation field but didn't extract a variation from the opening,
    # use the PGN variation field
    if not opening_variation and variation_raw:
        opening_variation = variation_raw
    
    # Return the structured opening information
    return {
        "opening_full": opening_full,
        "opening_main": opening_main,
        "opening_sub": opening_sub,
        "opening_variation": opening_variation,
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
        # More comprehensive regex to catch mistakes and blunders
        is_mistake = bool(re.search(r'[?!]{1,2}|mistake|blunder|inaccuracy|error|missed|poor|wrong|bad|weak|dubious', comment, re.IGNORECASE))
        
        # If ACL or similar metrics are in the comment, likely a mistake
        if re.search(r'cent[i]?pawn|c\.?p\.?|acl|loss', comment, re.IGNORECASE):
            is_mistake = True
        
        # Determine which side just moved (White moves on even move counts starting from 0)
        moving_side = "White" if move_count % 2 == 0 else "Black"
        
        if is_mistake:
            mistakes.append({
                "move_number": move_count // 2 + 1,
                "side": moving_side,  # Side that just moved
                "move": san,
                "comment": comment
            })
        
        # Add move to the list
        moves.append({
            "move_number": move_count // 2 + 1,
            "side": moving_side,  # Side that just moved
            "move": san,
            "comment": comment
        })
        
        board.push(move)
        move_count += 1
    
    # Generate insights based on the game
    insights = []
    
    # Insight based on the number of mistakes
    player_mistakes = [m for m in mistakes if m["side"] == player_side]
    opponent_side = "Black" if player_side == "White" else "White"
    opponent_mistakes = [m for m in mistakes if m["side"] == opponent_side]
    
    # Get opponent name
    opponent_name = white if player_side == "Black" else black
    
    # Analyze player's performance with personalized insights for Tony
    if len(player_mistakes) == 0:
        insights.append("Tony, you played a clean game with no obvious mistakes!")
    elif len(player_mistakes) <= 2:
        insights.append(f"Tony, you made {len(player_mistakes)} mistake(s), overall a good game.")
    else:
        insights.append(f"Tony, you made {len(player_mistakes)} mistakes that affected your position.")
    
    # Add comparison with opponent
    if len(opponent_mistakes) > len(player_mistakes):
        insights.append(f"Your opponent made more mistakes ({len(opponent_mistakes)}) than you did ({len(player_mistakes)}), Tony.")
    elif len(opponent_mistakes) < len(player_mistakes):
        insights.append(f"Tony, you made more mistakes ({len(player_mistakes)}) than your opponent ({len(opponent_mistakes)}).")
    
    # Add phase analysis
    early_mistakes = [m for m in player_mistakes if m["move_number"] <= 10]
    middle_mistakes = [m for m in player_mistakes if 10 < m["move_number"] <= 25]
    late_mistakes = [m for m in player_mistakes if m["move_number"] > 25]
    
    if early_mistakes:
        insights.append(f"Tony, your early game had {len(early_mistakes)} mistake(s). Focus on opening preparation.")
    if middle_mistakes:
        insights.append(f"Tony, your middle game had {len(middle_mistakes)} mistake(s). Work on tactical awareness.")
    if late_mistakes:
        insights.append(f"Tony, your endgame had {len(late_mistakes)} mistake(s). Practice endgame techniques.")
    
    # Add game length analysis
    if move_count > 60:
        insights.append(f"This was a long game ({move_count//2} moves), Tony. You showed good defensive skills.")
    elif move_count < 20:
        insights.append(f"This was a short game ({move_count//2} moves), Tony, which may indicate tactical oversights.")
    
    # Insight based on opening
    insights.append(f"Opening played: {opening_info['opening_full']}")
    if opening_info.get('opening_variation'):
        insights.append(f"Variation: {opening_info['opening_variation']}")
    if opening_info.get('eco'):
        insights.append(f"ECO Code: {opening_info['eco']}")
    
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
    opening_full = []
    opening_main = []
    opening_sub = []
    opening_variation = []
    eco_codes = []
    results = []
    sides = []
    
    for i, row in df.iterrows():
        pgn = row['PGN']
        result = row['RESULT'].lower() if not pd.isna(row['RESULT']) else 'unknown'
        
        # Fix side format: Convert 'W' to 'White' and 'B' to 'Black' for consistency
        side = row['Side'] if not pd.isna(row['Side']) else 'unknown'
        if side == 'W':
            side = 'White'
        elif side == 'B':
            side = 'Black'
        
        opening_info = extract_opening_info(pgn)
        
        # If main and full opening are the same, add "Main Line" to the full opening
        if opening_info['opening_main'] == opening_info['opening_full'] and opening_info['opening_main'] != "":
            modified_full = f"{opening_info['opening_main']}: Main Line"
            opening_full.append(modified_full)
        else:
            opening_full.append(opening_info['opening_full'])
            
        opening_main.append(opening_info['opening_main'])
        opening_sub.append(opening_info['opening_sub'])
        
        # If there's no variation, set it to "Main Line"
        if not opening_info['opening_variation'] and opening_info['opening_main'] != "":
            opening_variation.append("Main Line")
        else:
            opening_variation.append(opening_info['opening_variation'])
            
        eco_codes.append(opening_info['eco'])
        results.append(result)
        sides.append(side)
    
    # Create a dataframe with all the information
    opening_df = pd.DataFrame({
        'OpeningFull': opening_full,
        'OpeningMain': opening_main,
        'OpeningSub': opening_sub,
        'OpeningVariation': opening_variation,
        'ECO': eco_codes,
        'Result': results,
        'Side': sides
    })
    
    # Calculate statistics by main opening
    opening_stats_main = opening_df.groupby('OpeningMain').agg(
        total=('OpeningMain', 'count'),
        wins=('Result', lambda x: (x == 'win').sum()),
        losses=('Result', lambda x: (x == 'loss').sum()),
        draws=('Result', lambda x: (x == 'draw').sum()),
        white=('Side', lambda x: (x.str.lower() == 'white').sum()),  # Case-insensitive comparison
        black=('Side', lambda x: (x.str.lower() == 'black').sum())   # Case-insensitive comparison
    ).reset_index()
    
    # Calculate win percentage
    opening_stats_main['win_pct'] = round(opening_stats_main['wins'] / opening_stats_main['total'] * 100, 1)
    
    # Sort by most played
    opening_stats_main = opening_stats_main.sort_values('total', ascending=False)
    
    # Calculate statistics by full opening
    opening_stats_full = opening_df.groupby('OpeningFull').agg(
        total=('OpeningFull', 'count'),
        wins=('Result', lambda x: (x == 'win').sum()),
        losses=('Result', lambda x: (x == 'loss').sum()),
        draws=('Result', lambda x: (x == 'draw').sum()),
        white=('Side', lambda x: (x.str.lower() == 'white').sum()),  # Case-insensitive comparison
        black=('Side', lambda x: (x.str.lower() == 'black').sum())   # Case-insensitive comparison
    ).reset_index()
    
    # Calculate win percentage
    opening_stats_full['win_pct'] = round(opening_stats_full['wins'] / opening_stats_full['total'] * 100, 1)
    
    # Sort by most played
    opening_stats_full = opening_stats_full.sort_values('total', ascending=False)
    
    # Keep the detailed dataframe for drill-down analysis
    return {
        'opening_df': opening_df,
        'opening_stats_main': opening_stats_main,
        'opening_stats_full': opening_stats_full
    }

def is_player_name(name, player_names=None):
    """Check if a name belongs to the player (Tony/Tony Cushman)"""
    if player_names is None:
        player_names = PLAYER_NAMES
        
    if not name or pd.isna(name):
        return False
        
    return any(player.lower() in name.lower() for player in player_names)

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
        return ["Not enough game data to identify mistake patterns for Tony."]
    
    # Count early game (moves 1-10), middle game (11-25), and endgame (26+) mistakes
    early_mistakes = sum(1 for m in all_mistakes if m['move_number'] <= 10)
    middle_mistakes = sum(1 for m in all_mistakes if 10 < m['move_number'] <= 25)
    endgame_mistakes = sum(1 for m in all_mistakes if m['move_number'] > 25)
    
    patterns = []
    
    # Identify where most mistakes happen
    most_mistakes = max(early_mistakes, middle_mistakes, endgame_mistakes)
    if most_mistakes == early_mistakes and early_mistakes > 0:
        patterns.append("Tony, you tend to make more mistakes in the opening phase (moves 1-10).")
    elif most_mistakes == middle_mistakes and middle_mistakes > 0:
        patterns.append("Tony, your middle game (moves 11-25) shows the most room for improvement.")
    elif most_mistakes == endgame_mistakes and endgame_mistakes > 0:
        patterns.append("Tony, your endgame play (moves 26+) contains the most mistakes.")
    
    return patterns