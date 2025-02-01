import geopandas as gpd
import pandas as pd
import geodatasets
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import streamlit as st

# refactor eventually to save the raw assets - no reason to do this every time

@st.cache_data
def data_load():
    '''load all necessary data, wrap with @st.cache to only run once; returns the dfs'''

    with st.empty():
        # read the rail lines in
        st.write('Importing Rail Lines')
        lines = gpd.read_file("./CTA_RailLines/doc.kml")

        # explode the lines so you plot once for each time they overlap
        st.write('Transforming Rail Line Data...')
        lines['Name'] = lines.Name.str.split(', ')
        lines = lines.explode('Name')

        # replace the names with a consistent naming convention 
        names_mapping = {
            'Yellow Line': 'Yellow',
            'Orange Line': 'Orange',
            'Blue Line (O\'Hare)': 'Blue',
            'Blue Line (Forest Park)': 'Blue',
            'Pink Line': 'Pink',
            'Brown': 'Brown',
            'Purple (Express)': 'Purple (Exp)',
            'Red': 'Red',
            'Brown Line': 'Brown',
            'Purple Line': 'Purple',
            'Red Line': 'Red',
            'Purple': 'Purple',
            'Green': 'Green',
            'Orange': 'Orange',
            'Pink': 'Pink',
            'Purple (Exp)': 'Purple (Exp)',
            'Green Line': 'Green'
        }
        lines['Name'] = lines.Name.map(names_mapping)

        # Add the color coding: 
        lineColorMap = {
            "Red": "#c60c30",
            "Blue": "#00a1de",
            "Brown": "#62361b",
            "Green": "#009b3a",
            "Orange": "#f9461c",
            "Purple": "#522398",
            "Purple (Exp)": "#522398", # using same color for now - can switch this up later
            "Pink": "#e27ea6",
            "Yellow": "#f9e300",
            "Sign Grey": "#565a5c"
        }
        lines['Color'] = lines.Name.map(lineColorMap)

        # READ station file to a geopandas dataframe 
        st.write('Importing stations data...')
        stations = gpd.read_file("./CTA_RailStations/doc.kml")

        st.write('Transforming station data...')
        # get the lat/long - this helps us later
        stations['lat'] = stations.geometry.x
        stations['lon'] = stations.geometry.y

        def get_metadata(html_string):
            # parse with beautiful soup
            parsed_metadata = BeautifulSoup(html_string)

            # get the rail line from the html table
            rail_line = parsed_metadata.find('td', string='Rail Line').find_next_sibling('td').text

            # get the station id from the html table
            station_id = parsed_metadata.find('td', string='Station ID').find_next_sibling('td').text

            return (rail_line, station_id)

        stations['metadata'] = stations.Description.apply(get_metadata)

        # parse metadata out
        stations['RailLine'] = stations.metadata.str[0]
        stations['StationID'] = stations.metadata.str[1]

        # get the daily L station entries
        st.write('Getting ridership data...')
        entries_df = pd.read_csv('L_Station_EntriesDaily_Totals_20250201.csv', parse_dates=['date'], dtype={'station_id': str})

        st.write('Transforming ridership data...')
        # station ID has an identifier at the beginning per https://www.transitchicago.com/assets/1/6/cta_Train_Tracker_API_Developer_Guide_and_Documentation.pdf, separate that out
        # change to int and back to remove leading zeroes
        entries_df['StationID'] = entries_df.station_id.str[1:].astype(int).astype(str)

        # create datatime columns
        entries_df['YearMonth'] = entries_df.date.dt.strftime('%Y-%m')

        # sort
        entries_df = entries_df.sort_values(by='date', ascending=True)

        # get the year-monthly rider counts
        year_month_ridership = entries_df.groupby(['YearMonth', 'StationID'], as_index=False).rides.sum()

        # merge to get the station ID plots with counts
        year_month_ridership_stations = year_month_ridership.merge(stations, on='StationID')

        # generate year-month sequence for animation
        year_month_ridership_stations['YearMonthKey'] = (year_month_ridership_stations['YearMonth'] != year_month_ridership_stations['YearMonth'].shift()).cumsum()

        # get chicago map
        st.write('Getting Chicagoland map assets...')
        chicago = gpd.read_file(geodatasets.get_path('geoda.chicago_commpop'))

        return chicago, lines, year_month_ridership_stations

def main():
    import time

    chicago, lines, year_month_ridership_stations = data_load()
    st.write('Done!')

    ##
    ## PLOT : Just Jan 2001 For Now
    ##

    # set marker size for the rides
    year_month_ridership_stations['markersize'] = (year_month_ridership_stations.rides / 4000).astype(int)

    # set up the progress bar
    frames = year_month_ridership_stations.YearMonthKey.max()
    status_text = st.empty()
    progress_bar = st.progress(0)

    fig, (ax1, ax2) = plt.subplots(
        nrows=2, 
        ncols=1, 
        figsize=(6, 11.66),
        gridspec_kw={'height_ratios': [5, 1]}
    )

    fig.tight_layout()

    ###
    ### TRANSIT AND STATION MAP
    ###

    # remove coordinates from the chicago map
    ax1.set_axis_off()
    ax1.set_title('Monthly Ridership by Chicago \'L\' Station \nStation bubble size = ridership', size=8)

    fig_chicago = chicago.boundary.plot(ax=ax1, lw=.66, alpha=.33)
    fig_rail_lines = lines.plot(ax=ax1, color=lines.Color, zorder=1)
    
    # plot on ax to remove later
    january_2001 = year_month_ridership_stations.loc[year_month_ridership_stations.YearMonth == '2001-01']
    fig_stations = ax1.scatter(
        x=january_2001.lat,
        y=january_2001.lon,
        s=january_2001.markersize, 
        marker='o', 
        color='white', 
        edgecolor='black', 
        zorder=2,
    )
    plot = st.pyplot(fig)

    html_string = ('''<br> <p style="text-align:center;">Made with <strong>Streamlit 
                   </strong>near the Western Blue Line Station (O'Hare Branch) in Chicago, IL 💖🚉</p>
                   <p style="text-align:center;"><sub>Data from </sub><a target="_blank" rel="noopener 
                   noreferrer" href="https://www.transitchicago.com/data/">
                   <sub>transitchicago.com/data</sub></a></p>'''
    )
    st.html(html_string)

    fig_stations.remove()

    def animate(frame): 
        stations_timeframe = year_month_ridership_stations.loc[year_month_ridership_stations.YearMonthKey == frame]
        fig_stations = ax1.scatter(
            x=stations_timeframe.lat,
            y=stations_timeframe.lon,
            s=stations_timeframe.markersize, 
            marker='o', 
            color='white', 
            edgecolor='black', 
            zorder=2,
        )
        plot.pyplot(fig)
        fig_stations.remove()
 
    # have to use index 1 becasue that's whaat the YearMonthKey column starts with - otherwise will get error when accessing
    for frame in range(1, frames):
        animate(frame)

        # clean up later, not efficient - but use this to display
        currentYearMonth_df = year_month_ridership_stations.loc[year_month_ridership_stations.YearMonthKey == frame]
        if len(currentYearMonth_df) > 0:  # handles any missing data
            currentYearMonth = currentYearMonth_df.YearMonth.iloc[0]
            status_text.text(f'Month: {currentYearMonth}')
            progress_bar.progress(frame / frames)

    
        

if __name__ == '__main__':
    main()