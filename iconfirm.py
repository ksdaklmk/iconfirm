import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pydeck as pdk
import time
import folium
from streamlit_folium import folium_static
from altair import Chart, X, Y, Axis, SortField, OpacityValue


st.beta_set_page_config(layout="wide")
DATE_TIME = "date/time"


@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv('cs_data.csv', nrows=nrows, dtype='str')
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data[DATE_TIME] = pd.to_datetime(data[DATE_TIME])
    return data


@st.cache(persist=True)
def load_branch_data(nrows):
    data = pd.read_csv('7eleven_branch.csv', nrows=nrows, dtype='str')
    return data


data = load_data(100000)
branch_df = load_branch_data(1000)
branch_df[['lat', 'lon']] = branch_df[['lat', 'lon']].apply(pd.to_numeric)


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
                data=branch_df,
                get_position=["lon", "lat"],
                radius=100,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data = branch_df,
                get_position = '[lon, lat]',
                get_color = '[200, 30, 0, 160]',
                get_radius = 200,
            ),
        ]
    ))

st.title("i-Confirm @ 7-11 data")

row2_1, row2_2 = st.beta_columns((1,1))

with row2_1:
    st.write("**Nationwide**")
    branch_df[['lat', 'lon']] = branch_df[['lat', 'lon']].apply(pd.to_numeric)
    st.map(branch_df.dropna(subset=['lat', 'lon']))

with row2_2:
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

monthly_data = pd.read_csv('monthly_data.csv')
monthly_data.set_index(keys='Month', inplace=True)
monthly_df = pd.DataFrame(monthly_data)
st.subheader('**Number of transactions between Bangkok and provincial area by month**')
st.line_chart(monthly_df)

st.subheader('Top branches having customers identified oneself')
counter = st.slider('Select top number', 10, 50)
top_txn = pd.DataFrame(data['branch'].value_counts().head(counter))
st.bar_chart(top_txn)
if st.checkbox('Show raw data'):
    st.write(top_txn)

hour_data = data.groupby(data[DATE_TIME].dt.hour).size()
hist = np.histogram(data[DATE_TIME].dt.hour, bins=24, range=(0, 24))[0]
hour_df = pd.DataFrame({"hour": range(24), "transactions": hist})
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
