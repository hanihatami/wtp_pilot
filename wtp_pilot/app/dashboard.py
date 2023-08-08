import sys
import streamlit as st
import toml
from PIL import Image
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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

# Info
with st.expander(
    "Pilot app to build a WTP estimation for a pretend flight", expanded=False
):
    st.write(readme["app"]["app_intro"])
    st.write("")
st.write("")
st.sidebar.image(load_image("logo.jpg"), use_column_width=True)


st.sidebar.title("1. Data")
# Load data
with st.sidebar.expander("Dataset", expanded=True):
    load_options, datasets = dict(), dict()
    load_options["toy_dataset"] = st.checkbox("Load a toy dataset", True, help=readme["tooltips"]["upload_choice"])
    if load_options["toy_dataset"]:
        dataset_name = st.selectbox(
            "Select a toy dataset",
            options= ["Mock WTP"],
            # format_func=lambda x: config["datasets"][x]["name"],
            help=readme["tooltips"]["toy_dataset"]   
        )
        df = pd.read_csv(Path(get_project_root()) / "wtp_pilot/inputs/wtp_mock_data3.csv")


st.sidebar.title("2. Flight")
# Choose flight
with st.sidebar.expander("Flight", expanded=False):
    flight_selected = st.selectbox(
            "Flight Number",
            ["NZ631"],
            help = readme["tooltips"]["select_flight"],
        )
    flight_df = df[df["flight_number"] == flight_selected]

    class_selected = st.selectbox(
            "Flight Class",
            ["Economy", "Business"],
            help = readme["tooltips"]["select_class"],
        )
    flight_class_df = flight_df[flight_df["class"] == class_selected]
    if class_selected == "Economy":
        txt = ["100", "+80", "+30", "-40", "-20", "wtp"]
        vals_y = [100, 80, +30, -40, -20, 0]
        baseline = 500
    else:
        txt = ["fare", "+210", "-45", "+150", "+240","wtp"]
        vals_y = [500, 210, -75, +150, +240, 0]
        baseline = 5000
#  x = ["Fare", "WOY", "DOW", "DTD", "SEARCH", "POS", "WTP"],

# fig = go.Figure()
# colors = {"price": "blue", "wtp": "green"}
# fig.add_trace(go.Bar(x=flight_class_df["date"], y=flight_class_df['air_fare_usd'], name='price', marker_color=colors['price']))
# fig.add_trace(go.Bar(x=flight_class_df["date"], y=flight_class_df['WTP'], name='wtp', marker_color=colors['wtp']))
# st.plotly_chart(fig)
################################################################
average__seats_per_DCP = flight_class_df.groupby("DCP")["number_of_checkouts"].sum().mean()
average__wtp_per_DCP = flight_class_df.groupby("DCP")["WTP2"].mean().mean()

flight_class_df['date'] = pd.to_datetime(flight_class_df['date'])
average_checkout_rate = flight_class_df[['date', 'checkout_rate']].set_index('date').resample('W').mean()

revenue_generated = flight_class_df['daily_revenue'].sum()
wtp_revenue_generated = (flight_class_df['WTP2'] * flight_class_df["number_of_checkouts"]).sum()
flight_class_df['day_name'] = flight_class_df['date'].dt.day_name()
weekday_wtp = flight_class_df.groupby('day_name')['WTP2'].mean().reset_index()
################################################################
col1, col2, col3, col4 = st.columns(4)
with col1:
    CHART_THEME = 'plotly_white' 

    indicators_ptf1 = go.Figure()
    indicators_ptf1.layout.template = CHART_THEME
    indicators_ptf1.add_trace(go.Indicator(
        mode = "number+delta",
        value = average__seats_per_DCP,
        number = {'suffix': ""},
        title = {"text": "<br><span style='font-size:1.5em;color:gray'>Seats Sold per DCP</span>"},
        delta = {'position': "bottom", 'reference': average__seats_per_DCP, 'relative': True},
        domain = {'row': 0, 'column': 0}))

    indicators_ptf1.update_layout(
        height=300,
        width=300
        )
    st.plotly_chart(indicators_ptf1)
with col2:    
    indicators_ptf2 = go.Figure()
    indicators_ptf2.add_trace(go.Indicator(
        mode = "number+delta",
        value = average__wtp_per_DCP,
        number = {'suffix': ""},
        title = {"text": "<span style='font-size:1.5em;color:gray'>Average WTP per DCP</span>"},
        delta = {'position': "bottom", 'reference': average__wtp_per_DCP, 'relative': False},
        domain = {'row': 0, 'column': 1}))
    
    indicators_ptf2.update_layout(
        height=300,
        width=300
        )
    st.plotly_chart(indicators_ptf2)
with col3:    
    indicators_ptf3 = go.Figure()
    indicators_ptf3.add_trace(go.Indicator(
        mode = "number+delta",
        value = np.round(average_checkout_rate['checkout_rate'][-1],2),
        number = {'suffix': " %"},
        title = {"text": "<span style='font-size:1.5em;color:gray'>Check-out Rate</span>"},
        delta = {'position': "bottom", 'reference': average_checkout_rate['checkout_rate'][-2], 'relative': False},
        domain = {'row': 0, 'column': 2}))
    indicators_ptf3.update_layout(
        height=300,
        width=300
        )
    st.plotly_chart(indicators_ptf3)
with col4:   
    ref =  2/3 * revenue_generated if class_selected=='Economy' else 3/4*revenue_generated
    indicators_ptf4 = go.Figure()
    indicators_ptf4.add_trace(go.Indicator(
        mode = "number+delta",
        value = wtp_revenue_generated,
        number = {'suffix': ""},
        title = {"text": "<span style='font-size:1.5em;color:gray'>Revenue $</span>"},
        delta = {'position': "bottom",
                 'reference': ref,
                 'relative': False},
        domain = {'row': 0, 'column': 3}))
    indicators_ptf4.update_layout(
        height=300,
        width=300
        )
    st.plotly_chart(indicators_ptf4)
    # indicators_ptf.update_layout(
    #     grid = {'rows': 1, 'columns': 4, 'pattern': "independent"},
    #     margin=dict(l=50, r=50, t=30, b=30)
    # )
################################################################
col1, col2 = st.columns(2)
with col1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=flight_class_df["date"], y=flight_class_df["WTP2"],
                        mode='lines+markers',
                        name='WTP',
                        line = dict(color='#88cc43', width=4)))
    fig1.add_trace(go.Scatter(x=flight_class_df["date"], y=flight_class_df["air_fare_usd"],
                        mode='lines+markers',
                        name='Price',
                        line = dict(color='lightgrey', width=4)))
    # Edit the layout
    fig1.update_layout( 
                    width=600,
                    height=500,
                    title='Daily WTP vs airfare',
                    xaxis_title='Date',
                    yaxis_title='$ US Dollar')
    st.plotly_chart(fig1)

df_plot = flight_class_df.copy()
df_plot["net"] = df_plot["WTP2"]-df_plot["air_fare_usd"]
df_plot["Color"] = np.where(df_plot["net"]<0, '#f58787', '#88cc43')

with col2:
    fig4 = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["absolute", "relative", "relative", "relative", "relative", "total"],
        x = ["Fare", "WOY", "DOW", "DTD", "SEARCH",  "WTP"],
        textposition = "outside",
        text = txt,
        y = vals_y,
        base=baseline,
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        increasing = {"marker":{"color": "#88cc43"}},  # Color for increasing bars
        decreasing = {"marker":{"color": "#f58787"}},  # Color for decreasing bars
        totals = {"marker":{"color":'lightgrey', "line":{"color":'lightgrey', "width":3}}}
        # Set custom color for the "Fare" bar
    ))

    fig4.update_layout(
            title = "WTP Breakdown",
            showlegend = False,
            width=600,
            height=500
    )

    st.plotly_chart(fig4)

col1, col2 = st.columns(2)
with col1:
    fig3 = px.area(flight_class_df, x="date", y="website_visit", title="Financial Impact, World, RCP = 2.6", color_discrete_sequence=["#ffc0cb"])#ffd343##ffb300
    # Edit the layout
    fig3.update_layout(
                    width=600,
                    height=500,
                    title = "Number of searches on website",
                    xaxis_title='date',
                    yaxis_title='number')
    st.plotly_chart(fig3)
with col2:
    # colors = ['#A9A9A9', '#A2CD5A', '#006400', '#CDC8B1', '#26bf2e', '#77ba7a', '#808080']

    # fig4 = go.Figure(data=[go.Pie(labels=weekday_wtp['day_name'],
    #                             values=np.round(weekday_wtp['WTP2'],1))])
    # fig4.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=20,
    #                 marker=dict(colors=colors, line=dict(color='#000000', width=2)))
    
    # fig4.update_layout(
    #                 width=600,
    #                 height=500,
    #                 title = "Average daily WTP")
    # st.plotly_chart(fig4)

    fig2 = go.Figure()
    fig2.add_trace(
        go.Bar(name='Net',
            x=df_plot['date'],
            y=df_plot['net'],
            marker_color=df_plot['Color']))
    fig2.update_layout(barmode='stack')

    # Edit the layout
    fig2.update_layout( 
                    width=600,
                    height=500,
                    title='Daily difference of WTP and airfare',
                    xaxis_title='Date',
                    yaxis_title='$USD')

    st.plotly_chart(fig2)

    