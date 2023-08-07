import streamlit as st
from PIL import Image
from pathlib import Path
from datetime import date, timedelta
import sys
import pandas as pd
import numpy as np
import datetime
import time
import matplotlib.pyplot as plt

sys.path.append('wtp_pilot')
from lib.flight_price_scraping.data_scrape import scrape_data

def get_project_root() -> str:
    return str(Path(__file__).parent.parent.parent)

def load_image(image_name: str):
    return Image.open(Path(get_project_root()) / f"wtp_pilot/references/{image_name}")

def load_data(file_name: str):
    return pd.read_csv(Path(get_project_root()) / f"wtp_pilot/inputs/{file_name}")
def plot_no_annimation(day, bookings, fares):
    # Create a Streamlit figure and axis
    fig, ax = plt.subplots()
    ax.set_xlabel('Day')
    ax.set_ylabel('Cumulative Booking')
    ax.set_title('Booking and Fare')
    ax.grid(True)

    # Create a secondary y-axis for fare
    ax2 = ax.twinx()
    ax2.set_ylabel('Fare', color='red')
    # ax2.set_label_position('right')

    # Plot cumulative booking on the left y-axis
    booking_cum_sum = bookings.cumsum()
    line1, = ax.plot(day, booking_cum_sum, marker='o', color='blue', label='Cumulative Booking')

    # Plot fare on the right y-axis
    line2, = ax2.plot(day, fares, marker='o', color='red', label='Fare')

    # Combine the legends from both axes
    lines = [line1, line2]
    ax.legend(lines, [line.get_label() for line in lines])
    
    # Create a Streamlit figure placeholder
    st_figure = st.pyplot(fig)

    # Update the plot dynamically
    
    ax.clear()
    ax2.clear()
    line1, = ax.plot(day, booking_cum_sum, marker='o', color='blue', label='Cumulative Booking')
    line2, = ax2.plot(day, fares, marker='o', color='red')

    ax.set_xlabel('Days')
    ax.set_ylabel('Cumulative Booking')
    ax2.set_ylabel('Fare', color='red')
    ax.grid(True)
    ax2.grid(False)
    ax.legend(lines, [line.get_label() for line in lines])
    ax2.legend()
    st_figure.pyplot(fig)
        # time.sleep(speed)

def plot_cumulative_booking_and_fare(day, bookings, fares, speed=0.0001):
    # Create a Streamlit figure and axis
    fig, ax = plt.subplots()
    ax.set_xlabel('Day')
    ax.set_ylabel('Cumulative Booking')
    ax.set_title('Booking and Fare')
    ax.grid(True)

    # Create a secondary y-axis for fare
    ax2 = ax.twinx()
    ax2.set_ylabel('Fare', color='red')
    # ax2.set_label_position('right')

    # Plot cumulative booking on the left y-axis
    booking_cum_sum = bookings.cumsum()
    line1, = ax.plot(day, booking_cum_sum, marker='o', color='blue', label='Cumulative Booking')

    # Plot fare on the right y-axis
    line2, = ax2.plot(day, fares, marker='o', color='red', label='Fare')

    # Combine the legends from both axes
    lines = [line1, line2]
    ax.legend(lines, [line.get_label() for line in lines])
    
    # Create a Streamlit figure placeholder
    st_figure = st.pyplot(fig)

    # Update the plot dynamically
    for i in range(len(day)):
        ax.clear()
        ax2.clear()
        line1, = ax.plot(day[:i+1], booking_cum_sum[:i+1], marker='o', color='blue', label='Cumulative Booking')
        line2, = ax2.plot(day[:i+1], fares[:i+1], marker='o', color='red')
    
        ax.set_xlabel('Days')
        ax.set_ylabel('Cumulative Booking')
        ax2.set_ylabel('Fare', color='red')
        ax.set_title('Dynamic Time Series Plot')
        ax.grid(True)
        ax2.grid(False)
        ax.legend(lines, [line.get_label() for line in lines])
        ax2.legend()
        st_figure.pyplot(fig)
        # time.sleep(speed)

# Dictionary to add values based on keys
my_dict = {0: 50, 1: 70, 2: 90, 3: 100, 4:120, 5: 150, 6: 170, 7: 190, 8: 190, 9:200}

# Function to add values from the dictionary to 'WTP' based on 'TF'
def add_values(row):
    tf_value = row['TF']
    if tf_value in my_dict:
        return row['fare'] + my_dict[tf_value]
    else:
        return row['fare']


def main():
    # Set the page title
    st.title("Flight Selection")

    # Add a sidebar
    with st.sidebar:
        # Add the logo image at the top
        st.sidebar.image(load_image("logo.png"), use_column_width=True)

        # Add a text input for departure and arrival airports
        departure_airport = st.text_input("Departure Airport (e.g., AKL)", "AKL")
        arrival_airport = st.text_input("Arrival Airport (e.g., SYD)", "SYD")

        # Calculate default departure date (3 months from today)
        # default_departure_date = date.today() + timedelta(days=90)
        default_departure_date = datetime.date(2024, 3, 1)

        # Calculate the maximum allowed departure date (1 year from today)
        # max_allowed_date = date.today() + timedelta(days=365)
        max_allowed_date = datetime.date(2024, 8, 1)

        # Add a date input for departure date
        departure_date = st.date_input("Departure Date", default_departure_date, min_value=date.today(), max_value=max_allowed_date)

        # Calculate number of days to departure
        today = date.today()
        days_to_departure = (departure_date - today).days
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

        # Read data from the CSV file in the input folder
        simulated_flight_data = load_data("booking_730_flights_36_2024_2025.csv")
        # Filter the data based on the selected departure date
        filtered_flight_data = simulated_flight_data[simulated_flight_data["departure_date"] == str(departure_date)]
        filtered_flight_data['simulation_day'] = 365 - filtered_flight_data['days_to_departure']
        filtered_flight_data['WTP2'] = filtered_flight_data['WTP']
        filtered_flight_data['WTP2'] += filtered_flight_data.groupby('TF').cumcount()
        filtered_flight_data['wtp_dtd'] = filtered_flight_data.groupby('TF')['WTP2'].transform(lambda x: x * np.random.uniform(0.7, 0.75))
        WTP_WOY = load_data("WTP_WOY.csv")
        filtered_flight_data = pd.merge(filtered_flight_data, WTP_WOY, left_on='woy_departure', right_on='WOY')
        DOW_WTP={1: 40, 2: 20, 3: 20, 4: 20, 5: 45, 6: 70, 7: 50}
        filtered_flight_data['DOW_WTP'] = filtered_flight_data['dow_departure'].map(DOW_WTP)
        filtered_flight_data['final_wtp'] = filtered_flight_data['DOW_WTP'] + filtered_flight_data['wtp_dtd'] + filtered_flight_data['WOY_WTP']
        filtered_flight_data['final_fare'] = filtered_flight_data['final_wtp'] + filtered_flight_data['bid_price']
        # Apply the function to the DataFrame
        # filtered_flight_data['fare'] = filtered_flight_data.apply(add_values, axis=1)
    # Add a button to submit the selection
    submit_button = st.button("Search Flights")

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

    # Simulation of capacity and days to departure
    # Simulation of capacity and days to departure
    st.subheader("Capacity and Days to Departure Simulation")
    box = st.empty()  # Create an empty box

    # for day in range(1, days_to_departure + 1):
    #     # Calculate the capacity for the current day (you can replace this with your actual capacity calculation logic)
    #     capacity_for_day = 100 - day  # Example: capacity decreases by 1 each day
    #     # Update the box with the current values
    #     box.text(f"Days to Departure: {days_to_departure - day}, Capacity: {capacity_for_day}")



    n_rows = 5  # Specify the number of rows to display
    # Scrape flight data and display n rows
    # competitor_flight_data = scrape_data(departure_airport, arrival_airport, str(departure_date), str(departure_date + timedelta(days=30)))
    # st.write(f"Scraped Flight Data (Showing {n_rows} rows):")
    # st.dataframe(competitor_flight_data.head(n_rows))

    # Scrape flight data and display n rows
    st.write(f"Simulated Flight Data (Showing {n_rows} rows):")
    st.dataframe(filtered_flight_data)
    col1, col2 = st.columns(2)
    # with col1:
    plot_cumulative_booking_and_fare(filtered_flight_data['simulation_day'], filtered_flight_data['booking'], filtered_flight_data['fare'])

    # with col2:
    #     plot_no_annimation(filtered_flight_data['simulation_day'], filtered_flight_data['booking'], filtered_flight_data['final_fare'])
if __name__ == '__main__':
    main()
