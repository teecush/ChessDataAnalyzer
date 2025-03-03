import plotly.express as px
import plotly.graph_objects as go

def create_rating_progression(df):
    """Create rating progression chart"""
    # Filter out rows where New Rating is NaN for the chart
    rating_df = df[df['New Rating'].notna()].copy()

    fig = px.line(rating_df, x='Date', y='New Rating',
                  title='Rating Progression Over Time',
                  labels={'New Rating': 'ELO Rating', 'Date': 'Game Date'},
                  line_shape='spline')

    fig.update_layout(
        template='plotly_white',
        hovermode='x unified'
    )
    return fig

def create_win_loss_pie(stats):
    """Create win/loss distribution pie chart"""
    labels = ['Wins', 'Losses', 'Draws']
    values = [stats['wins'], stats['losses'], stats['draws']]

    fig = go.Figure(data=[go.Pie(labels=labels, values=values,
                                hole=.3,
                                marker_colors=['#4CAF50', '#f44336', '#2196F3'])])
    fig.update_layout(title='Game Results Distribution')
    return fig

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
            showlegend=False
        )
        return fig
    else:
        # Return empty figure if no opening stats
        return go.Figure()