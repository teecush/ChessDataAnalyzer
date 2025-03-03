import pandas as pd
import numpy as np

def process_chess_data(df):
    """Process the raw chess data for analysis"""
    if df is None:
        return None

    try:
        # Convert date column
        df['Date'] = pd.to_datetime(df['Date'])

        # Process tournament ratings (keeping NaN values for between-tournament periods)
        df['Performance Rating'] = pd.to_numeric(df['Performance Rating'], errors='coerce')
        df['New Rating'] = pd.to_numeric(df['New Rating'], errors='coerce')

        # Convert game number to numeric
        df['#'] = pd.to_numeric(df['#'], errors='coerce')

        # Process other numeric columns
        df['Game Rating'] = pd.to_numeric(df['Game Rating'], errors='coerce')
        df['Opponent ELO'] = pd.to_numeric(df['Opponent ELO'], errors='coerce')
        df['Accuracy %'] = pd.to_numeric(df['Accuracy %'], errors='coerce')
        df['Average Centipawn Loss (ACL)'] = pd.to_numeric(df['Average Centipawn Loss (ACL)'], errors='coerce')

        # Keep only the columns we need for visualization
        processed_df = df[['Date', '#', 'Performance Rating', 'New Rating', 
                          'Side', 'Result', 'Game Rating', 'Opponent ELO',
                          'Accuracy %', 'Average Centipawn Loss (ACL)']].copy()

        # Debug information
        print("Processed data shape:", processed_df.shape)
        print("Sample of processed data:", processed_df.head())
        print("Rating range:", processed_df['Performance Rating'].min(), "-", processed_df['Performance Rating'].max())

        return processed_df

    except Exception as e:
        print(f"Error in process_chess_data: {str(e)}")
        return None

def calculate_statistics(df):
    """Calculate various chess statistics"""
    if df is None:
        return {
            'total_games': 0,
            'avg_rating': 0,
            'max_rating': 0,
            'min_rating': 0,
            'tournament_performance': 0
        }

    stats = {
        'total_games': len(df),
        'avg_rating': df['New Rating'].mean(),
        'max_rating': df['New Rating'].max(),
        'min_rating': df['New Rating'].min(),
        'tournament_performance': df['Performance Rating'].mean()  # Average tournament performance
    }

    return stats

def get_opening_stats(df):
    """No longer used - returning empty series"""
    return pd.Series()