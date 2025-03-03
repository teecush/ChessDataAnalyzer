import pandas as pd
import numpy as np

def process_chess_data(df):
    """Process the raw chess data for analysis"""
    if df is None:
        return None

    try:
        # Debug starting point
        print("Starting data processing, initial shape:", df.shape)

        # Clean string data and convert date
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()

        # Convert date with error handling
        try:
            df['Date'] = pd.to_datetime(df['Date'])
            print("Date conversion successful. Sample dates:", df['Date'].head())
        except Exception as e:
            print(f"Error converting dates: {e}")
            print("Sample date values:", df['Date'].head())
            return None

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

        # Keep only the columns we need for visualization
        processed_df = df[['Date', '#', 'Performance Rating', 'New Rating', 
                          'Side', 'Result', 'sparkline data', 'Average Centipawn Loss (ACL)',
                          'Accuracy %', 'Game Rating', 'Opponent Name', 'Opponent ELO']].copy()

        # Debug information
        print("Processed data shape:", processed_df.shape)
        print("Sample of processed data:", processed_df.head())
        print("Column dtypes:", processed_df.dtypes)
        print("Rating range:", processed_df['Performance Rating'].min(), "-", processed_df['Performance Rating'].max())
        print("Total number of games:", len(processed_df))
        print("Game numbers range:", processed_df['#'].min(), "-", processed_df['#'].max())

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
            'tournament_performance': 0
        }

    stats = {
        'total_games': len(df),
        'avg_rating': df['New Rating'].mean() if not df['New Rating'].isna().all() else 0,
        'tournament_performance': df['Performance Rating'].mean() if not df['Performance Rating'].isna().all() else 0
    }

    # Round numeric values
    stats['avg_rating'] = round(stats['avg_rating'], 0)
    stats['tournament_performance'] = round(stats['tournament_performance'], 0)

    return stats

def get_opening_stats(df):
    """No longer used - returning empty series"""
    return pd.Series()