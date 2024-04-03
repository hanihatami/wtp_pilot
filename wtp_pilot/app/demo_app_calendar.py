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
import random

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

def get_top_events_for_april_sydney():
    # Static list of top 5 events with their importance scores and dates
    events = [
        # {"date": "2024-04-01", "name": "Sydney Royal Easter Show", "importance": 95},
        # {"date": "2024-04-15", "name": "The Sydney Comedy Festival", "importance": 90},
        # {"date": "2024-04-25", "name": "ANZAC Day Commemorations", "importance": 85},
        # {"date": "2024-04-12", "name": "Australian Fashion Week", "importance": 80},
        # {"date": "2024-04-27", "name": "Vivid Sydney", "importance": 75}
        {"date": "2024-06-05", "name": "Sydney Film Festival", "importance": 95},
        {"date": "2024-06-12", "name": "Good Food & Wine Show Sydney", "importance": 90},
        {"date": "2024-06-19", "name": "Sydney Winter Festival", "importance": 85},
        {"date": "2024-06-26", "name": "State of Origin: Rugby Match", "importance": 80},
        {"date": "2024-06-30", "name": "Sydney Harbour 10K & 5K", "importance": 75},
    ]

    events_df = pd.DataFrame(events)
    return events_df

def generate_price_changes(bid_price, recommended_fare, n, increment=25):
    """
    Generate a list of price changes starting with the bid price and ending with the recommended fare.
    The function will generate 'n' meaningful intermediate changes that are multiples of the increment
    and include both positive and negative values.
    
    :param bid_price: Initial bid price as an integer or float
    :param recommended_fare: Recommended fare as an integer or float
    :param n: Number of intermediate steps to generate
    :param increment: The minimum absolute value for intermediate steps
    :return: List of strings representing the price changes
    """

    max_change = recommended_fare // 5  # 1/5th of recommended price as the maximum change
    price_changes_with_dollar_sign = [f"${bid_price}"]
    price_changes = [f"{bid_price}"]
    remaining_change = recommended_fare - bid_price
    
    # Adjust the max_change if it's too large compared to the remaining change
    if abs(max_change) > abs(remaining_change):
        max_change = remaining_change

    # Generate 'n' intermediate changes as multiples of the increment
    for i in range(n):
        # If we're on the last step, the change must bring us to the recommended fare
        if i == n - 1:
            change = remaining_change
        else:
            # Generate a list of possible changes, ensuring at least two possibilities
            # and not exceeding max_change
            min_change = -min(abs(max_change), abs(remaining_change))
            max_possible_change = min(abs(max_change), abs(remaining_change))
            possible_changes = list(range(min_change, max_possible_change+1, increment))
            possible_changes = [x for x in possible_changes if x != 0]  # Remove zero from possible changes

            # Choose a random change
            change = random.choice(possible_changes)

        # Apply the change and update the remaining change
        remaining_change -= change
        sign = '+' if change > 0 else ''
        price_changes_with_dollar_sign.append(f"{sign}${change}")
        price_changes.append(f"{sign}{change}")
    # Add the recommended fare as the final value
    price_changes_with_dollar_sign.append(f"${recommended_fare}")
    price_changes.append(f"{recommended_fare}")

    price_changes = [int(i) for i in price_changes]
    return price_changes_with_dollar_sign, price_changes

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
            /* Assuming 'min-price-comparison-table' is the class of your table */
            .min-price-comparison-table {
                width: 100%; /* Adjust the width as needed */
                table-layout: fixed; /* This makes your columns have fixed width */
                border-collapse: collapse;
            }

            .min-price-comparison-table th, 
            .min-price-comparison-table td {
                text-align: center;
                border: 1px solid black; /* for visibility */
            }

            /* Assuming 'all-flights-col' is the class for the first column cells with the logos */
            .min-price-comparison-table .all-flights-col {
                width: 20%; /* Adjust the width as needed */
            }

            /* Assuming 'flight-info-col' is the class for the rest of the columns */
            .min-price-comparison-table .flight-info-col {
                width: 10%; /* Adjust the width as needed */
            }
                </style>
        """
    # Using columns to place the calendar and the events side by side
    col1, col2 = st.columns([3, 3])  # Adjust the ratio as per your layout needs
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
                        defaultDate: '2024-06-01',
                        header: {{
                            left: '',
                            center: 'title',
                            right: ''
                        }},
                        fixedWeekCount: false,
                        validRange: {{
                            start: '2024-06-01',
                            end: '2024-07-01'
                        }},
                        dateClick: function(info) {{
                            Streamlit.setSessionState('clicked_date', info.dateStr);
                        }},
                        dayRender: function(info) {{
                            var cell = info.el;
                            var randomColor = Math.random() < 0.5 ? '#F2D7D5' : '#A9DFBF';
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

    # Sidebar date selection
    min_date = dt.date(2024, 6, 1)  # Start of June 2024
    max_date = dt.date(2024, 6, 30)  # End of June 2024
    default_date = min_date  # Default to the start of the month
    
    flight_date = st.sidebar.date_input(
        "Select a Date",
        value=default_date,
        min_value=min_date,
        max_value=max_date,
    )
    # Convert the departure date to a seed by taking the total number of days since a fixed date
    fixed_date = dt.datetime.strptime("2000-01-01", "%Y-%m-%d").date()
    seed = (flight_date - fixed_date).days
    random.seed(seed)  # Seed the random number generator
    carrier_mapping = {
    'JQ': 'Jetstar',
    'LA': 'Latam',
    'NZ': 'Air New Zealand',
    'QF': 'Qantas',
    'TN': 'Air Tahiti Nui',
    'FJ': 'Fiji Airways',
    'MU': 'China Eastern',
    'NF': 'Air Vanuatu',
    'SB': 'Aircalin'
    }

    # logo_mapping = {carrier : Path(get_project_root()) / f"wtp_pilot/references/carrier_logos/{carrier}-logo.png" for carrier in carrier_mapping.values()}
    logo_mapping = {carrier : f'https://raw.githubusercontent.com/hanihatami/wtp_pilot/master/wtp_pilot/references/carrier_logos/{carrier}-logo.png' for carrier  in carrier_mapping.values()}

    if True:
        with st.spinner('Fetching flight information...'):
            try:
                flights_info = cached_get_flights_info(amadeus, departure, arrival, flight_date, day_range=0)
                segments, fares, flights, prices = parse_flight_details(flights_info)
                NZ_nonStop_flights, non_NZ_flights, nonStop_nonNz_flights_carrier_codes = filter_and_merge_flights(segments, flights, fares)
                NZ_flights_for_DepartureDay = filter_flights_by_departure_date(NZ_nonStop_flights, flight_date)

                flights_with_one_stops = flights[flights['NumberOfStops'] == 1]
                flights_with_no_stops = flights[flights['NumberOfStops'] == 0]
                flights_with_one_stops_with_price = pd.merge(flights_with_one_stops, prices, on= 'ItineraryID')
                flights_with_no_stops_with_price = pd.merge(flights_with_no_stops, prices, on= 'ItineraryID')
                flights_with_one_stops_with_price_with_carrier_codes = pd.merge(flights_with_one_stops_with_price, segments[['ItineraryID', 'FlightID', 'CarrierCode']], on= 'ItineraryID')
                flights_with_no_stops_with_price_with_carrier_codes = pd.merge(flights_with_no_stops_with_price, segments[['ItineraryID', 'FlightID', 'CarrierCode']], on= 'ItineraryID')
                market_df = create_min_price_comparison_table(flights_with_no_stops_with_price_with_carrier_codes, 
                                                  flights_with_one_stops_with_price_with_carrier_codes,
                                                  carrier_mapping,
                                                  logo_mapping)
                # html_table_with_classes = add_classes_to_table_html(market_html)
                # col1, col2, col3 = st.columns([1,4,1])  # Adjust the ratio as needed
                # with col2:
                #     components.html(html_table_with_classes, height=300, width=2000)
                
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
            bid_calculator = BidCalculator((100, 250), 'ECONOMY', flight_date, demand_rate_per_tf, 1)
            optimal_bid_prices = bid_calculator.calculate_bid_price(seats=target_flight['Capacity'], time=days_to_departure + 1)



    # Extract unique carrier codes
    unique_carrier_codes = nonStop_nonNz_flights_carrier_codes['CarrierCode'].unique().tolist()

    # Create the multiselect widget in the sidebar
    selected_carriers = st.sidebar.multiselect(
        'Choose carrier codes:',
        options=unique_carrier_codes,
        default=unique_carrier_codes  # Optionally set a default value
    )
    if selected_carriers:
        # Filter the DataFrame based on selected carrier codes
        filtered_df = nonStop_nonNz_flights_carrier_codes[nonStop_nonNz_flights_carrier_codes['CarrierCode'].isin(selected_carriers)]
    ####
    filtered_df_with_prices = pd.merge(filtered_df, prices, on= 'ItineraryID')

    non_stops_flights = market_df[market_df['NonStopMinPrice'] != '--']
    one_stop_flights = market_df[market_df['OneStopMinPrice'] != '--']
    
    # Sample data
    # airlines = ["Air NZ", 'Competitors (Non-Stop)', 'Competitors (With Stops)', 'Selected Competitors']
    non_stops_airlines = list(non_stops_flights['CarrierCode'].values)
    one_stop_airlines = list(one_stop_flights['CarrierCode'].values)

    # target_flight_price = target_flight_price.values[0]
    competition_prices_per_type = top_similar_flights_with_price.groupby('IsNonStop')['Total'].mean()
    competition_prices_non_stop = competition_prices_per_type[True]
    # competition_prices_with_stop = competition_prices_per_type[False]
    # selected_competition_prices = filtered_df_with_prices['Total'].mean()
    # prices = [target_flight_price, competition_prices_non_stop, competition_prices_with_stop, selected_competition_prices]
    non_stops_price_labels = list(non_stops_flights['NonStopMinPrice'].values)
    one_stop_price_labels = list(one_stop_flights['OneStopMinPrice'].values)
    # Define your color palette
    colors = ['#517fa4', '#62975c', '#8a5fa2', '#e3a448']  # Muted shades of blue, green, purple, and orange
    colors = ['#A9CCE3', '#A9DFBF', '#D7BDE2', '#F9E79F']  # Light blue, light green, light purple, light yellow
    # colors = ['#FAD7A0', '#E59866', '#D2B4DE', '#AED6F1']  # Peach, orange, lavender, light blue
    # colors = ['#E8DAEF', '#D5F5E3', '#D4E6F1', '#FCF3CF']  # Lilac, mint, baby blue, pale yellow
    # colors = ['#E6B0AA', '#F5CBA7', '#A3E4D7', '#FDEBD0']  # Dusty pink, apricot, teal, cream
    colors = ['#F2D7D5', '#D7DBDD', '#A9DFBF', '#AED6F1', '#F9E79F', '#A9CCE3']  # Soft pink, grey blue, seafoam, cornflower blue
    # Convert prices to string with dollar sign for display
    # price_labels = ['$' + '{:.2f}'.format(price) for price in prices]
    non_stops_prices = [float(price.strip('NZ$')) for price in non_stops_price_labels]
    one_stop_prices = [float(price.strip('NZ$')) for price in one_stop_price_labels]

    non_stop_logo_urls = list(non_stops_flights['Logo'].values)
    one_stop_logo_urls = list(one_stop_flights['Logo'].values)

    # Pair each airline with its corresponding price and sort by price
    paired_sorted_nonstops = sorted(zip(non_stops_prices, non_stops_price_labels, non_stops_airlines, non_stop_logo_urls))
    paired_sorted_onestop = sorted(zip(one_stop_prices, one_stop_price_labels, one_stop_airlines, one_stop_logo_urls))

    # Unzip the pairs to get sorted prices and corresponding airlines
    sorted_nonstops_prices, sorted_nonstops_price_lables, sorted_nonstops_airlines, sorted_nonstops_logo_urls  = zip(*paired_sorted_nonstops)
    sorted_onestop_prices, sorted_onestop_price_lables, sorted_onestop_airlines, sorted_onestop_logo_urls = zip(*paired_sorted_onestop)

    # Convert the tuples back to lists
    non_stops_prices = list(sorted_nonstops_prices)[:5]
    non_stops_price_labels = list(sorted_nonstops_price_lables)[:5]
    non_stops_airlines = list(sorted_nonstops_airlines)[:5]
    non_stop_logo_urls = list(sorted_nonstops_logo_urls)[:5]

    one_stop_prices = list(sorted_onestop_prices)[:5]
    one_stop_price_labels = list(sorted_onestop_price_lables)[:5]
    one_stop_airlines = list(sorted_onestop_airlines)[:5]
    one_stop_logo_urls = list(sorted_onestop_logo_urls)[:5]

    # Create the bar chart
    fig_non_stops = go.Figure([go.Bar(x=non_stops_airlines, y=non_stops_prices, text=non_stops_price_labels, textposition='auto', marker_color=colors)])
    ################################

    # # Convert prices to string with dollar sign for display
    # price_labels = ['$' + '{:.2f}'.format(price) for price in prices]

    # # Create the bar chart
    # fig = go.Figure([go.Bar(x=airlines, y=prices, text=price_labels, textposition='auto', marker_color=colors)])

    # # Annotations for the logos, assuming you have the URLs or paths to the logo images
    # logo_urls = [
    #     'https://raw.githubusercontent.com/hanihatami/wtp_pilot/master/wtp_pilot/references/Air%20New%20Zealand-logo.png',
    #     'https://raw.githubusercontent.com/hanihatami/wtp_pilot/master/wtp_pilot/references/Air%20New%20Zealand-logo.png',
    #     'https://raw.githubusercontent.com/hanihatami/wtp_pilot/master/wtp_pilot/references/Air%20New%20Zealand-logo.png',
    #     'https://raw.githubusercontent.com/hanihatami/wtp_pilot/master/wtp_pilot/references/Air%20New%20Zealand-logo.png',
    #     'https://raw.githubusercontent.com/hanihatami/wtp_pilot/master/wtp_pilot/references/Air%20New%20Zealand-logo.png'
    # ]
    
    
    # st.text(logo_urls[0])
    # non_stop_logo_urls = logo_urls

    # Calculate positions for the logos. This might require some tweaking.
    y_positions_non_stops = [price / 4 for price in non_stops_prices]  # Adjust the offset as necessary

    # Add logos as annotations
    for i, airline in enumerate(non_stops_airlines):
        fig_non_stops.add_layout_image(
            dict(
                source=non_stop_logo_urls[i],
                x=airline,
                y=y_positions_non_stops[i],
                xref="x",
                yref="y",
                sizex=0.2,
                sizey=max(non_stops_prices) * 0.1,  # Adjust size relative to your y-axis scale
                xanchor="center",
                yanchor="middle"
            )
        )


    # Create a bar chart for one-stop flights
    fig_one_stops = go.Figure(
        [go.Bar(
            x=one_stop_airlines,
            y=one_stop_prices,
            text=one_stop_price_labels,
            textposition='auto',
            marker_color=colors  # Make sure you have enough colors
        )]
    )
    
    y_positions_one_stop = [price / 4 for price in one_stop_prices]  # Adjust as necessary

    for i, airline in enumerate(one_stop_airlines):
        fig_one_stops.add_layout_image(
            dict(
                source=one_stop_logo_urls[i],  # Make sure you don't go out of bounds
                x=airline,
                y=y_positions_one_stop[i],
                xref="x",
                yref="y",
                sizex=0.2,
                sizey=max(one_stop_prices) * 0.1,  # Adjust size relative to your y-axis scale
                xanchor="center",
                yanchor="middle"
            )
        )



    # The font used throughout your app
    font_family = "Arial, Helvetica, sans-serif"
    fig_non_stops.update_layout(
        title='Market Price Positioning',
        title_font=dict(family=font_family, size=22, color='black'),  # Match title style
        xaxis=dict(
            title='Nonstops',
            title_font=dict(family=font_family, size=18, color='black'),  # Match axis title style
            tickfont=dict(family=font_family, size=14, color='black')  # Match axis tick labels
        ),
        yaxis=dict(showticklabels=False, showgrid=False
        ),
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        plot_bgcolor='rgba(240, 240, 240, 0.8)',  # Light grey background, adjust opacity as needed
        barmode='group',
        height=600, width=800,
        margin=dict(l=100, r=100, t=100, b=100)
        )

    # Set font for the bar labels, if you have them
    fig_non_stops.update_traces(textfont=dict(family=font_family, size=16, color='black'))

    fig_one_stops.update_layout(
        title='',
        title_font=dict(family=font_family, size=22, color='black'),  # Match title style
        xaxis=dict(
            title='1 stop',
            title_font=dict(family=font_family, size=18, color='black'),  # Match axis title style
            tickfont=dict(family=font_family, size=14, color='black')  # Match axis tick labels
        ),
        yaxis=dict(showticklabels=False, showgrid=False
        ),
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        plot_bgcolor='rgba(240, 240, 240, 0.8)',  # Light grey background, adjust opacity as needed
        barmode='group',
        height=600, width=800,
        margin=dict(l=100, r=100, t=100, b=100)
        )

    # Set font for the bar labels, if you have them
    fig_one_stops.update_traces(textfont=dict(family=font_family, size=16, color='black'))
    

    plot_bgcolor = 'rgba(0,0,0,0)'  # This sets the background transparent
    paper_bgcolor = 'rgba(240, 240, 240, 0.8)'  # Streamlit's default grey background

    # # Display the figure in the Streamlit app
    # col1, col2, col3, col4 = st.columns([0.1,3,3,0.1])  # Adjust the ratio as needed
    # with col2:
    #     st.plotly_chart(fig_non_stops)
    #     st.plotly_chart(fig_one_stops)
    # Use st.columns to create two columns
    col1, col2 = st.columns(2)  # Creates two columns with equal width by default

    # Display non-stop flights bar chart in the first column
    with col1:
        st.plotly_chart(fig_non_stops)

    # Display one-stop flights bar chart in the second column
    with col2:
        st.plotly_chart(fig_one_stops)
    # Add a horizontal line
    st.markdown("---")
    # spacer, col1, col2, col3, col4, spacer = st.columns([0.5, 10, 10, 10, 10, 1])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        available_seats_figure = go.Figure()
        available_seats_figure.add_trace(go.Indicator(
            mode="number",
            value=available_seats,
            number={'suffix': ""},
            title={"text": "<span style='font-size:1.5em;color:gray'>Available Seats</span>"} # Set overall figure background color
        ))
        available_seats_figure.update_layout(height=300, width=300,
                                             plot_bgcolor=plot_bgcolor, 
                                             paper_bgcolor=paper_bgcolor)
        st.plotly_chart(available_seats_figure)

    with col2:
        load_factor_figure = go.Figure()
        load_factor_figure.add_trace(go.Indicator(
            mode="number",
            value=int((target_flight['Capacity'] - available_seats)/target_flight['Capacity'] * 100),
            number={'suffix': "%"},
            title={"text": "<span style='font-size:1.5em;color:gray'>Load Factor</span>"}
        ))
        load_factor_figure.update_layout(height=300, width=300,
                                         plot_bgcolor=plot_bgcolor, 
                                         paper_bgcolor=paper_bgcolor)
        st.plotly_chart(load_factor_figure)

    with col3:
        dtd_figure = go.Figure()
        dtd_figure.add_trace(go.Indicator(
            mode="number",
            value=days_to_departure,
            number={'suffix': ""},
            title={"text": "<span style='font-size:1.5em;color:gray'>Days to Departure</span>"}
        ))
        dtd_figure.update_layout(height=300, width=300,
                                 plot_bgcolor=plot_bgcolor, 
                                 paper_bgcolor=paper_bgcolor)
        st.plotly_chart(dtd_figure)

    bid_price = max(100, int(optimal_bid_prices[(available_seats, days_to_departure)]))
    with col4:
        bid_price_figure = go.Figure()
        bid_price_figure.add_trace(go.Indicator(
            mode="number+delta",
            value=bid_price,
            delta={'reference': int(optimal_bid_prices[(available_seats+1, days_to_departure+1)]), 'valueformat': ".2f"},
            number={'prefix': "$"},
            title={"text": "<span style='font-size:1.5em;color:gray'>Bid Price</span>"}
        ))
        bid_price_figure.update_layout(height=300, width=300,
                                       plot_bgcolor=plot_bgcolor, 
                                       paper_bgcolor=paper_bgcolor)
        st.plotly_chart(bid_price_figure)
        ##################################################################
    n=4
    # if bid price is more than 200 then recommended price is up to 80 euros more than competitor non_stop
    # if bid price is less than 200 then recommended price is between -20 to +20 of the minimum selected competitors
    # if bid_price >= 200:
    #     recommended_price = competition_prices_non_stop 
    # elif bid_price <= 200 and bid_price >= 150:
    #     recommended_price = 
    # else:
    #     recommended_price = filtered_df_with_prices['Total'].min() 

    # Assuming competition_prices_non_stop and filtered_df_with_prices are already defined
    max_bid_price = 250
    if bid_price > 200:
        # Proportionally increase the price by a value between 50 to 100 based on the difference from 200
        proportion = (bid_price - 200) / (max_bid_price - 200)  # max_bid_price is the maximum bid price observed or a set limit
        increase = proportion * (100 - 50) + 50  # Scale the proportion by the range (100 - 50) and add the minimum (50)
        recommended_price = int(competition_prices_non_stop + increase)
    elif bid_price < 150:
        # Adjust the price by a value between -20 to +20 of the minimum selected competitors prices
        adjustment = random.uniform(-20, 20)
        recommended_price = int(filtered_df_with_prices['Total'].min() + adjustment)
    else:
        # Proportionally increase the price by a value between 30 to 50 based on the difference from 200
        proportion = (bid_price - 150) / (200 - 150)  # This is assuming bid_price is less than 150
        increase = proportion * (50 - 30) + 30  # Scale the proportion by the range (50 - 30) and add the minimum (30)
        recommended_price = int(competition_prices_non_stop + increase)

    txt, vals_y= generate_price_changes(bid_price, recommended_price, n, increment=25)
    # txt = ['$500', '$-2', '$-28', '$-56', '$-39', '$375']
    # vals_y = [500, 100, -50, 25, -200, 375]
    key_drivers =  ["WOY", "DOW", "DTD", "SEARCH" ]
    # chose n key driver
    # key_drivers_subset = random.sample(key_drivers, n)
    key_drivers_subset = key_drivers
    baseline = 0
   
    # Layout setup for columns
    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        # Creating the waterfall chart

        # Assuming these are the colors used in your app, adjust as necessary
        color_for_increasing = '#A9DFBF' # Greenish shade
        color_for_decreasing = '#F2D7D5'  # Reddish shade
        color_for_totals = '#D7DBDD'   # Grey shade
        font_family = "Arial, Helvetica, sans-serif"  # The font used in the rest of your app

        wtp_breakdown_figure = go.Figure(go.Waterfall(
            name="20", 
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["Bid Price"] + key_drivers_subset +  ["Recommended Fare"],
            textposition="outside",
            text=txt,
            y=vals_y,
            base=baseline,
            connector={"line":{"color":"rgb(63, 63, 63)"}},
            increasing=dict(marker=dict(color=color_for_increasing)),
            decreasing=dict(marker=dict(color=color_for_decreasing)),
            totals=dict(marker=dict(color=color_for_totals)),
        ))

        wtp_breakdown_figure.update_layout(
            title="WTP Breakdown",
            title_font=dict(family=font_family, size=22, color='black'),
            font=dict(family=font_family, size=14, color='black'),
            waterfallgap=0.3,  # Adjust the gap between bars if needed
            # Set the rest of the layout properties as required
            height=600, width=800
        )
        # Apply consistent colors and font styles to the axis titles
        wtp_breakdown_figure.update_xaxes(title_font=dict(family=font_family, size=16, color='black'))
        wtp_breakdown_figure.update_yaxes(title_font=dict(family=font_family, size=16, color='black'))

        # Displaying the chart in Streamlit
        st.plotly_chart(wtp_breakdown_figure)

            
                # display_price_distribution_v2(top_similar_flights_with_price, target_flight_price)
if __name__ == "__main__":
    main()
