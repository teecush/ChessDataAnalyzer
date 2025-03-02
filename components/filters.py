import streamlit as st

def create_filters(df):
    """Create sidebar filters for the dashboard"""
    st.sidebar.header('Filters')
    
    # Date range filter
    date_range = st.sidebar.date_input(
        'Select Date Range',
        [df['Date'].min(), df['Date'].max()]
    )
    
    # Result filter
    results = st.sidebar.multiselect(
        'Select Results',
        options=['Win', 'Loss', 'Draw'],
        default=['Win', 'Loss', 'Draw']
    )
    
    # Rating range filter
    rating_range = st.sidebar.slider(
        'Rating Range',
        int(df['Rating'].min()),
        int(df['Rating'].max()),
        (int(df['Rating'].min()), int(df['Rating'].max()))
    )
    
    return {
        'date_range': date_range,
        'results': results,
        'rating_range': rating_range
    }

def apply_filters(df, filters):
    """Apply selected filters to the dataframe"""
    mask = (
        (df['Date'].dt.date >= filters['date_range'][0]) &
        (df['Date'].dt.date <= filters['date_range'][1]) &
        (df['Result'].isin(filters['results'])) &
        (df['Rating'].between(filters['rating_range'][0], filters['rating_range'][1]))
    )
    return df[mask]
