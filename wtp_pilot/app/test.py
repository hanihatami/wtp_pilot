import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time

# Sample DataFrame with columns 'date' and 'capacity'
# Replace this with your actual DataFrame
data = {
    'date':  pd.date_range(start='2023-01-01', periods=365, freq='D'),
    'capacity': range(1, 366)
}
df = pd.DataFrame(data)

# Create a Streamlit figure and axis
fig, ax = plt.subplots()
ax.set_xlabel('Date')
ax.set_ylabel('Capacity')
ax.set_title('Dynamic Time Series Plot')
ax.grid(True)

# Create a Streamlit figure placeholder
st_figure = st.pyplot(fig)

# Animation settings
speed = 0.001  # Adjust the speed (in seconds) to control the animation

# Update the plot dynamically
for i, row in df.iterrows():
    ax.clear()
    ax.plot(df['date'][:i+1], df['capacity'][:i+1], marker='o')
    ax.set_xlabel('Date')
    ax.set_ylabel('Capacity')
    ax.set_title('Dynamic Time Series Plot')
    ax.grid(True)
    st_figure.pyplot(fig)
    time.sleep(speed)
