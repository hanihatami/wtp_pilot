from lib.flight_price_scraping.utils import make_url, get_results, convert_to_price_history_dataframe
import pandas as pd

def scrape_data(origin, dest, date_leave, date_return, cache = False) -> dict:
    '''
        Scraping multiple urls
    '''
    if isinstance(date_leave, list) and isinstance(date_return, list):
        # Construct list of urls
        url = [make_url(origin = origin, dest = dest, date_leave = date_leave[i], date_return = date_return[i]) for i in range(len(date_leave))]
        
        # Get the data of urls
        data = get_results(url = url, origin = origin, dest = dest, date_leave = date_leave, date_return = date_return)

        # # Cache them
        # if cache:
        #     cache_data(data = data, origin = origin, dest = dest)

        return data

    '''
        Scraping single url
    '''
    if isinstance(date_leave, str) and isinstance(date_return, str):
        # Construct one url
        url = make_url(origin = origin, dest = dest, date_leave = date_leave, date_return = date_return)

        # Get the data
        # data, price_history = get_results(url = url, origin = origin, dest = dest, date_leave = date_leave, date_return = date_return)
        data = get_results(url = url, origin = origin, dest = dest, date_leave = date_leave, date_return = date_return)

        # # Cache it
        # if cache:
        #     cache_data(data = data, origin = origin, dest = dest)
        # price_history_df = convert_to_price_history_dataframe(price_history)
        
        return pd.DataFrame(data)#, price_history_df

    else:
        raise TypeError('Incorrect types provided')