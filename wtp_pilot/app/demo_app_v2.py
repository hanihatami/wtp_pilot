import streamlit as st
from PIL import Image
from pathlib import Path
import datetime as dt
import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import sys
import pandas as pd
import plotly.graph_objects as go

sys.path.append('/Users/hanih/Documents/Projects/wtp_pilot/wtp_pilot/lib/flight_utils')
sys.path.append('/Users/hanih/Documents/Projects/wtp_pilot/wtp_pilot/lib/bid_price_utils')
from flight_utils import *
from demand_rate import *
from bid_price import *

# Load environment variables from .env file
load_dotenv()

# Function to get the project root directory
def get_project_root() -> str:
    return str(Path(__file__).parent.parent.parent)

# Function to load an image
def load_image(image_name: str):
    image_path = Path(get_project_root()) / f"wtp_pilot/references/{image_name}"
    return Image.open(image_path)

# Cache the function to get flights info
@st.cache_data
def cached_get_flights_info(_client, departure, arrival, flight_date, day_range):
    return get_flights_info(_client, departure, arrival, flight_date, day_range)

# Page config
st.set_page_config(page_title="Pilot", layout="wide")
# Main function where we design our Streamlit app
def main():
    amadeus = Client(
        client_id=os.getenv('AMADEUS_CLIENT_ID'),
        client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
    )

    # Load the image and display it in the sidebar
    logo_image = load_image("logo.jpg")
    st.sidebar.image(logo_image, use_column_width=True)

    # Dropdown for Departure
    departure = st.sidebar.selectbox(
        "Departure (AKL)",
        ["AKL", "WLG"]  # Example options for departure
    )

    # Dropdown for Arrival
    arrival = st.sidebar.selectbox(
        "Arrival (SYD)",
        ["SYD", "MEL"]  # Example options for arrival
    )
    today = dt.date.today()
    # Calculate one month from now for the minimum flight date
    one_month_from_now = today+ dt.timedelta(days=30)

    # Date of Flight
    flight_date = st.sidebar.date_input(
        "Date of Flight",
        value=one_month_from_now,
        min_value=one_month_from_now,
        max_value= today + dt.timedelta(days=365)
    )

    # Flexibility parameter for departure date
    flexibility = st.sidebar.slider(
        "Flexibility in days around departure date",
        min_value=0, max_value=3, value=0, step=1,
        help="Specifies how many days before or after the selected departure date you are willing to consider for your flight."
    )

    # if st.sidebar.button('Search Flights'):
    if True:
        with st.spinner('Fetching flight information...'):
            try:
                flights_info = cached_get_flights_info(amadeus, departure, arrival, flight_date, day_range=flexibility)
                segments, fares, flights, prices = parse_flight_details(flights_info)
                NZ_nonStop_flights, non_NZ_flights = filter_and_merge_flights(segments, flights, fares)
                NZ_flights_for_DepartureDay = filter_flights_by_departure_date(NZ_nonStop_flights, flight_date)

                if NZ_flights_for_DepartureDay.shape[0] > 0:
                    departure_times = NZ_flights_for_DepartureDay['DepartureTime'].unique()
                    departure_times = sorted(departure_times)
                    selected_time = st.sidebar.selectbox(
                        "Time of Flight",
                        options=departure_times,
                        index=0,
                        format_func=lambda x: x.strftime('%H:%M') if isinstance(x, dt.time) else x
                    )
                else:
                    st.sidebar.write("No flights found for the selected criteria.")
            except ResponseError as e:
                st.error('Failed to fetch flight information. Please try again later.')

            target_flight = NZ_flights_for_DepartureDay[NZ_flights_for_DepartureDay['DepartureTime'] == selected_time].iloc[0]
            cabin_capacities = {"ECONOMY": 180, "BUSINESS":  30, "FIRST CLASS": 10}
            target_flight['Capacity'] = cabin_capacities.get(target_flight['Cabin'])

            # Ensure that target_flight['Capacity'] is not None or 0 to avoid errors
            available_seats = st.sidebar.slider(
                "Select Available Seats",
                min_value=1,
                max_value=target_flight['Capacity'],
                value=1  # Default value
    )
            days_to_departure = (flight_date - today).days

            top_similar_flights = find_top_n_similar_flights(target_flight, non_NZ_flights, n=20)

            # add price
            top_similar_flights_with_price = pd.merge(top_similar_flights, prices, on= 'ItineraryID')
            target_flight_price = prices.loc[prices['ItineraryID'] == target_flight['ItineraryID'], 'Total']

            demand_rate_per_tf = generate_demand_rates(target_flight, num_tfs=10)
            bid_calculator = BidCalculator((100, 400), 'ECONOMY', flight_date, demand_rate_per_tf, 1)
            optimal_bid_prices = bid_calculator.calculate_bid_price(seats=target_flight['Capacity'], time=days_to_departure + 1)

            # spacer, col1, col2, col3, col4, spacer = st.columns([0.5, 10, 10, 10, 10, 1])
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                available_seats_figure = go.Figure()
                available_seats_figure.add_trace(go.Indicator(
                    mode="number",
                    value=available_seats,
                    number={'suffix': ""},
                    title={"text": "<span style='font-size:1.5em;color:gray'>Available Seats</span>"}
                ))
                available_seats_figure.update_layout(height=300, width=300)
                st.plotly_chart(available_seats_figure)

            with col2:
                load_factor_figure = go.Figure()
                load_factor_figure.add_trace(go.Indicator(
                    mode="number",
                    value=int((target_flight['Capacity'] - available_seats)/target_flight['Capacity'] * 100),
                    number={'suffix': "%"},
                    title={"text": "<span style='font-size:1.5em;color:gray'>Load Factor</span>"}
                ))
                load_factor_figure.update_layout(height=300, width=300)
                st.plotly_chart(load_factor_figure)

            with col3:
                dtd_figure = go.Figure()
                dtd_figure.add_trace(go.Indicator(
                    mode="number",
                    value=days_to_departure,
                    number={'suffix': ""},
                    title={"text": "<span style='font-size:1.5em;color:gray'>Days to Departure</span>"}
                ))
                dtd_figure.update_layout(height=300, width=300)
                st.plotly_chart(dtd_figure)

            with col4:
                bid_price_figure = go.Figure()
                bid_price_figure.add_trace(go.Indicator(
                    mode="number+delta",
                    value=int(optimal_bid_prices[(available_seats, days_to_departure)]),
                    delta={'reference': int(optimal_bid_prices[(available_seats+1, days_to_departure+1)]), 'valueformat': ".2f"},
                    number={'prefix': "$"},
                    title={"text": "<span style='font-size:1.5em;color:gray'>Bid Price</span>"}
                ))
                bid_price_figure.update_layout(height=300, width=300)
                st.plotly_chart(bid_price_figure)
                ##################################################################

            col1, col2, col3 = st.columns([1,6,1])  # Adjust the ratio as needed
            with col2:
                display_price_distribution_v2(top_similar_flights_with_price, target_flight_price)

        
    # Display selected options for confirmation
    st.write(f"Departure: {departure}")
    st.write(f"Arrival: {arrival}")
    st.write(f"Date of Flight: {flight_date}")

if __name__ == "__main__":
    main()
