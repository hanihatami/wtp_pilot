from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import tqdm
import time
import pandas as pd
from datetime import date, timedelta


def make_url(origin : str, dest : str, date_leave : str, date_return : str) -> str:
    base = 'https://www.google.com/travel/flights?q=Flights%20to%20{}%20from%20{}%20on%20{}%20through%20{}'
    return base.format(dest, origin, date_leave, date_return)

def get_info(res):
    info = []
    collect = False
    for r in res:

        # if 'more flights' in r:
        #     collect = False

        if collect and 'price' not in r.lower() and 'prices' not in r.lower() and 'other' not in r.lower() and ' – ' not in r.lower():
            info += [r]

        if r == 'Sort by:':
            collect = True
    return info

def end_condition(x):
    if len(x) < 2:
        return False

    if x[-2] == '+':
        x = x[:-2]
    
    if x[-2:] == 'AM' or x[-2:] == 'PM':
        return True
    return False

def partition_info(info):
    i=0
    grouped = []
    while i < len(info)-1:
        j = i+2
        end = -1
        while j < len(info):
            if end_condition(info[j]):
                end = j
                break
            j += 1 

        #print(i, end)
        if end == -1:
            break
        grouped += [info[i:end]]
        i = end
        
    return grouped
def parse_columns(grouped, date_leave, date_return):
    # Instantiate empty column arrays
    depart_time = []
    arrival_time = []
    airline = []
    travel_time = []
    origin = []
    dest = []
    stops = []
    stop_time = []
    stop_location = []
    co2_emission = []
    emission = []
    price = []
    trip_type = []
    access_date = [date.today().strftime('%Y-%m-%d')]*len(grouped)

    # For each "flight"
    for g in grouped:
        i_diff = 0 # int that checks if we need to jump ahead based on some conditions

        # Get departure and arrival times
        depart_time += [g[0]]
        arrival_time += [g[1]]

        # When this string shows up we jump ahead an index
        i_diff += 1 if 'Separate tickets booked together' in g[2] else 0

        # Add airline, travel time, origin, and dest
        airline += [g[2 + i_diff]]
        travel_time += [g[3 + i_diff]]
        origin += [g[4 + i_diff].split('–')[0]]
        dest += [g[4 + i_diff].split('–')[1]]
        
        # Grab the number of stops by splitting string
        num_stops = 0 if 'Nonstop' in g[5 + i_diff] else int(g[5 + i_diff].split('stop')[0])
        stops += [num_stops]

        # Add stop time/location given whether its nonstop flight or not
        stop_time += [None if num_stops == 0 else (g[6 + i_diff].split('min')[0] if num_stops == 1 else None)]
        stop_location += [None if num_stops == 0 else (g[6 + i_diff].split('min')[1] if num_stops == 1 and 'min' in g[6 + i_diff] else [g[6 + i_diff].split('hr')[1] if 'hr' in g[6 + i_diff] and num_stops == 1 else g[6 + i_diff]])]
        
        # Jump ahead an index if flight isn't nonstop to accomodate for stop_time, stop_location
        i_diff += 0 if num_stops == 0 else 1

        # If Co2 emission not listed then we skip, else we add
        if g[6 + i_diff] != '–':
            co2_emission += [float(g[6 + i_diff].replace(',','').split(' kg')[0])]
            emission += [0 if g[7 + i_diff] == 'Avg emissions' else int(g[7 + i_diff].split('%')[0])]

            price += [float(g[8 + i_diff][1:].replace(',',''))]
            trip_type += [g[9 + i_diff]]
        else:
            co2_emission += [None]
            emission += [None]
            price += [float(g[7 + i_diff][1:].replace(',',''))]
            trip_type += [g[8 + i_diff]]

       
    
    return {
        'Leave Date' : [date_leave]*len(grouped),
        'Return Date' : [date_return]*len(grouped),
        'Depart Time (Leg 1)' : depart_time,
        'Arrival Time (Leg 1)' : arrival_time,
        'Airline(s)' : airline,
        'Travel Time' : travel_time,
        'Origin' : origin,
        'Destination' : dest,
        'Num Stops' : stops,
        'Layover Time' : stop_time,
        'Stop Location' : stop_location,
        'CO2 Emission' : co2_emission,
        'Emission Avg Diff (%)' : emission,
        'Price ($)' : price,
        'Trip Type' : trip_type,
        'Access Date' : access_date
    }
def get_results(url, origin, dest, date_leave, date_return):
    '''
        Return results for single url
    '''
    if isinstance(url, str) and isinstance(date_leave, str) and isinstance(date_return, str):

    
        # Make URL request
        # results, price_history = make_url_request(url = url)
        results = make_url_request(url = url)

        # Data cleaning
        flight_info = get_info(results) # First, get relevant results
        partition = partition_info(flight_info) # Partition list into "flights"

        return parse_columns(partition, date_leave, date_return)# , price_history # "Transpose" to data frame

def get_flight_elements(d) -> list:
    return d.find_element(by = By.XPATH, value = '//body[@id = "yDmH0d"]').text.split('\n')

def find_flight_history_price(d):
    # labels = d.find_elements(By.TAG_NAME, 'g')
    WebDriverWait(d, timeout = 15).until(EC.presence_of_element_located((By.XPATH, "//*[name()='path' and contains(@class,'yLHjwb-ppH')]")))
    labels = d.find_elements(By.TAG_NAME, 'g')
    texts = [l.get_attribute("aria-label") for l in labels if l.get_attribute("aria-label") is not None]
    return texts

def convert_to_price_history_dataframe(prices):
    tday = date.today()
    df = pd.DataFrame([l.split(' - ') for l in prices], columns=['days ago', 'price $'])
    df['days ago'] = df['days ago'].str.extract('(\d+)').fillna(0)
    df["days ago"] = df["days ago"].apply(lambda x: tday-timedelta(days=int(x)))
    df['price $'] = df['price $'].str.extract('(\d+)').fillna(0)
    return df

def make_url_request(url):
    if isinstance(url, str):
        # Instantiate driver and get raw data
         # seconds
        # Set path to chromedriver executable
        chrome_options = Options()
        chrome_options.add_argument('chromedriver_mac64/chromedriver')

        # Instantiate the Chrome driver with options
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        driver.maximize_window()
        driver.get(url)
        currency = driver.find_element(By.XPATH,"//span[normalize-space()='Currency']")
        currency.click()
        usd = driver.find_element(By.XPATH,"//span[normalize-space()='US Dollar']")
        usd.click()
        ok_button = driver.find_element(By.XPATH,"//span[normalize-space()='OK']")
        ok_button.click()

        more_flights = driver.find_element(By.XPATH, "//div[@class='zISZ5c QB2Jof']") 
        more_flights.click()

        # Waiting and initial XPATH cleaning
        # WebDriverWait(driver, timeout = 10).until(lambda d: len(get_flight_elements(d)) > 1000)
        WebDriverWait(driver, timeout = 10).until(
            EC.text_to_be_present_in_element(
            (By.XPATH, "//span[@class='bEfgkb ']"), # Element Filtration
            "Hide"# The Expected Text
            )
        )

        # price_history = driver.find_element(By.XPATH, "//div[@class='GY6iob AdWm1c I3j9Le']") #"//div[@class='iy3L1b']"
        # 
        # price_history = WebDriverWait(driver, timeout = 20).until(EC.element_to_be_clickable(
        #         (By.XPATH, "//div[@class='vx1PSc']")
        #         )).click()  
        # HISTORICAL PRICES
        # # Wait for the button element to be clickable
        # button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='View price history']")))
        # button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".VfPpkd-LgbsSe"))) 
        # # Click on the button
        # button.click()

        results = get_flight_elements(driver)
        # price_history = find_flight_history_price(driver)
        driver.quit()

    if isinstance(url, list):
        # Instantiate driver
        driver = webdriver.Chrome(options=chrome_options)

        # Begin getting results for each url
        results = []
        for u in tqdm(url, desc = 'Data Scrape'):
            driver.get(u)

            try:
                WebDriverWait(driver, timeout = 30).until(lambda d: len(get_flight_elements(d)) > 100)
                results += [get_flight_elements(driver)]
            except:
                print('Timeout exception')

        driver.quit()

    # return results, price_history
    return results