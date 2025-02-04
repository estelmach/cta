import pandas as pd
import geopandas as gpd
import altair as alt
import streamlit as st
import os

@st.cache_data
def load_data():

    # Load the data
    st.write(os.listdir('/data/silver/'))
    filepath = '/data/silver/'

    # load geodata
    parkRide_df = gpd.read_parquet(filepath + 'DimParkRide.parquet')
    railLine_df = gpd.read_parquet(filepath + 'DimRailLine.parquet')
    railStation_df = gpd.read_parquet(filepath + 'DimRailStation.parquet')
    commArea_df = gpd.read_parquet(filepath + 'DimCommunityArea.parquet')

    # load other data
    stationEntries_df = pd.read_parquet(filepath + 'FactSTationEntries.parquet')

    return parkRide_df, railLine_df, railStation_df, commArea_df, stationEntries_df


def plot_map(railLine_df, railStation_df, commArea_df):

    # dummy data add to make charts work in streamlit due to current bug

    commArea_map = alt.Chart(commArea_df).mark_geoshape(
        fill='lightgrey', stroke='white'
    ).properties(
        width=900, 
        height=900
    )

    railLine_map = alt.Chart(railLine_df).mark_geoshape(
        filled=False, 
        strokeWidth=2,
    ).encode(
        color=alt.Color('SystemRouteHexColor', scale=None)
    )

    # map stations in a normal dataframe - this will also help with animation
    railStation_df['lat'] = railStation_df.geometry.y
    railStation_df['lon'] = railStation_df.geometry.x

    railStation_map = alt.Chart(railStation_df).mark_circle(
        fill='white', 
        stroke='black', 
        size=30
    ).encode(
        longitude='lon', 
        latitude='lat'
    )

    # comebine into a single map
    layered_map = commArea_map + railLine_map + railStation_map

    # make interactive
    layered_map.interactive()

    st.altair_chart(layered_map, use_container_width=True)


def main():
    text = st.empty()

    text.write('Loading data...')
    _, railLine_df, railStation_df, commArea_df, _ = load_data()
    text.write('Data loaded!')

    text.write('Plotting map...')
    plot_map(railLine_df, railStation_df, commArea_df)


if __name__ == "__main__":
    main()

