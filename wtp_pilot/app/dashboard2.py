import streamlit as st
from PIL import Image
from pathlib import Path
from datetime import date
import sys

sys.path.append('wtp_pilot')
from lib.bid_price.bid_price_generator import BidCalculator
from lib.flight_price_scraping.data_scrape import scrape_data

def get_project_root() -> str:
    return str(Path(__file__).parent.parent.parent)

def load_image(image_name: str):
    return Image.open(Path(get_project_root()) / f"wtp_pilot/references/{image_name}")

def calculate_days_to_departure(departure_date):
    today = date.today()
    days_to_departure = (departure_date - today).days
    return days_to_departure

def generate_bid_prices(seats_available, days_to_departure, price_range):
    bid_calculator = BidCalculator(price_range)
    bid_prices = bid_calculator.calculate_bid_prices(seats_available, days_to_departure)
    return bid_prices

def main():
    # Set the page title
    st.title("Flight Selection")

    # Add a sidebar
    with st.sidebar:
        # Add the logo image at the top
        # st.image("logo.png", use_column_width=True)
        st.sidebar.image(load_image("logo.png"), use_column_width=True)

        # Add a text input for departure and arrival airports
        departure_airport = st.text_input("Departure Airport (e.g., AKL)", "AKL")
        arrival_airport = st.text_input("Arrival Airport (e.g., SYD)", "SYD")

        # Add a date input for departure date
        departure_date = st.date_input("Departure Date")

        # Calculate number of days to departure
        days_to_departure = calculate_days_to_departure(departure_date)
        st.write(f"Days to Departure: {days_to_departure}")

        # Add a price range input
        price_range = st.sidebar.slider("Price Range", min_value=0, max_value=1000, value=(100, 500))

        # Add an input for number of seats available
        seats_available = int(st.sidebar.text_input("Number of Seats Available", "100"))

        # Add a checkbox for special event
        is_special_event = st.checkbox("Special Event on Departure Date")

        special_event_importance = None

        if is_special_event:
            # Add a slider to specify the importance of the event
            special_event_importance = st.slider("Importance of the Special Event (1-10)", 1, 10)

        

    # Add a button to submit the selection
    submit_button = st.button("Search Flights")

    # Add a button to generate bid prices
    bid_price_button = st.button("Bid Price Generator")

    # Handle the button click event
    if submit_button:
        st.write(f"Departure Airport: {departure_airport}")
        st.write(f"Arrival Airport: {arrival_airport}")
        st.write(f"Departure Date: {departure_date}")
        st.write(f"Price Range: {price_range[0]} - {price_range[1]}")
        st.write(f"Number of Seats Available: {seats_available}")
        st.write(f"Days to Departure: {days_to_departure}")

        if is_special_event:
            st.write(f"Special Event: Yes")
            st.write(f"Event Importance: {special_event_importance}")
        else:
            st.write("Special Event: No")

    if bid_price_button:
        bid_prices = generate_bid_prices(seats_available, days_to_departure, price_range)

    # Scrape flight data and display n rows
    n_rows = 5  # Specify the number of rows to display
    import datetime
    flight_data = scrape_data(departure_airport, arrival_airport, str(departure_date), str(departure_date + datetime.timedelta(days=30)))
    st.write(f"Scraped Flight Data (Showing {n_rows} rows):")
    st.dataframe(flight_data.head(n_rows))

if __name__ == '__main__':
    main()
