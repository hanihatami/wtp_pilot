import streamlit as st
from PIL import Image
from pathlib import Path
import datetime as dt
import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from utils import *

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
        ["AKL", "WLG", "CHC"]  # Example options for departure
    )

    # Dropdown for Arrival
    arrival = st.sidebar.selectbox(
        "Arrival (SYD)",
        ["SYD", "MEL", "BNE"]  # Example options for arrival
    )

    # Calculate one month from now for the minimum flight date
    one_month_from_now = dt.date.today() + dt.timedelta(days=30)

    # Date of Flight
    flight_date = st.sidebar.date_input(
        "Date of Flight",
        value=one_month_from_now,
        min_value=one_month_from_now,
        max_value=dt.date.today() + dt.timedelta(days=365)
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
            top_similar_flights = find_top_n_similar_flights(target_flight, non_NZ_flights, n=20)

            # add price
            top_similar_flights_with_price = pd.merge(top_similar_flights, prices, on= 'ItineraryID')
    # Display selected options for confirmation
    st.write(f"Departure: {departure}")
    st.write(f"Arrival: {arrival}")
    st.write(f"Date of Flight: {flight_date}")

if __name__ == "__main__":
    main()
