import streamlit as st

def create_filters(df):
    """Create sidebar filters for the dashboard"""
    st.sidebar.header('Filters')

    # Show available date range
    valid_dates = df[df['Date'].notna()]['Date']
    if len(valid_dates) > 0:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
        st.sidebar.text(f"Available dates:\n{min_date} to {max_date}")

        # Date range filter - default to full range
        date_range = st.sidebar.date_input(
            'Select Date Range',
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = None
        st.sidebar.text("No valid dates available")

    # Rating range filter - only for games with ratings
    valid_ratings = df[df['New Rating'].notna()]['New Rating']
    if len(valid_ratings) > 0:
        rating_range = st.sidebar.slider(
            'Rating Range',
            int(valid_ratings.min()),
            int(valid_ratings.max()),
            (int(valid_ratings.min()), int(valid_ratings.max()))
        )
    else:
        rating_range = None
        st.sidebar.text("No valid ratings available")

    # Debug info
    if date_range:
        st.sidebar.text(f"Selected date range:\n{date_range[0]} to {date_range[1]}")

    return {
        'date_range': date_range,
        'rating_range': rating_range
    }

def apply_filters(df, filters):
    """Apply selected filters to the dataframe"""
    filtered_df = df.copy()  # Start with a copy of all data

    # Apply date filter only to rows with valid dates
    if filters['date_range']:
        date_mask = df['Date'].isna() | (
            (df['Date'].dt.date >= filters['date_range'][0]) &
            (df['Date'].dt.date <= filters['date_range'][1])
        )
        filtered_df = filtered_df[date_mask]

    # Apply rating filter only to rows with valid ratings
    if filters['rating_range']:
        rating_mask = df['New Rating'].isna() | (
            df['New Rating'].between(filters['rating_range'][0], filters['rating_range'][1])
        )
        filtered_df = filtered_df[rating_mask]

    return filtered_df  # Return a copy to avoid SettingWithCopyWarning