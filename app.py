import geopandas as gpd
import pandas as pd
import geodatasets
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import streamlit as st
import altair as alt

# refactor eventually to save the raw assets - no reason to do this every time

def main():

    st.set_page_config(layout='wide')

    chicago_url = geodatasets.get_url('geoda.chicago_commpop.geojson')
    st.write(chicago_url)

    # using https://github.com/streamlit/streamlit/issues/1002#issuecomment-967582597
    chicagoMap = alt.Chart(chicago).mark_geoshape().encode(color='POP2010', shape='geometry:G').project('albersUsa')
    lineMap = alt.Chart(lines_simplified).mark_geoshape(stroke='black')
    stationMap = alt.Chart(stations).mark_circle(size=100, fill='white', stroke='black', opacity=1).encode(longitude='lon:Q', latitude='lat:Q')

    layered_chart = chicagoMap + lineMap + stationMap

    st.altair_chart(layered_chart)

    st.write('plotted!')


    html_string = ('''<br> <p style="text-align:center;">Made with <strong>Streamlit 
                   </strong>near the Western Blue Line Station (O'Hare Branch) in Chicago, IL 💖🚉</p>
                   <p style="text-align:center;"><sub>Data from </sub><a target="_blank" rel="noopener 
                   noreferrer" href="https://www.transitchicago.com/data/">
                   <sub>transitchicago.com/data</sub></a></p>'''
    )
    st.html(html_string)
        

if __name__ == '__main__':
    main()