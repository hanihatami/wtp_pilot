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
import plotly.graph_objects as go
import plotly.express as px

# from lib.flight_price_scraping.data_scrape import scrape_data

sys.path.append('wtp_pilot')
st.set_page_config(page_title="Pilot", layout="wide")

def get_project_root() -> str:
    return str(Path(__file__).parent.parent.parent)

def load_image(image_name: str):
    return Image.open(Path(get_project_root()) / f"wtp_pilot/references/{image_name}")

def load_data(file_name: str):
    return pd.read_csv(Path(get_project_root()) / f"wtp_pilot/inputs/{file_name}")


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
        ax.grid(False)
        ax2.grid(False)
        ax.legend(lines, [line.get_label() for line in lines])
        ax2.legend()
        st_figure.pyplot(fig)
        time.sleep(speed)

def plot_no_annimation(day, bookings, fares):
    # Create a Streamlit figure placeholder
    st_figure = st.empty()

    # Create a Plotly figure
    fig = go.Figure()

    # Plot cumulative booking on the left y-axis
    booking_cum_sum = bookings.cumsum()
    fig.add_trace(go.Scatter(x=day, y=booking_cum_sum, mode='markers+lines', name='Cumulative Booking', line=dict(color='#1f77b4')))

    # Plot fare on the right y-axis
    fig.add_trace(go.Scatter(x=day, y=fares, mode='lines+markers', name='Fare', line=dict(color='#ff7f0e'), yaxis='y2'))

    # Update the layout
    fig.update_layout(
        title='Booking and Fare',
        xaxis_title='Days',
        yaxis=dict(title='Cumulative Booking'),
        yaxis2=dict(title='Fare', overlaying='y', side='right', showgrid=False),
        legend=dict(yanchor='top', y=0.99, xanchor='left', x=0.01),
        height=400,  # Adjust the height of the Plotly figure
        width=600
    )

    # Render the Plotly figure using Streamlit
    st.plotly_chart(fig)

def create_stacked_bar_chart(tf_wtp_dtd_fare):
    # Sample data
    categories = tf_wtp_dtd_fare['TF']
    stack1 = tf_wtp_dtd_fare['wtp_dtd']
    stack2 = tf_wtp_dtd_fare['woy']
    stack3 = tf_wtp_dtd_fare['dow']
    # Create the Plotly figure
    fig = go.Figure()

    # Add the first stack
    fig.add_trace(go.Bar(
        x=categories,
        y=stack1,
        name='DTD',
    ))

    # Add the second stack on top of the first one
    fig.add_trace(go.Bar(
        x=categories,
        y=stack2,
        name='WOY',
        base=stack1,  # The base for the second stack is the first stack
    ))
        # Add the second stack on top of the first one
    fig.add_trace(go.Bar(
        x=categories,
        y=stack3,
        name='DOW',
        base=stack1,  # The base for the second stack is the first stack
    ))

    # Update the layout
    fig.update_layout(
        barmode='stack',  # Set the barmode to 'stack' for stacking bars
        title='WTP Component',
        xaxis_title='DCP',
        yaxis_title='',
        height=400,  # Adjust the height of the Plotly figure
        width=600
    )

     # Render the Plotly figure using Streamlit
    st.plotly_chart(fig)

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
    st.title("Flight Information")

    # Add a sidebar
    with st.sidebar:
        # Add the logo image at the top
        st.sidebar.image(load_image("logo.jpg"), use_column_width=True)

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
        filtered_flight_data['wtp_dtd'] = filtered_flight_data.groupby('TF')['fare'].transform(lambda x: x * np.random.uniform(0.7, 0.75))
        
        filtered_flight_data['revenue'] = filtered_flight_data['booking'] * filtered_flight_data['fare']
        
        ff = filtered_flight_data.groupby('TF')['wtp_dtd'].mean().reset_index()
        gg = filtered_flight_data.groupby('TF')['fare'].mean().reset_index()
        tf_wtp_dtd_fare = pd.merge(ff, gg, on='TF') 
        tf_wtp_dtd_fare['diff'] = tf_wtp_dtd_fare['fare'] - tf_wtp_dtd_fare['wtp_dtd']
        tf_wtp_dtd_fare['woy'] = np.round(tf_wtp_dtd_fare['diff'] * 0.8, 2)
        tf_wtp_dtd_fare['dow'] = np.round(tf_wtp_dtd_fare['diff'] * 0.2, 2)
        # WTP_WOY = load_data("WTP_WOY.csv")
        # filtered_flight_data = pd.merge(filtered_flight_data, WTP_WOY, left_on='woy_departure', right_on='WOY')
        # DOW_WTP={1: 40, 2: 20, 3: 20, 4: 20, 5: 45, 6: 70, 7: 50}
        # filtered_flight_data['DOW_WTP'] = filtered_flight_data['dow_departure'].map(DOW_WTP)
        # filtered_flight_data['final_wtp'] = filtered_flight_data['DOW_WTP'] + filtered_flight_data['wtp_dtd'] + filtered_flight_data['WOY_WTP']
        # filtered_flight_data['final_fare'] = filtered_flight_data['final_wtp'] + filtered_flight_data['bid_price']
        # # Apply the function to the DataFrame
        # filtered_flight_data['fare'] = filtered_flight_data.apply(add_values, axis=1)
   
        mock_data = load_data("wtp_mock_data.csv")
    if False:
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

    n_rows = 5  # Specify the number of rows to display
    # st.write(f"Simulated Flight Data (Showing {n_rows} rows):")
    # st.dataframe(filtered_flight_data)

    ################################################################
    average__seats_per_DCP = mock_data.groupby("DCP")["number_of_checkouts"].sum().mean()
    average__seats_per_DCP = filtered_flight_data.groupby("TF")["booking"].sum().mean()
    average__wtp_per_DCP = filtered_flight_data.groupby("TF")["WTP"].mean().mean()

    mock_data['date'] = pd.to_datetime(mock_data['date'])
    average_checkout_rate = mock_data[['date', 'checkout_rate']].set_index('date').resample('W').mean()

    revenue_generated = filtered_flight_data['revenue'].sum()

    mock_data['day_name'] = mock_data['date'].dt.day_name()
    weekday_wtp = mock_data.groupby('day_name')['WTP'].mean().reset_index()
    # ################################################################
    # col1, col2, col3, col4 = st.columns(4)
    # with col1:
    #     CHART_THEME = 'plotly_white' 

    #     indicators_ptf1 = go.Figure()
    #     indicators_ptf1.layout.template = CHART_THEME
    #     indicators_ptf1.add_trace(go.Indicator(
    #         mode = "number+delta",
    #         value = average__seats_per_DCP,
    #         number = {'suffix': ""},
    #         title = {"text": "<br><span style='font-size:1.5em;color:gray'>Seats Sold per DCP</span>"},
    #         delta = {'position': "bottom", 'reference': average__seats_per_DCP, 'relative': True},
    #         domain = {'row': 0, 'column': 0}))

    #     indicators_ptf1.update_layout(
    #         height=300,
    #         width=300
    #         )
    #     st.plotly_chart(indicators_ptf1)
    # with col2:    
    #     indicators_ptf2 = go.Figure()
    #     indicators_ptf2.add_trace(go.Indicator(
    #         mode = "number+delta",
    #         value = average__wtp_per_DCP,
    #         number = {'suffix': ""},
    #         title = {"text": "<span style='font-size:1.5em;color:gray'>Average WTP per DCP</span>"},
    #         delta = {'position': "bottom", 'reference': average__wtp_per_DCP, 'relative': False},
    #         domain = {'row': 0, 'column': 1}))
        
    #     indicators_ptf2.update_layout(
    #         height=300,
    #         width=300
    #         )
    #     st.plotly_chart(indicators_ptf2)
    # with col3:    
    #     indicators_ptf3 = go.Figure()
    #     indicators_ptf3.add_trace(go.Indicator(
    #         mode = "number+delta",
    #         value = np.round(average_checkout_rate['checkout_rate'][-1],2),
    #         number = {'suffix': " %"},
    #         title = {"text": "<span style='font-size:1.5em;color:gray'>Check-out Rate</span>"},
    #         delta = {'position': "bottom", 'reference': average_checkout_rate['checkout_rate'][-2], 'relative': False},
    #         domain = {'row': 0, 'column': 2}))
    #     indicators_ptf3.update_layout(
    #         height=300,
    #         width=300
    #         )
    #     st.plotly_chart(indicators_ptf3)
    # with col4:    
    #     indicators_ptf4 = go.Figure()
    #     indicators_ptf4.add_trace(go.Indicator(
    #         mode = "number+delta",
    #         value = revenue_generated,
    #         number = {'suffix': ""},
    #         title = {"text": "<span style='font-size:1.5em;color:gray'>Revenue $</span>"},
    #         delta = {'position': "bottom", 'reference': revenue_generated, 'relative': False},
    #         domain = {'row': 0, 'column': 3}))
    #     indicators_ptf4.update_layout(
    #         height=300,
    #         width=300
    #         )
    #     st.plotly_chart(indicators_ptf4)

    # col1, col2 = st.columns(2)
    # with col1:
    plot_cumulative_booking_and_fare(filtered_flight_data['simulation_day'], filtered_flight_data['booking'], filtered_flight_data['fare'])

    # with col2:
    #     create_stacked_bar_chart(tf_wtp_dtd_fare)

if __name__ == '__main__':
    main()
