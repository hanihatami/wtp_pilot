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

def get_top_events_for_april_sydney():
    # Static list of top 5 events with their importance scores and dates
    events = [
        {"date": "2024-04-01", "name": "Sydney Royal Easter Show", "importance": 95},
        {"date": "2024-04-15", "name": "The Sydney Comedy Festival", "importance": 90},
        {"date": "2024-04-25", "name": "ANZAC Day Commemorations", "importance": 85},
        {"date": "2024-04-12", "name": "Australian Fashion Week", "importance": 80},
        {"date": "2024-04-27", "name": "Vivid Sydney", "importance": 75},
    ]
    events_df = pd.DataFrame(events)
    return events_df


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

    # Get the top events data
    events_df = get_top_events_for_april_sydney()

    # Style settings for consistent appearance
    style_settings = """
        <style>
            body {
                font-family: Arial, Helvetica, sans-serif;
                background-color: #f4f7fa;
            }
            #calendar, .events-table {
                margin: 0 auto;
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
            .fc-day-top {
                color: #000;
            }
            .fc-day, .fc-day-top {
                background-color: transparent;
            }
            .fc-day-grid-event .fc-content {
                padding: 4px;
            }
            .events-table {
                width: 100%;
                border-collapse: collapse;
            }
            .events-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            .events-table th, .events-table td {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 20px; /* Increased padding for larger cells */
            }
            .events-table th {
                background-color: #f2f2f2;
                font-size: 18px; /* Larger font size for headers */
            }
            .events-table tr:nth-child(even) td {
                background-color: #f9f9f9;
            }
            /* Set a minimum height for each row to ensure they take up more vertical space. */
            .events-table tr {
                min-height: 50px; /* Adjust the height as needed */
            }
                </style>
        """
    # Using columns to place the calendar and the events side by side
    col1, col2 = st.columns([3, 2.5])  # Adjust the ratio as per your layout needs
    with col1:
        # Enhanced HTML, CSS, and JS for the calendar
        calendar_html = f"""
            <head>
                {style_settings}
                <link href='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/core/main.min.css' rel='stylesheet' />
                <link href='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/daygrid/main.min.css' rel='stylesheet' />
            </head>
            <body>
                <div id='calendar'></div>
                <script src='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/core/main.min.js'></script>
                <script src='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/interaction/main.min.js'></script>
                <script src='https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/4.2.0/daygrid/main.min.js'></script>
                <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    var calendarEl = document.getElementById('calendar');
                    var calendar = new FullCalendar.Calendar(calendarEl, {{
                        plugins: ['interaction', 'dayGrid'],
                        defaultDate: '2024-04-01',
                        header: {{
                            left: '',
                            center: 'title',
                            right: ''
                        }},
                        fixedWeekCount: false,
                        validRange: {{
                            start: '2024-03-31',
                            end: '2024-05-06'
                        }},
                        dateClick: function(info) {{
                            alert('Clicked on: ' + info.dateStr);
                        }},
                        dayRender: function(info) {{
                            var cell = info.el;
                            var randomColor = Math.random() < 0.5 ? '#ffcccc' : '#ccffcc';
                            cell.style.backgroundColor = randomColor;
                        }}
                    }});
                    calendar.render();
                }});
                </script>
            </body>
            """

        # Use components.html to embed the calendar HTML in the Streamlit app
        components.html(calendar_html, height=600)
    
    with col2:
        # Call the function to get the events data
        events_df = get_top_events_for_april_sydney()
        
        # Generate the events HTML table with dates
        events_html = f"""
            <head>
                {style_settings}
            </head>
            <body>
                <h2 style='text-align: center;'>Top Events in {arrival}</h2>
                <table class='events-table'>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Event</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
            """
        for event in events_df.to_dict(orient='records'):
            events_html += f"""
                <tr>
                    <td>{event['date']}</td>
                    <td>{event['name']}</td>
                    <td>{event['importance']}</td>
                </tr>
            """
        
        events_html += """
                </tbody>
            </table>
        </body>
        """

        # Embed the events HTML into the Streamlit app
        components.html(events_html, height=600)  # Adjust height as needed



if __name__ == "__main__":
    main()
