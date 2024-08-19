from data_columns import column_names
import pandas as pd
import streamlit as st
from probabilistic_summarizer import summarize_news
import datetime
from title_extractor import extract_article_text



# Create the Streamlit app
# Create the Streamlit app
st.title('Top 3 Most Mentioned News Articles')

def date_selector():
    # Get today's date
    today = datetime.date.today()

    # Option to choose between today and date range
    date_option = st.radio("Get news from:", ["Today", "Choose dates"])

    if date_option == "Today":
        return today, today
    else:
        # Allow user to select start and end dates
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", today, max_value=today)
        with col2:
            # Ensure the initial end_date is not after today
            initial_end_date = min(today, start_date)
            end_date = st.date_input("End date", initial_end_date, min_value=start_date, max_value=today)

        # Calculate the difference between start and end dates
        date_difference = (end_date - start_date).days

        # Check if the range is within 31 days
        if date_difference > 31:
            st.error("Please select a date range of 31 days or fewer.")
            return None, None
        else:
            return start_date, end_date

# Calculate the date range
start_date, end_date = date_selector()
if start_date == None:
    pass
elif start_date == end_date:
    st.write(f"Fetching news from {start_date}")
else:
    st.write(f"Fetching news from {start_date} to {end_date}")



def get_urls(start_date, end_date, num_urls):
    if start_date == end_date:
        date = start_date.strftime("%Y%m%d")
        data = pd.read_csv(f"GDELT Event Files/{date}.export.CSV", sep="\t", header=None)
        data.columns = column_names
        clean_data = data.drop_duplicates(subset='source_url')
        relevant_data = clean_data[['num_sources', 'source_url']]
        sorted_data = relevant_data.sort_values(by='num_sources', ascending=False).head(num_urls)
        urls = sorted_data.source_url.values.tolist()
        return urls
    else:
        all_dfs = []
        days = (end_date - start_date).days
        date = start_date.strftime("%Y%m%d")
        for i in range(days):
            date = (start_date + datetime.timedelta(days=i)).strftime("%Y%m%d")
            # I want to combine all the csv in the chooosen dates
            data = pd.read_csv(f"GDELT Event Files/{date}.export.CSV", sep="\t", header=None)
            data.columns = column_names
            clean_data = data.drop_duplicates(subset='source_url')
            relevant_data = clean_data[['num_sources', 'source_url']]
            all_dfs.append(relevant_data)
        data = pd.concat(all_dfs)
        sorted_data = data.sort_values(by='num_sources', ascending=False).head(num_urls)
        urls = sorted_data.source_url.values.tolist()
        return urls



urls = get_urls(start_date, end_date, 5)
# Generate summaries
summaries = [url for url in urls]


# Create a container for the scrollable area
with st.container():
    for i, (url, summary) in enumerate(zip(urls, summaries), 1):
        # Extract title from the URL (you might want to improve this based on your actual data)
        title = extract_article_text(url)
        # If not title, ask GPT to create one based on the summary
        
        # Create an expander for each article
        with st.expander(title):
            st.write(summary)

# Add some CSS to make the container scrollable
st.markdown("""
    <style>
        .stContainer {
            max-height: 400px;
            overflow-y: auto;
        }
    </style>
    """, unsafe_allow_html=True)