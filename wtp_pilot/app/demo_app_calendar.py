import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import matplotlib.pyplot as plt
from pathlib import Path
import datetime as dt
import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import calendar
from plotly.subplots import make_subplots


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


    # Enhanced HTML, CSS, and JS for the calendar
    calendar_html = """
    <head>
        <link href='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/core/main.min.css' rel='stylesheet' />
        <link href='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/daygrid/main.min.css' rel='stylesheet' />
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, Helvetica, sans-serif;
            background-color: #f4f7fa; /* Adjust the background color as needed */
        }
        #calendar {
            max-width: 700px; /* Adjust the width as needed */
            margin: 40px auto;
        }
        .fc-day-grid-event {
            cursor: pointer;
        }
        .fc-highlight {
            background: #bce8f1;
        }
        .fc-day:hover {
            background-color: #f5f5f5;
        }
        .fc-today {
            background-color: #d4edda !important;
            border-color: #c3e6cb !important;
        }
        /* Add custom styles for the calendar cells */
        .fc .fc-day-top {
            color: #000; /* Color of the day numbers */
        }
        .fc .fc-day, .fc .fc-day-top {
            background-color: transparent; /* Remove default background to allow custom colors */
        }
        .fc-day-grid-event .fc-content {
            padding: 4px; /* Adjust padding for events */
        }
    </style>
    </head>
    <body>
        <div id='calendar'></div>
        <script src='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/core/main.min.js'></script>
        <script src='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/interaction/main.min.js'></script>
        <script src='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/daygrid/main.min.js'></script>
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var calendarEl = document.getElementById('calendar');
            var calendar = new FullCalendar.Calendar(calendarEl, {
                plugins: ['interaction', 'dayGrid'],
                defaultDate: '2024-04-01',
                header: {
                    left: '',
                    center: 'title',
                    right: ''
                },
                fixedWeekCount: false,
                validRange: {
                    start: '2024-03-31',
                    end: '2024-05-06'
                },
                dateClick: function(info) {
                    alert('Clicked on: ' + info.dateStr);
                },
                dayRender: function(info) {
                    var cell = info.el;
                    var randomColor = Math.random() < 0.5 ? '#ffcccc' : '#ccffcc';
                    cell.style.backgroundColor = randomColor;
                }
            });
            calendar.render();
        });
        </script>
    </body>
    """

    # Use components.html to embed the calendar HTML in the Streamlit app
    components.html(calendar_html, height=800)




if __name__ == "__main__":
    main()
