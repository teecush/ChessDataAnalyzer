import streamlit as st

def create_filters(df):
    """Create sidebar filters for the dashboard"""
    st.sidebar.header('Filters')

    # Show available date range
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    st.sidebar.text(f"Available dates:\n{min_date} to {max_date}")

    # Date range filter - default to full range
    date_range = st.sidebar.date_input(
        'Select Date Range',
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Rating range filter
    rating_range = st.sidebar.slider(
        'Rating Range',
        int(df['New Rating'].min()),
        int(df['New Rating'].max()),
        (int(df['New Rating'].min()), int(df['New Rating'].max()))
    )

    # Debug info
    st.sidebar.text(f"Selected date range:\n{date_range[0]} to {date_range[1]}")

    return {
        'date_range': date_range,
        'rating_range': rating_range
    }

def apply_filters(df, filters):
    """Apply selected filters to the dataframe"""
    mask = (
        (df['Date'].dt.date >= filters['date_range'][0]) &
        (df['Date'].dt.date <= filters['date_range'][1]) &
        (df['New Rating'].between(filters['rating_range'][0], filters['rating_range'][1]))
    )
    return df[mask].copy()  # Return a copy to avoid SettingWithCopyWarning