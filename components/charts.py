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
    
    labels = ['Wins', 'Losses', 'Draws']
    values = [wins, losses, draws]
    
    # Calculate percentages
    win_pct = round((wins / total * 100), 1) if total > 0 else 0
    loss_pct = round((losses / total * 100), 1) if total > 0 else 0
    draw_pct = round((draws / total * 100), 1) if total > 0 else 0
    
    # Create outside percentage-only labels (larger bold font for better visibility)
    outside_labels = [f'<b>Wins: {win_pct}%</b>', f'<b>Losses: {loss_pct}%</b>', f'<b>Draws: {draw_pct}%</b>']
    
    # Create inside count-only texts
    inside_counts = [str(wins), str(losses), str(draws)]

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values,
        hole=.3,
        marker_colors=['#4CAF50', '#f44336', '#2196F3'],
        # Show count inside the pie
        textinfo='value',
        textposition='inside',
        insidetextfont=dict(size=12, color='white'),
        # Don't pull any slices so they're aligned properly
        pull=[0, 0, 0],
        # Don't use text attribute for outside labels (we'll use annotations instead)
        text=None,
        hoverinfo='label+percent+value',
        hovertemplate='%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
        # Add names for the legend
        name='Game Results',
        legendgroup='results'
    )])
    
    # Add hidden traces for color legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None], 
        mode='markers',
        marker=dict(size=10, color='#4CAF50'),
        showlegend=True, name='Wins'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], 
        mode='markers',
        marker=dict(size=10, color='#f44336'),
        showlegend=True, name='Losses'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], 
        mode='markers',
        marker=dict(size=10, color='#2196F3'),
        showlegend=True, name='Draws'
    ))
    
    # Add the count labels as annotations instead of textposition='outside'
    annotations = []
    
    # Add center annotation for total
    annotations.append(
        dict(
            x=0.5,
            y=0.5,
            text=f'Total: {total}',
            showarrow=False,
            font=dict(size=14, color='black', family='Arial, sans-serif')
        )
    )
    
    # Add count labels as annotations
    for i, label in enumerate(outside_labels):
        value = values[i]
        if value > 0:  # Only add annotation if the value is positive
            # Get the angle at the middle of the slice
            angle = (2 * 3.14159 * (value/sum(values)) / 2) if i == 0 else (
                2 * 3.14159 * (sum(values[:i])/sum(values) + value/sum(values)/2)
            )
            
            # Calculate x,y position at edge of pie + offset
            r = 1.3  # radius further outside pie for better visibility
            x = 0.5 + r * np.cos(angle)
            y = 0.5 + r * np.sin(angle)
            
            # Add to annotations list
            annotations.append(
                dict(
                    x=x,
                    y=y,
                    text=label,
                    showarrow=False,
                    font=dict(size=14)
                )
            )
    
    fig.update_layout(
        title='Game Results Distribution',
        template='plotly_white',
        height=350,  # Increased height to accommodate legend
        margin=dict(l=50, r=50, t=60, b=50),  # Increased margins for outside labels
        showlegend=True,  # Show legend for the pie chart colors
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,  # Position below the chart
            xanchor="center",
            x=0.5
        ),
        annotations=annotations
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