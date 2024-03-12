import streamlit as st
import toml
from PIL import Image
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
# import plotly.express as px
from datetime import datetime, timedelta
################################################################
def get_project_root() -> str:
    return str(Path(__file__).parent.parent.parent)

def load_image(image_name: str):
    return Image.open(Path(get_project_root()) / f"wtp_pilot/references/{image_name}")

def load_config(config_readme_filename):
    return toml.load(Path(get_project_root()) / f"wtp_pilot/config/{config_readme_filename}")
################################################################
# Load config
readme = load_config('config_readme.toml')
# Page config
st.set_page_config(page_title="Pilot", layout="wide")
################################################################
# Info
with st.expander(
    "Pilot app to build a WTP estimation for a pretend flight", expanded=False
):
    st.write(readme["app"]["app_intro"])
    st.write("")
st.write("")
st.sidebar.image(load_image("logo.jpg"), use_column_width=True)
################################################################
# Load data
df = pd.read_csv(Path(get_project_root()) / "wtp_pilot/inputs/wtp_mock_data4.csv")
################################################################
# Sample data: Mapping of flight numbers to a list of departure times
flight_departure_times = {
    "FL100": ["06:00", "14:00", "22:00"],
    "FL101": ["07:00", "15:00", "23:00"],
    "FL102": ["08:00", "16:00"],
    "FL103": ["09:00", "17:00", "01:00"],
    "FL104": ["10:00", "18:00", "02:00"],
}
################################################################
with st.sidebar:
    with st.expander("Flight", expanded=True):
        # Flight Details Expander
        # This section allows users to specify details for a flight booking within an expander UI element.
        # Users can select a flight number, flight class, departure date, and time, which can be used
        # for further processing like price calculations or seat availability checks.
        flight_selected = st.selectbox(
            "Flight Number",
            options=list(flight_departure_times.keys()),
            help="Select a flight number from the list."
        )
        
        # Flight Class Selection
        # Provides a dropdown for the user to select the class of service.
        # Options range from basic economy to first class, affecting price and comfort level.
        class_selected = st.selectbox(
            "Flight Class",
            ["Economy Basic", "Economy Standard", "Economy Flex", "Premium Economy",
            "Business Standard", "Business Flex", "First Class"],
            help="Select your preferred class for the flight."
        )

        # Departure Date Selection
        # A date input is used for the user to pick the date of departure,
        # with the minimum selectable date being the current day.
        departure_date = st.date_input(
            "Departure Date",
            min_value=datetime.today(),
            help="Select the departure date for your flight."
        )
        
        # Departure Time Selection
        # Once a flight number is selected, this dropdown shows the available departure times.
        # It's dynamically populated based on the flight number selected by the user.
        if flight_selected:
            departure_time = st.selectbox(
                "Departure Time",
                options=flight_departure_times[flight_selected],
                help="Select the departure time for your flight."
            )

            # Optionally, parse the selected time as a datetime object for further use
            departure_datetime_str = f"{departure_date} {departure_time}"
            departure_datetime = datetime.strptime(departure_datetime_str, "%Y-%m-%d %H:%M")

################################################################
    # Competitor Comparison Expander
    # This section is dedicated to comparing the pricing of the selected flight with other airlines.
    # It provides options for users to select competitors and set a range of dates for which 
    # they want to compare the prices, accounting for potential differences in flight schedules.

    with st.expander("Competitor Comparison", expanded=True):
            # Competitor Airline Selection
            # Users can select multiple airlines to compare their flight prices with the current selection.
            # This helps in understanding the market positioning of the selected flight's pricing.
            competitor_airlines = st.multiselect(
                "Select Competitor Airlines",
                ["Airline A", "Airline B", "Airline C"],  # Example competitor names
                help="Select one or more competitor airlines for price comparison."
            )

            # Date Flexibility Selection
            # This slider allows users to define a range of dates for the competitor price comparison.
            # The flexibility helps to find the best comparable prices if competitors do not have 
            # flights on the exact selected departure date.
            date_flexibility = st.slider(
                "Select Date Flexibility (Days)",
                min_value=0,
                max_value=7,
                value=3,  # Default value showing +/- 3 days flexibility
                help="Select how many days around the departure date to include in the comparison."
            )

            # Flexible Date Range Calculation
            # Based on the selected date flexibility, calculate the start and end dates for the 
            # comparison period. This range is used to query competitor prices within a window 
            # around the chosen departure date.
            start_date = departure_date - timedelta(days=date_flexibility)
            end_date = departure_date + timedelta(days=date_flexibility)

##################################################################
#######                  TODO: Function                    #######

# write a function that for each flight gets the compatitors price
# from the amadius api
##################################################################

# Dashboard Metrics Section
# -------------------------
# This section creates a visual dashboard with key airline metrics using Plotly indicators.
# Each column represents a different metric related to airline operations:
# - Column 1: Available Seats - Displays the number of seats currently available for booking on a particular flight.
# - Column 2: Load Factor - Shows the percentage of seats filled on the flight.
# - Column 3: Days to Departure (DTD) - Indicates the number of days remaining until the flight departs.
# - Column 4: Bid Price - Represents the current price point for bidding on seat sales, with a delta showing the change from the previous day.
# These metrics provide a quick snapshot of the flight's booking status and pricing strategy for revenue management purposes.col1, col2, col3, col4 = st.columns(4)

col1, col2, col3, col4 = st.columns(4)
with col1:
    available_seats_figure = go.Figure()
    available_seats_figure.add_trace(go.Indicator(
        mode="number",
        value=20,
        number={'suffix': ""},
        title={"text": "<span style='font-size:1.5em;color:gray'>Available Seats</span>"}
    ))
    available_seats_figure.update_layout(height=300, width=300)
    st.plotly_chart(available_seats_figure)

with col2:
    load_factor_figure = go.Figure()
    load_factor_figure.add_trace(go.Indicator(
        mode="number",
        value=80,
        number={'suffix': "%"},
        title={"text": "<span style='font-size:1.5em;color:gray'>Load Factor</span>"}
    ))
    load_factor_figure.update_layout(height=300, width=300)
    st.plotly_chart(load_factor_figure)

with col3:
    dtd_figure = go.Figure()
    dtd_figure.add_trace(go.Indicator(
        mode="number",
        value=15,
        number={'suffix': ""},
        title={"text": "<span style='font-size:1.5em;color:gray'>Days to Departure</span>"}
    ))
    dtd_figure.update_layout(height=300, width=300)
    st.plotly_chart(dtd_figure)

with col4:
    bid_price_figure = go.Figure()
    bid_price_figure.add_trace(go.Indicator(
        mode="number+delta",
        value=105,
        delta={'reference': 90, 'valueformat': ".2f"},
        number={'prefix': "$"},
        title={"text": "<span style='font-size:1.5em;color:gray'>Bid Price</span>"}
    ))
    bid_price_figure.update_layout(height=300, width=300)
    st.plotly_chart(bid_price_figure)
##################################################################
