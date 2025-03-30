import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def extract_game_features(df):
    """Extract numerical features for ML analysis"""
    features = pd.DataFrame()

    # Extract available numerical features
    features['acl'] = pd.to_numeric(df['ACL'], errors='coerce')
    features['accuracy'] = pd.to_numeric(df['Accuracy %'], errors='coerce')
    features['game_rating'] = pd.to_numeric(df['Game Rating'], errors='coerce')
    features['opponent_elo'] = pd.to_numeric(df['Opp. ELO'], errors='coerce')
    
    # Add playing side as a binary feature (1 for White, 0 for Black)
    features['played_white'] = df['Side'].apply(
        lambda x: 1 if pd.notna(x) and x.upper() in ['W', 'WHITE'] else 0
    )
    
    # Extract game length and phase features from PGN if available
    if 'PGN' in df.columns:
        import re
        
        # Extract move count as a rough estimate of game length
        features['move_count'] = df['PGN'].apply(
            lambda x: len(re.findall(r'\d+\.', x)) if pd.notna(x) else np.nan
        )
        
        # Extract result (win, loss, draw) as a numerical feature
        features['result_numeric'] = df['RESULT'].apply(
            lambda x: 1 if pd.notna(x) and x.lower() == 'win' else 
                     (0 if pd.notna(x) and x.lower() == 'loss' else 0.5)
        )
    
    # Fill missing values with mean
    features = features.fillna(features.mean())
    return features

def analyze_playing_strength(df):
    """Analyze playing strength using KMeans clustering"""
    features = extract_game_features(df)

    # Standardize features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(scaled_features)

    # Calculate cluster statistics
    cluster_stats = []
    for i in range(3):
        cluster_mask = clusters == i
        stats = {
            'cluster': i,
            'size': sum(cluster_mask),
            'avg_accuracy': features['accuracy'][cluster_mask].mean(),
            'avg_acl': features['acl'][cluster_mask].mean(),
            'avg_rating': features['game_rating'][cluster_mask].mean()
        }
        cluster_stats.append(stats)

    return pd.DataFrame(cluster_stats)

def generate_performance_insights(df):
    """Generate ML-based insights about player performance, now enhanced with PGN analysis and side-specific analysis"""
    features = extract_game_features(df)

    insights = {
        'strength_consistency': features['accuracy'].std(),
        'rating_progression': features['game_rating'].diff().mean(),
        'performance_clusters': analyze_playing_strength(df),
        'weakness_areas': identify_weakness_areas(df, features),
        'recommendations': generate_recommendations(df, features)
    }

    # Generate text insights personalized for Tony
    text_insights = []
    if insights['rating_progression'] > 0:
        text_insights.append("📈 Tony, your rating shows an improving trend")
    else:
        text_insights.append("📊 Tony, your rating has been stable or slightly declining")

    consistency = insights['strength_consistency']
    if consistency < 10:
        text_insights.append("🎯 Tony, your play shows high consistency across games")
    elif consistency < 20:
        text_insights.append("⚖️ Tony, your play shows moderate consistency")
    else:
        text_insights.append("📊 Tony, your play shows high variance between games")

    # Analyze performance by side (White vs Black)
    if 'played_white' in features.columns:
        white_games = features[features['played_white'] == 1]
        black_games = features[features['played_white'] == 0]
        
        if len(white_games) >= 3 and len(black_games) >= 3:
            # Compare average accuracy by side
            white_accuracy = white_games['accuracy'].mean()
            black_accuracy = black_games['accuracy'].mean()
            
            if white_accuracy > black_accuracy + 5:
                text_insights.append("♟️ Tony, your accuracy is significantly better when playing White")
            elif black_accuracy > white_accuracy + 5:
                text_insights.append("♟️ Tony, your accuracy is significantly better when playing Black")
            
            # Compare win rates by side if result data is available
            if 'result_numeric' in features.columns:
                white_win_rate = white_games['result_numeric'].mean() * 100
                black_win_rate = black_games['result_numeric'].mean() * 100
                
                if white_win_rate > black_win_rate + 10:
                    text_insights.append(f"♔ Tony, your win rate is higher with White ({white_win_rate:.1f}%) compared to Black ({black_win_rate:.1f}%)")
                elif black_win_rate > white_win_rate + 10:
                    text_insights.append(f"♚ Tony, your win rate is higher with Black ({black_win_rate:.1f}%) compared to White ({white_win_rate:.1f}%)")
                
                # Provide specific advice based on side performance
                if white_win_rate < 40 and len(white_games) >= 5:
                    text_insights.append("🔍 Tony, focus on strengthening your White opening repertoire with more aggressive options")
                if black_win_rate < 40 and len(black_games) >= 5:
                    text_insights.append("🔍 Tony, consider studying solid Black defenses that suit your style")
    
    # Add personalized recommendations
    text_insights.extend(insights['recommendations'])
    
    # Add PGN-based analysis if available
    if 'PGN' in df.columns and not df['PGN'].isna().all():
        try:
            # Import PGN analyzer only if needed
            from utils.pgn_analyzer import get_common_mistakes
            
            # Add common mistake patterns
            mistake_patterns = get_common_mistakes(df)
            if mistake_patterns:
                text_insights.extend([""] + ["🔍 " + pattern for pattern in mistake_patterns])
            
            # Analyze openings with side awareness
            from utils.pgn_analyzer import extract_opening_info
            
            # Create a list of (opening, side) pairs to analyze repertoire by color
            opening_side_pairs = []
            for i, row in df.iterrows():
                if not pd.isna(row['PGN']) and not pd.isna(row['Side']):
                    try:
                        opening_info = extract_opening_info(row['PGN'])
                        side = 'White' if row['Side'].upper() in ['W', 'WHITE'] else 'Black'
                        opening_side_pairs.append((opening_info['opening_main'], side))
                    except:
                        continue
            
            # Convert to DataFrame for easier analysis
            if opening_side_pairs:
                openings_df = pd.DataFrame(opening_side_pairs, columns=['Opening', 'Side'])
                
                # Get most common openings by side
                white_openings = openings_df[openings_df['Side'] == 'White']['Opening'].value_counts()
                black_openings = openings_df[openings_df['Side'] == 'Black']['Opening'].value_counts()
                
                # Add insights about most played openings by side
                if len(white_openings) > 0:
                    most_common_white = white_openings.index[0]
                    white_count = white_openings.iloc[0]
                    if white_count >= 2:
                        text_insights.append(f"♔ Tony, as White you most frequently play the {most_common_white} ({white_count} games)")
                
                if len(black_openings) > 0:
                    most_common_black = black_openings.index[0]
                    black_count = black_openings.iloc[0]
                    if black_count >= 2:
                        text_insights.append(f"♚ Tony, as Black you most frequently face the {most_common_black} ({black_count} games)")
                
                # Add advice about expanding repertoire if appropriate
                if len(white_openings) == 1 and len(df[df['Side'].isin(['W', 'White'])]) >= 5:
                    text_insights.append("🎭 Tony, consider expanding your White opening repertoire for more variety")
                if len(black_openings) == 1 and len(df[df['Side'].isin(['B', 'Black'])]) >= 5:
                    text_insights.append("🎭 Tony, consider learning additional Black defenses to handle different White setups")
        except Exception as e:
            # If any errors occur with PGN analysis, don't break the main analysis
            print(f"Error in PGN-based ML analysis: {e}")

    insights['text_insights'] = text_insights
    return insights

def identify_weakness_areas(df, features):
    """Identify areas where improvement is needed"""
    weakness_areas = []

    # Analyze accuracy trends
    if features['accuracy'].mean() < 80:
        if features['acl'].mean() > 50:
            weakness_areas.append('tactical_precision')
        else:
            weakness_areas.append('strategic_planning')

    # Analyze rating performance
    rating_diff = features['game_rating'] - features['opponent_elo']
    if rating_diff.mean() < 0:
        weakness_areas.append('underperformance')

    return weakness_areas

def generate_recommendations(df, features):
    """Generate personalized improvement recommendations"""
    recommendations = []
    weakness_areas = identify_weakness_areas(df, features)

    recommendation_map = {
        'tactical_precision': [
            "🎯 Tony, focus on tactical puzzles to improve calculation accuracy",
            "⚔️ Tony, practice endgame positions to reduce mistakes in critical positions"
        ],
        'strategic_planning': [
            "🧮 Tony, study positional chess principles to improve long-term planning",
            "🏰 Tony, review your games focusing on pawn structure decisions"
        ],
        'underperformance': [
            "🧘‍♂️ Tony, work on pre-game preparation to reduce opening mistakes",
            "⏰ Tony, practice time management with rapid games"
        ]
    }

    # Add general recommendations if no specific weaknesses found
    if not weakness_areas:
        recommendations.append("🌟 Tony, your play is well-rounded. Consider studying advanced concepts to further improve")
    else:
        for area in weakness_areas:
            recommendations.extend(recommendation_map.get(area, []))

    return recommendations