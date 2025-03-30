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
    """Generate ML-based insights about player performance, now enhanced with PGN analysis"""
    features = extract_game_features(df)

    insights = {
        'strength_consistency': features['accuracy'].std(),
        'rating_progression': features['game_rating'].diff().mean(),
        'performance_clusters': analyze_playing_strength(df),
        'weakness_areas': identify_weakness_areas(df, features),
        'recommendations': generate_recommendations(df, features)
    }

    # Generate text insights
    text_insights = []
    if insights['rating_progression'] > 0:
        text_insights.append("📈 Your rating shows an improving trend")
    else:
        text_insights.append("📊 Your rating has been stable or slightly declining")

    consistency = insights['strength_consistency']
    if consistency < 10:
        text_insights.append("🎯 Your play shows high consistency across games")
    elif consistency < 20:
        text_insights.append("⚖️ Your play shows moderate consistency")
    else:
        text_insights.append("📊 Your play shows high variance between games")

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
                
            # Add opening-based recommendations if we have enough data
            # Count openings played at least twice
            from utils.pgn_analyzer import extract_opening_info
            opening_counts = df['PGN'].apply(
                lambda x: extract_opening_info(x)['opening'] if pd.notna(x) and x else None
            ).value_counts()
            
            common_openings = opening_counts[opening_counts >= 2].index.tolist()
            
            if common_openings:
                # Get most common opening
                most_common = common_openings[0]
                text_insights.append(f"🏆 You have the most experience with the {most_common} opening")
                
                # Add advice about expanding repertoire if appropriate
                if len(common_openings) <= 2 and len(df) >= 10:
                    text_insights.append("🎭 Consider expanding your opening repertoire to gain experience with different structures")
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
            "🎯 Focus on tactical puzzles to improve calculation accuracy",
            "⚔️ Practice endgame positions to reduce mistakes in critical positions"
        ],
        'strategic_planning': [
            "🧮 Study positional chess principles to improve long-term planning",
            "🏰 Review your games focusing on pawn structure decisions"
        ],
        'underperformance': [
            "🧘‍♂️ Work on pre-game preparation to reduce opening mistakes",
            "⏰ Practice time management with rapid games"
        ]
    }

    # Add general recommendations if no specific weaknesses found
    if not weakness_areas:
        recommendations.append("🌟 Your play is well-rounded. Consider studying advanced concepts to further improve")
    else:
        for area in weakness_areas:
            recommendations.extend(recommendation_map.get(area, []))

    return recommendations