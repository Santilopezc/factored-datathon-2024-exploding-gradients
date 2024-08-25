import streamlit as st
import pandas as pd
from databricks import sql
import os
from datetime import datetime, timedelta
from llm_summary import summarize_news_article
from title_extractor import extract_article_text

# Databricks connection parameters
SERVER_HOSTNAME = os.getenv("SERVER_HOSTNAME")
HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")
ACCESS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# Create the Streamlit app
st.title('Top News Articles')

# Use streamlit's caching mechanism
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def get_cached_summary(url):
    with st.spinner('Generating summary'):
        title = extract_article_text(url)
        summary, category = summarize_news_article(url)
        if summary is None or "unavailable" in title or "BizToc" in title:
            return None, None, None
        return title, summary, category

# Add a sidebar for category selection
st.sidebar.title("News Categories")
selected_category = st.sidebar.selectbox(
    "Select categories to display",
    ["All", "Political", "Economical", "Social"]
)

def date_selector():
    today = datetime.now().date()
    date_option = st.radio("Get news from:", ["Today", "Choose dates"])
    if date_option == "Today":
        return today, today
    else:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", today, max_value=today)
        with col2:
            initial_end_date = min(today, start_date)
            end_date = st.date_input("End date", initial_end_date, min_value=start_date, max_value=today)
        date_difference = (end_date - start_date).days
        if date_difference > 31:
            st.error("Please select a date range of 31 days or fewer.")
            return None, None
        return start_date, end_date

# Calculate the date range
start_date, end_date = date_selector()

def get_urls_from_databricks(start_date, end_date, num_urls):
    with sql.connect(
        server_hostname=SERVER_HOSTNAME,
        http_path=HTTP_PATH,
        access_token=ACCESS_TOKEN
    ) as connection:
        with connection.cursor() as cursor:
            query = f"""
            SELECT SOURCEURL
            FROM gold_layer
            WHERE Day >= '{start_date.strftime("%Y%m%d")}' AND Day <= '{end_date.strftime("%Y%m%d")}'
            ORDER BY Importance DESC
            LIMIT {num_urls}
            """
            cursor.execute(query)
            result = cursor.fetchall()
    return [row[0] for row in result]

if start_date and end_date:
    if start_date == end_date:
        st.write(f"Fetching news from {start_date}")
    else:
        st.write(f"Fetching news from {start_date} to {end_date}")

    try:
        urls = get_urls_from_databricks(start_date, end_date, 100)

        # Generate summaries
        num_news = 0
        with st.container():
            for url in urls:
                if num_news >= 10:
                    break
                title, summary, category = get_cached_summary(url)
                if title and summary and category:
                    num_news += 1
                    if selected_category == "All" or category == selected_category:
                        with st.expander(f"{category}: {title}"):
                            st.write(f'Summary: {summary}')
                            st.write(f'URL: {url}')
    except Exception as e:
        st.error(f"An error occurred while fetching data: {str(e)}")