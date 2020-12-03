import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk
import folium
from streamlit_folium import folium_static


st.beta_set_page_config(layout="wide")
DATE_TIME = "date/time"

@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv('cs_data.csv', nrows=nrows, dtype='str')
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data[DATE_TIME] = pd.to_datetime(data[DATE_TIME])
    return data

def load_branch_data(nrows):
    data = pd.read_csv('7eleven_branch.csv', nrows=nrows, dtype='str')
    return data

data = load_data(10000)
branch_df = load_branch_data(10000)
branch_df[['lat', 'lon']] = branch_df[['lat', 'lon']].apply(pd.to_numeric)
data.merge(branch_df, on='branch', how='outer')

def map(data, lat, lon, zoom):
    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": lat,
            "longitude": lon,
            "zoom": zoom,
            "pitch": 40
        },
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=data,
                get_position=["lon", "lat"],
                radius=100,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
        ]
    ))

# Data preparation

#data = data.replace(branch_df.set_index('branch')['name'])
monthly_data = pd.read_csv('monthly_data.csv')
monthly_data.set_index(keys='Month', inplace=True)
monthly_df = pd.DataFrame(monthly_data)
top_txn = pd.DataFrame(data['branch'].value_counts().head(10))
hour_data = data.groupby(data[DATE_TIME].dt.hour).size()
hist = np.histogram(data[DATE_TIME].dt.hour, bins=24, range=(0, 24))[0]
hour_df = pd.DataFrame({"hour": range(24), "transactions": hist})
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_data = data.groupby(data[DATE_TIME].dt.day_name()).size().reindex(DAYS)
percent_data = (day_data / day_data.sum()) * 100
days_df = pd.DataFrame({"day": DAYS, "percentage": percent_data})
days_df.set_index(keys='day', inplace=True)


# Data visualisation

st.title("i-Confirm @ 7-Eleven")

row1_1, row1_2 = st.beta_columns((1,1))
row2_1, row2_2, row2_3 = st.beta_columns((1,1,1))

with row1_1:
    st.write("**Nationwide**")
    branch_df[['lat', 'lon']] = branch_df[['lat', 'lon']].apply(pd.to_numeric)
    #data[['lat', 'lon']] = data[['lat', 'lon']].apply(pd.to_numeric)
    map(branch_df, np.average(branch_df["lat"]), np.average(branch_df["lon"]), 11)
    #st.map(branch_df.dropna(subset=['lat', 'lon']))

with row1_2:
    st.write("**Bangkok**")
    lats = branch_df['lat']
    lons = branch_df['lon']
    names = branch_df['branch'] + branch_df['name']
    m = folium.Map(location=[lats[0], lons[0]], zoom_start=12)
    for lat, lon, name in zip(lats, lons, names):
        # Create marker with other locations
        folium.Marker(location=[lat, lon],
                      popup=name,
                      icon=folium.Icon(color='green')
                      ).add_to(m)
    folium_static(m)

with row2_1:
    st.write("**Rank #1**")

with row2_2:
    st.write("**Rank #2**")

with row2_3:
    st.write("**Rank #3**")

st.subheader('**Number of transactions between Bangkok and provincial area by month**')
st.line_chart(monthly_df)

st.subheader('Top branches having customers identified oneself')

st.bar_chart(top_txn)
if st.checkbox('Show top branches data table'):
    data = data.replace(branch_df.set_index('branch')['name'])
    top_name = pd.DataFrame(data['branch'].value_counts().head(10))
    st.write(top_name)

st.subheader('Breakdown of transactions per hour')
st.altair_chart(alt.Chart(hour_df)
    .mark_area(
        interpolate='step-after',
    ).encode(
        x=alt.X("hour:Q", scale=alt.Scale(nice=False)),
        y=alt.Y("transactions:Q"),
        tooltip=['hour', 'transactions']
    ).configure_mark(
        opacity=0.5,
        color='red'
    ), use_container_width=True)

if st.checkbox('Show transactions data table'):
    st.write(hour_df)

st.subheader('Percentage of transactions by day of week')
st.bar_chart(days_df)
st.line_chart(days_df)
if st.checkbox('Show percentage data table'):
    st.write(days_df)