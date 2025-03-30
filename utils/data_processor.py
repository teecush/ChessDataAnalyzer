import pandas as pd
import numpy as np

def process_chess_data(df):
    """Process the raw chess data for analysis"""
    if df is None:
        return None

    try:
        # Clean string data and convert date
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()

        # Convert date with error handling
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            # Silently log error but don't output debug info
            return None

        # Filter out rows without dates (future/unplayed games)
        df = df[df['Date'].notna()].copy()

        # Convert game number to numeric, ensure it starts from 1
        df['#'] = pd.to_numeric(df['#'], errors='coerce')
        df['#'] = df['#'].fillna(0).astype(int) + 1  # Convert to int and add 1 to start from 1

        # Process numeric columns, keeping NaN values for missing data
        df['Performance Rating'] = pd.to_numeric(df['Performance Rating'], errors='coerce')
        df['New Rating'] = pd.to_numeric(df['New Rating'], errors='coerce')
        df['Game Rating'] = pd.to_numeric(df['Game Rating'], errors='coerce')
        df['Opponent ELO'] = pd.to_numeric(df['Opponent ELO'], errors='coerce')
        df['Accuracy %'] = pd.to_numeric(df['Accuracy %'], errors='coerce')
        df['Average Centipawn Loss (ACL)'] = pd.to_numeric(df['Average Centipawn Loss (ACL)'], errors='coerce')
        
        # Rename columns for better display
        df.rename(columns={
            'Average Centipawn Loss (ACL)': 'ACL',
            'Opponent ELO': 'Opp. ELO'
        }, inplace=True)

        # Keep only the columns we need for visualization
        # Add 'RESULT' column for the win-loss chart
        df['RESULT'] = df['Result']  # Create a copy of Result column as RESULT
        
        # Include PGN column if it exists (it will, we added it in google_sheets.py)
        columns_to_keep = ['Date', '#', 'Performance Rating', 'New Rating', 
                          'Side', 'Result', 'RESULT', 'sparkline data', 'ACL',
                          'Accuracy %', 'Game Rating', 'Opponent Name', 'Opp. ELO']
        
        # Add PGN column if it exists
        if 'PGN' in df.columns:
            columns_to_keep.append('PGN')
            
        processed_df = df[columns_to_keep].copy()

        return processed_df

    except Exception as e:
        print(f"Error in process_chess_data: {str(e)}")
        return None

def calculate_statistics(df):
    """Calculate various chess statistics"""
    if df is None:
        return {
            'total_games': 0,
            'current_rating': 0,
            'win_percentage': 0
        }

    total_games = len(df)

    # Calculate current rating (most recent non-null rating)
    current_rating = df.loc[df['New Rating'].notna(), 'New Rating'].iloc[-1] if not df['New Rating'].isna().all() else 0

    # Calculate win percentage
    if total_games > 0:
        wins = len(df[df['RESULT'].str.lower() == 'win'])  # Case-insensitive comparison
        win_percentage = (wins / total_games) * 100
    else:
        win_percentage = 0

    stats = {
        'total_games': total_games,
        'current_rating': round(current_rating, 0),
        'win_percentage': round(win_percentage, 1)
    }

    return stats

def get_opening_stats(df):
    """Extract opening statistics from PGN data"""
    if df is None or 'PGN' not in df.columns:
        return pd.Series()
    
    openings = []
    variations = []
    
    # Regular expressions to extract opening and variation info from PGN
    import re
    opening_pattern = r'\[Opening\s+"([^"]+)"\]'
    variation_pattern = r'\[Variation\s+"([^"]+)"\]'
    
    for pgn in df['PGN']:
        if pd.isna(pgn) or not pgn:
            openings.append(None)
            variations.append(None)
            continue
            
        # Extract opening
        opening_match = re.search(opening_pattern, pgn)
        opening = opening_match.group(1) if opening_match else "Unknown Opening"
        openings.append(opening)
        
        # Extract variation if present
        variation_match = re.search(variation_pattern, pgn)
        variation = variation_match.group(1) if variation_match else None
        variations.append(variation)
    
    # Create a new dataframe with the extracted data
    opening_df = pd.DataFrame({
        'Opening': openings,
        'Variation': variations
    })
    
    # Join with original dataframe to include results
    df_with_openings = pd.concat([df.reset_index(drop=True), opening_df.reset_index(drop=True)], axis=1)
    
    # Create opening statistics
    opening_stats = df_with_openings.groupby('Opening').size()
    opening_stats = opening_stats.sort_values(ascending=False)
    
    # Filter out None or empty values
    opening_stats = opening_stats[opening_stats.index.notnull() & (opening_stats.index != 'Unknown Opening')]
    
    return opening_stats