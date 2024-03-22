import datetime as dt
from datetime import datetime, timedelta
from amadeus import ResponseError
import pandas as pd
import re

def get_flights_info(client, departure_city, arrival_city, date, day_range=0):
    flights_info = []  # List to store flights data from all dates
    start_date = date - timedelta(days=day_range)
    end_date = date + timedelta(days=day_range)
    current_date = start_date
    while current_date <= end_date:
        try:
            response = client.shopping.flight_offers_search.get(
                originLocationCode=departure_city,
                destinationLocationCode=arrival_city,
                departureDate=current_date.strftime('%Y-%m-%d'),
                adults=1)
            flights_info.extend(response.data)  # Add the results to the list
        except ResponseError as error:
            print(error)
        current_date += timedelta(days=1)  # Move to the next date

    return flights_info


def filter_flights_by_departure_date(flights_df, departure_date):
    if isinstance(departure_date, str):
        departure_date = pd.to_datetime(departure_date).date()
    filtered_flights = flights_df[flights_df['DepartureDate'] == departure_date]
    
    return filtered_flights


def filter_flights_by_time_and_class(flights_df, departure_time=None, cabin=None):
    # Filter by departure time if specified
    if departure_time is not None:
        # If departure_time is a string, convert it to a time object for comparison
        if isinstance(departure_time, str):
            departure_time = pd.to_datetime(departure_time).time()
        filtered_flights = flights_df[flights_df['DepartureTime'] == departure_time]
    
    # Filter by cabin if specified
    if cabin is not None:
        filtered_flights = filtered_flights[filtered_flights['Cabin'] == cabin]
    
    return filtered_flights



def parse_duration(duration_str):
    """
    Parses a duration string in ISO 8601 format and returns the total duration in minutes.
    """
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?'
    match = re.match(pattern, duration_str)
    hours, minutes = match.groups(default='0')
    return int(hours) * 60 + int(minutes)

def is_overnight_flight(row):
    """
    Determine if a flight is an overnight flight.
    A flight is considered overnight if it arrives on the next day after it departs.
    """
    departure_hours = row['DepartureDateTime'].hour
    arrival_hours = row['ArrivalDateTime'].hour
    duration_hours = row['TotalDuration'] / 60
    overnight = arrival_hours < departure_hours and duration_hours > 1
    next_day_arrival = duration_hours > (24 - departure_hours + arrival_hours)
    return overnight or next_day_arrival

# Function to categorize departure time
def time_of_day(hour):
    if 0 <= hour < 6:
        return 'Early Morning'
    elif 6 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'
    
# Function to categorize flights as Short-haul, Medium-haul, or Long-haul
def categorize_flight_haul(duration):
    if duration <= 180: # Short-haul flights are less than or equal to 3 hours
        return 'Short-haul'
    elif duration <= 360: # Medium-haul flights are between 3 to 6 hours
        return 'Medium-haul'
    else: # Long-haul flights are more than 6 hours
        return 'Long-haul'
    
import pandas as pd

def parse_segment(segment, itinerary_id, flight_id):
    """
    Parse individual segment information.
    """
    aircraft_code = segment["aircraft"]["code"] if "aircraft" in segment else "Unknown"
    segment_duration_minutes = parse_duration(segment["duration"])
    return {
        "ItineraryID": itinerary_id,
        "FlightID": flight_id,
        "Duration": segment_duration_minutes,
        "Departure": segment["departure"]["iataCode"],
        "Arrival": segment["arrival"]["iataCode"],
        "CarrierCode": segment["carrierCode"],
        "DepartureDateTime": segment["departure"]["at"],
        "ArrivalDateTime": segment["arrival"]["at"],
        "NumberOfStops": segment["numberOfStops"],
        "AircraftCode": aircraft_code
    }

def parse_fares(offer, segment, itinerary_id, flight_id):
    """
    Extract fare details for each segment if available.
    """
    fares = []
    for traveler_pricing in offer["travelerPricings"]:
        for fare_detail in traveler_pricing["fareDetailsBySegment"]:
            if fare_detail["segmentId"] == segment["id"]:
                fares.append({
                    "ItineraryID": itinerary_id,
                    "FlightID": flight_id,
                    "Cabin": fare_detail["cabin"],
                    "Class": fare_detail["class"],
                    "FareBasis": fare_detail["fareBasis"],
                    "IncludedCheckedBagsQuantity": fare_detail.get("includedCheckedBags", {}).get("quantity", 0)
                })
    return fares

def parse_itinerary(itinerary, offer, itinerary_id):
    """
    Parse itinerary information and segment details.
    """
    segments_data, fares_data = [], []
    flight_id_counter = 1
    segments = itinerary["segments"]
    itinerary_duration = parse_duration(itinerary["duration"])

    for segment in segments:
        segments_data.append(parse_segment(segment, itinerary_id, flight_id_counter))
        fares_data.extend(parse_fares(offer, segment, itinerary_id, flight_id_counter))
        flight_id_counter += 1

    flight_info = {
        "ItineraryID": itinerary_id,
        "Departure": segments[0]["departure"]["iataCode"],
        "Arrival": segments[-1]["arrival"]["iataCode"],
        "DepartureDateTime": segments[0]["departure"]["at"],
        "ArrivalDateTime": segments[-1]["arrival"]["at"],
        "TotalDuration": itinerary_duration,
        "NumberOfStops": len(segments) - 1,
    }
    price_info = {
        "ItineraryID": itinerary_id,
        "Currency": offer["price"]["currency"],
        "Total": offer["price"]["total"],
        "Base": offer["price"]["base"],
    }
    return segments_data, fares_data, flight_info, price_info

def parse_flight_details(flight_data):
    """
    Parse flight details from the provided data.
    """
    segments_data, fares_data, flights_data, prices_data = [], [], [], []
    itinerary_id_counter = 1

    for offer in flight_data:
        for itinerary in offer["itineraries"]:
            segment_info, fare_info, flight_info, price_info = parse_itinerary(itinerary, offer, itinerary_id_counter)
            segments_data.extend(segment_info)
            fares_data.extend(fare_info)
            flights_data.append(flight_info)
            prices_data.append(price_info)
            itinerary_id_counter += 1

    # Convert lists to DataFrames and perform additional processing
    segments_df = pd.DataFrame(segments_data)
    fares_df = pd.DataFrame(fares_data)
    flights_df = pd.DataFrame(flights_data)
    prices_df = pd.DataFrame(prices_data)

    # Example of additional processing
    segments_df['DepartureDateTime'] = pd.to_datetime(segments_df['DepartureDateTime'])
    segments_df['ArrivalDateTime'] = pd.to_datetime(segments_df['ArrivalDateTime'])
    flights_df['DepartureDateTime'] = pd.to_datetime(flights_df['DepartureDateTime'])
    flights_df['ArrivalDateTime'] = pd.to_datetime(flights_df['ArrivalDateTime'])

    # Add any other transformations or calculations
    segments_df['DepartureDate'] = segments_df['DepartureDateTime'].dt.date
    segments_df['ArrivalDate'] = segments_df['ArrivalDateTime'].dt.date
    segments_df['DepartureTime'] = segments_df['DepartureDateTime'].dt.time
    segments_df['ArrivalTime'] = segments_df['ArrivalDateTime'].dt.time
    segments_df.rename(columns={'NumberOfStops': 'SegmentNumberOfStops'}, inplace=True)

    flights_df['DepartureDate'] = flights_df['DepartureDateTime'].dt.date
    flights_df['ArrivalDate'] = flights_df['ArrivalDateTime'].dt.date
    flights_df['DepartureTime'] = flights_df['DepartureDateTime'].dt.time
    flights_df['ArrivalTime'] = flights_df['ArrivalDateTime'].dt.time
    flights_df['Departure_TimeOfDay'] = flights_df['DepartureDateTime'].dt.hour.apply(time_of_day)
    flights_df['IsWeekend_Departure'] = flights_df['DepartureDateTime'].dt.dayofweek >= 5
    flights_df['FlightHaul'] = flights_df['TotalDuration'].apply(categorize_flight_haul)
    flights_df['IsNonStop'] = flights_df['NumberOfStops'] == 0
    flights_df['IsOverNightFlight'] = flights_df.apply(is_overnight_flight, axis=1)

    prices_df['Total'] = prices_df['Total'].astype(float)
    prices_df['Base'] = prices_df['Base'].astype(float)
    prices_df['FareCategory'] = pd.qcut(prices_df['Total'], q=3, labels=['Low', 'Medium', 'High'])
    prices_df['TotalZScore'] = (prices_df['Total'] - prices_df['Total'].mean()) / prices_df['Total'].std()

    fares_df['FlightsPerItinerary'] = fares_df.groupby('ItineraryID')['FlightID'].transform('count')

    return segments_df, fares_df, flights_df, prices_df


def filter_and_merge_flights(segments: pd.DataFrame, flights: pd.DataFrame, fares: pd.DataFrame):
    """
    Filters and merges flight data based on carrier code and number of stops.
    
    Parameters:
    - segments: DataFrame containing segment information including CarrierCode.
    - flights: DataFrame containing flight information including ItineraryID.
    - fares: DataFrame containing fare information.
    
    Returns:
    - NZ_nonStop_flights: DataFrame containing non-stop flights operated by NZ carrier.
    - non_NZ_flights: DataFrame containing flights not operated by NZ carrier, merged with fares.
    """
    # Filter segments by NZ carrier and merge with flights and fares
    NZ_carriers = segments[segments['CarrierCode'] == 'NZ']
    merged_flights = pd.merge(NZ_carriers, flights, on='ItineraryID', suffixes=('', '_drop'))
    merged_flights = pd.merge(merged_flights, fares, on=['ItineraryID', 'FlightID'], suffixes=('', '_drop'))
    NZ_flights = merged_flights.loc[:, ~merged_flights.columns.str.endswith('_drop')]

    # Filter for non-stop NZ flights
    NZ_nonStop_flights = NZ_flights.query("NumberOfStops == 0")

    # Find flights not operated by NZ carrier and merge with fares
    non_NZ_flights = flights[~flights['ItineraryID'].isin(NZ_flights['ItineraryID'])]
    non_NZ_flights = pd.merge(non_NZ_flights, fares, on=['ItineraryID'], suffixes=('', '_drop'))
    non_NZ_flights = non_NZ_flights.loc[:, ~non_NZ_flights.columns.str.endswith('_drop')]
    
    return NZ_nonStop_flights, non_NZ_flights

def FlightHaul_similarity(flight_haul1, flight_haul2):
    """
    Calculate similarity between two times of day, returning a score between 0 and 1.
    Closer times of day have higher scores.
    """
    # Define an ordered list of times of day for reference
    flight_hauls = ['Short-haul', 'Medium-haul', 'Long-haul']
    
    # Calculate the difference in indices between the two times
    diff = abs(flight_hauls.index(flight_haul1) - flight_hauls.index(flight_haul2))
    
    # Assign scores based on the difference
    if diff == 0:
        return 1  # Exact match
    elif diff == 1:
        return 0.75  # Adjacent 
    elif diff == 2:
        return 0.5  # One step removed
    else:
        return 0.25  # Furthest apart
    
def time_of_day_similarity(time1, time2):
    """
    Calculate similarity between two times of day, returning a score between 0 and 1.
    Closer times of day have higher scores.
    """
    # Define an ordered list of times of day for reference
    times_of_day = ['Early Morning', 'Morning', 'Afternoon', 'Evening', 'Night']
    
    # Calculate the difference in indices between the two times
    diff = abs(times_of_day.index(time1) - times_of_day.index(time2))
    
    # Assign scores based on the difference
    if diff == 0:
        return 1  # Exact match
    elif diff == 1:
        return 0.75  # Adjacent times of day
    elif diff == 2:
        return 0.5  # One step removed
    else:
        return 0.25  # Furthest apart (Morning vs. Night or vice versa)

def calculate_similarity_score(flight_a, flight_b):
    """
    Calculate a similarity score between two flights based on specified criteria.
    
    Parameters:
    - flight_a: The first flight (a Series or similar structure).
    - flight_b: The second flight (a Series or similar structure).
    
    Returns:
    - A similarity score (the higher, the more similar).
    """
    score = 0
    # Points for NumberOfStops match
    if flight_a['NumberOfStops'] == flight_b['NumberOfStops']:
        score += 2
    if flight_a['Cabin'] == flight_b['Cabin']:
        score += 2
    score += time_of_day_similarity(flight_a['Departure_TimeOfDay'], flight_b['Departure_TimeOfDay'])
    # Points for FlightHaul match 
    score += FlightHaul_similarity(flight_a['FlightHaul'], flight_b['FlightHaul'])
    # Add more sophisticated handling for FlightHaul if needed

    # Points for IsOverNightFlight match
    if flight_a['IsOverNightFlight'] == flight_b['IsOverNightFlight']:
        score += 0.5
    
    return score

def find_top_n_similar_flights(target_flight, all_flights, n=5):
    # Calculate similarity scores for all flights
    scores = all_flights.apply(lambda flight: calculate_similarity_score(target_flight, flight), axis=1)
    all_flights = all_flights.copy()
    # Add scores as a new column to the all_flights DataFrame
    all_flights['SimilarityScore'] = scores
    
    # Sort flights by similarity score in descending order
    sorted_flights = all_flights.sort_values('SimilarityScore', ascending=False)
    
    # Return the top N similar flights
    return sorted_flights.head(n)