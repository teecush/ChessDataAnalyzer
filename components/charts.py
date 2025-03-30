import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def create_rating_progression(df):
    """Create rating progression chart"""
    # Filter out rows where New Rating is NaN for the chart
    rating_df = df[df['New Rating'].notna()].copy()

    # Create base figure
    fig = go.Figure()

    # Add main line
    fig.add_trace(go.Scatter(
        x=rating_df['Date'],
        y=rating_df['New Rating'],
        mode='lines+markers',
        name='Rating',
        line=dict(color='#4CAF50', shape='spline'),
        marker=dict(size=4)
    ))

    # Add linear trendline
    if len(rating_df) > 1:
        x_numeric = np.arange(len(rating_df))
        z = np.polyfit(x_numeric, rating_df['New Rating'], 1)
        p = np.poly1d(z)

        fig.add_trace(go.Scatter(
            x=rating_df['Date'],
            y=p(x_numeric),
            mode='lines',
            name='Trend',
            line=dict(color='#FF4B4B', width=2, dash='dash'),
            showlegend=True
        ))

    fig.update_layout(
        title='Rating Progression Over Time',
        template='plotly_white',
        hovermode='x unified',
        height=300,  # Reduced height for mobile
        margin=dict(l=10, r=10, t=60, b=10),  # Increased top margin to prevent toolbar overlap
        xaxis_title=None,  # Remove axis titles for cleaner mobile view
        yaxis_title=None,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig

def create_win_loss_pie(df):
    """Create win/loss distribution pie chart"""
    # Count results with case-insensitive matching
    # Use 'RESULT' column instead of 'Result'
    result_counts = df['RESULT'].str.lower().value_counts()
    wins = result_counts.get('win', 0)
    losses = result_counts.get('loss', 0)
    draws = result_counts.get('draw', 0)
    
    total = sum([wins, losses, draws])
    
    # Calculate percentages
    win_pct = (wins / total * 100) if total > 0 else 0
    loss_pct = (losses / total * 100) if total > 0 else 0
    draw_pct = (draws / total * 100) if total > 0 else 0

    labels = ['Wins', 'Losses', 'Draws']
    values = [wins, losses, draws]
    
    # Create outside text labels with count values
    outside_labels = [f'Wins: {wins}', f'Losses: {losses}', f'Draws: {draws}']

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values,
        hole=.3,
        marker_colors=['#4CAF50', '#f44336', '#2196F3'],
        # Inside text will show percentages
        textinfo='percent',
        textposition='inside',
        insidetextfont=dict(size=12, color='white'),
        # Don't pull any slices so they're aligned properly
        pull=[0, 0, 0],
        # Add count values outside the pie
        text=outside_labels,
        texttemplate='%{text}',
        textfont=dict(size=12),
        hoverinfo='label+percent+value',
        hovertemplate='%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    # Add the count labels as annotations instead of textposition='outside'
    annotations = []
    
    # Add center annotation for total
    annotations.append(
        dict(
            x=0.5,
            y=0.5,
            text=f'Total: {total}',
            showarrow=False,
            font=dict(size=12)
        )
    )
    
    fig.update_layout(
        title='Game Results Distribution',
        template='plotly_white',
        height=300,  # Reduced height for mobile
        margin=dict(l=20, r=20, t=60, b=20),  # Increased margins for text labels
        showlegend=False,  # Hide legend since we're using direct labels
        annotations=annotations
    )
    
    # Add count labels as separate annotations
    for i, label in enumerate(outside_labels):
        value = values[i]
        if value > 0:  # Only add annotation if the value is positive
            # Get the angle at the middle of the slice
            angle = (2 * 3.14159 * (value/sum(values)) / 2) if i == 0 else (
                2 * 3.14159 * (sum(values[:i])/sum(values) + value/sum(values)/2)
            )
            
            # Calculate x,y position at edge of pie + offset
            r = 1.1  # radius slightly outside pie
            x = 0.5 + r * np.cos(angle)
            y = 0.5 + r * np.sin(angle)
            
            fig.add_annotation(
                x=x,
                y=y,
                text=label,
                showarrow=False,
                font=dict(size=10)
            )
    
    return fig

def create_metric_over_time(df, metric_col, title, y_label):
    """Create line chart for metrics over time"""
    # Filter out rows where metric is NaN
    metric_df = df[df[metric_col].notna()].copy()

    # Create base line plot
    fig = go.Figure()

    # Add main line
    fig.add_trace(go.Scatter(
        x=metric_df['Date'],
        y=metric_df[metric_col],
        mode='lines+markers',
        name='Actual',
        line=dict(color='#4CAF50', shape='spline'),
        marker=dict(size=4)  # Smaller markers for mobile
    ))

    # Add linear trendline
    if len(metric_df) > 1:
        x_numeric = np.arange(len(metric_df))
        z = np.polyfit(x_numeric, metric_df[metric_col], 1)
        p = np.poly1d(z)

        fig.add_trace(go.Scatter(
            x=metric_df['Date'],
            y=p(x_numeric),
            mode='lines',
            name='Trend',
            line=dict(color='#FF4B4B', width=2, dash='dash'),
            showlegend=True
        ))

    fig.update_layout(
        title=title,
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        height=300,  # Reduced height for mobile
        margin=dict(l=10, r=10, t=60, b=10),  # Increased top margin to prevent toolbar overlap
        xaxis_title=None,  # Remove axis titles for cleaner mobile view
        yaxis_title=None
    )
    return fig

def create_performance_charts(df):
    """Create all performance metric charts"""
    charts = {
        'acl': create_metric_over_time(
            df, 'ACL',
            'ACL Over Time',
            'ACL'
        ),
        'accuracy': create_metric_over_time(
            df, 'Accuracy %',
            'Accuracy % Over Time',
            'Accuracy %'
        ),
        'game_rating': create_metric_over_time(
            df, 'Game Rating',
            'Game Rating Over Time',
            'Game ELO'
        ),
        'performance_rating': create_metric_over_time(
            df, 'Performance Rating',
            'Performance Rating Over Time',
            'Performance Rating'
        )
    }
    return charts

def create_opening_bar(opening_stats):
    """Create opening statistics bar chart"""
    if not opening_stats.empty:
        fig = go.Figure(data=[
            go.Bar(
                x=opening_stats.index,
                y=opening_stats.values,
                marker_color='#4CAF50'
            )
        ])
        fig.update_layout(
            title='Most Played Openings',
            xaxis_tickangle=-45,
            template='plotly_white',
            showlegend=False,
            height=300,  # Reduced height for mobile
            margin=dict(l=10, r=10, t=60, b=10) # Increased top margin to prevent toolbar overlap
        )
        return fig
    else:
        # Return empty figure if no opening stats
        return go.Figure()