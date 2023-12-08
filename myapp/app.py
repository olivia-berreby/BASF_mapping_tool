# import all required packages
import json
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
from urllib.request import urlopen
import pandas as pd
from dash import callback_context
import numpy as np
import os

# set the current directory to myapp, this will be comented out for submission but is needed when running the app on Heroku because the directory needs to be set
# os.chdir("myapp")


# Load county geojson data
with urlopen(
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
) as response:
    counties = json.load(response)

# Load the state geoson data
with urlopen(
    "https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_040_00_5m.json"
) as response:
    states = json.load(response)


# Load data, format: load data, create variables for col names, if new column names update them here

# Data for plastic generated
df_plastic_generated = pd.read_csv("data/plastic_generation_county.csv")
col_fip_code = "FIPS"
col_plastic_generated_per_county = "tons generated in county (2022)"
df_plastic_generated["FIPS"] = df_plastic_generated["FIPS"].astype(str).str.zfill(5)


# Data for state regulations
df_regulations = pd.read_excel("data/regulations_state.xlsx")
col_state = "State"
col_state_abrv = "State_abbreviation"
col_rating = "ranking"
col_laws = "Applicable laws "
col_law_description = "Description of Laws"
col_law_short_description = "Short Description of laws "
col_law_sources = "Sources"
col_other_info = "Other relevant information "


# Data on existing pyrolysis oil companies
df_companies = pd.read_excel(
    "data/market_analysis_pyrolisis_oil.xlsx", sheet_name="USA 2.0"
)
col_longitude = "Longitude"
col_latitude = "Latitude"
col_text = "Text"
col_company_name = "Company Name"
col_link = "URL"
col_address = "Corporate Address"
col_partnerships = "Existing Parnerships"
col_feedstock = "Feedstock"
col_product_service = "Products and Services"


# Data on existing landfills in the US
df_landfills = pd.read_csv("data/landfill_information.csv")
col_landfill_state = "State"
col_landfill_county = "County"
col_landfill_lat = "Latitude"
col_landfill_lon = "Longitude"
col_landfill_closure_year = "Landfill Closure Year"
col_landfill_area = "Design Landfill Area (acres)"
col_landfill_years_to_fill = "Years until Fill"
col_landfill_planned_closure = "Years to Planned Closure"
col_landfill_waste = "Waste in Place (tons)"
col_landfill_acceptance = "Annual Waste Acceptance Rate (tons per year)"
col_landfill_available = "Percent Available"
col_landfill_volume_design = "Designed Volume (acres^3)"
df_landfills[col_landfill_years_to_fill] = df_landfills[
    col_landfill_years_to_fill
].where(~pd.isna(df_landfills[col_landfill_years_to_fill]), "click for more info")


# Link css style sheet to the web page
app = dash.Dash(__name__, external_stylesheets=["/assets/style.css"])
server = app.server

# Following code established the layout of the website
# The layout includes the header and header description at the top; the options to modify the interactive map on the right; and the map in the center-left.
app.layout = html.Div(
    className="app-container",
    children=[
        html.Div(  # header
            children=[
                html.Div(
                    children=[
                        html.Img(
                            src=app.get_asset_url("images/icons/BASF logo.jpg"),
                            className="header-logo",
                        ),
                        html.Span(
                            " Strategic Mapping Tool",
                            style={"verticalAlign": "middle"},
                        ),
                    ],
                    className="header-title",
                ),
                html.P(  # header-description
                    children="Explore Advanced Recycling Opportunities in the US",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(  # Options container, the menu with all info to click for the map
            className="options-container",
            children=[
                html.Div(  # Map coloring options
                    className="map_coloring_menu",
                    children=[
                        html.P("Select map coloring:"),
                        dcc.RadioItems(
                            id="map_color",
                            options=[
                                {
                                    "label": "Regulations - per state",
                                    "value": "regulations_state",
                                },
                                {
                                    "label": "Plastic generated in 2022 (tons) - per county",
                                    "value": "plastic_generated_county",
                                },
                                {
                                    "label": "No coloring",
                                    "value": "nothing",
                                },
                            ],
                            value="regulations_state",
                        ),
                    ],
                ),
                html.Div(  # Pin options
                    className="pin_options",
                    children=[
                        html.P("Additional information to plot:"),
                        dcc.Checklist(
                            id="pin-checklist",
                            options=[
                                {
                                    "label": "Locations of Existing Pyrolysis Oil Producing Companies",
                                    "value": "companies",
                                },
                                {
                                    "label": "Location of Landfills",
                                    "value": "landfills",
                                },
                                {
                                    "label": "Location of Landfills - Full in 10 Years",
                                    "value": "landfills_10",
                                },
                            ],
                            value=[],
                        ),
                    ],
                ),
                html.Div(
                    id="text_box",
                    className="text-box",
                    children=[],
                ),
            ],
        ),
        html.Div(  # Map
            className="map",
            children=[
                dcc.Graph(id="us-map", className="map"),
            ],
        ),
    ],
)


# The following is the app callback, so the code that handles updating the map when options are clicked, coloring the map and updating the pins that are displayed.
@app.callback(
    Output("us-map", "figure"),  # output is always the map
    [
        Input("map_color", "value")
    ],  # input, the map_coloring in the form of the ONE option selected in the dcc.RadioItems
    [
        Input("pin-checklist", "value")
    ],  # input the pins displayed through which MULTIPLE options selected in the dcc.Checklist
)
# function that updates the map, will be used when any new option is selected
def update_map(selected_option, selected_pins):
    # Change color to regulations per state according to our rating -1, 0, 1.
    if selected_option == "regulations_state":
        fig = px.choropleth_mapbox(
            df_regulations,
            locations="State",
            geojson=states,
            featureidkey="properties.NAME",
            color=col_rating,
            color_continuous_scale="RdYlGn",
            mapbox_style="carto-positron",
            zoom=3.2,
            center={"lat": 37.0902, "lon": -95.7129},
            opacity=0.6,
            labels={col_rating: "Rating"},
        )

        fig.update_traces(hovertemplate="<b>%{properties.NAME}</b><extra></extra>")

    # Change color to plastic generated by county, with hover information per county
    elif selected_option == "plastic_generated_county":
        df_plastic_generated["County_State"] = (
            df_plastic_generated["County"] + ", " + df_plastic_generated["State"]
        )

        df_plastic_generated["log_plastic_generated"] = np.log10(
            df_plastic_generated[col_plastic_generated_per_county] + 1
        )

        fig = px.choropleth_mapbox(
            df_plastic_generated,
            geojson=counties,
            locations=col_fip_code,
            color="log_plastic_generated",
            color_continuous_scale="Plasma",
            mapbox_style="carto-positron",
            zoom=3.2,
            center={"lat": 37.0902, "lon": -95.7129},
            opacity=0.8,
            labels={
                col_plastic_generated_per_county: "Plastic Generated (tons)",
                "log_plastic_generated": "Plastic Generated (tons) Log Scale",
            },
            hover_data={"County_State": False, col_plastic_generated_per_county: True},
            custom_data=["County_State", col_plastic_generated_per_county],
        )

        fig.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>Plastic Generated (tons): %{customdata[1]}<extra></extra>"
        )

    # have no coloring, using the county data, hover over an get county info, but opacity set the zero for no coloring
    elif selected_option == "nothing":
        df_plastic_generated["County_State"] = (
            df_plastic_generated["County"] + ", " + df_plastic_generated["State"]
        )

        fig = px.choropleth_mapbox(
            df_plastic_generated,
            geojson=counties,
            locations=col_fip_code,
            color=np.repeat("grey", df_plastic_generated.shape[0]),
            mapbox_style="carto-positron",
            zoom=3.2,
            center={"lat": 37.0902, "lon": -95.7129},
            opacity=0,
            custom_data=["County_State"],
        )

        fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><extra></extra>")
        # hide legend
        fig.update_layout(showlegend=False)

    # Add company pins if selected in the checklist
    if "companies" in selected_pins:
        scattermapbox_trace = go.Scattermapbox(
            lon=df_companies[col_longitude],
            lat=df_companies[col_latitude],
            mode="markers",
            marker=go.scattermapbox.Marker(size=10, color="blue"),
            name="Companies",
            hovertemplate="<b>%{text}</b><extra></extra>",
            text=df_companies[col_company_name].apply(lambda x: f"Company: {x}"),
        )

        # Add the scatter plot trace to the choropleth figure
        fig.add_trace(scattermapbox_trace)

    # create a function to have a color scale for the landfills
    def get_color_scale(value):
        if isinstance(value, str):
            return "darkgrey"  # Dark grey for NaN values
        elif value < 10:
            return "red"  # Red for less than 10 years
        elif 10 <= value < 20:
            return "orange"  # Orange for 10 to 20 years
        else:
            return "green"  # Green for 20 years or more

    # plot the landfills, with the color scale
    if "landfills" in selected_pins:
        landfill_colors = df_landfills[col_landfill_years_to_fill].apply(
            get_color_scale
        )

        scattermapbox_trace = go.Scattermapbox(
            lon=df_landfills[col_landfill_lon],
            lat=df_landfills[col_landfill_lat],
            mode="markers",
            marker=go.scattermapbox.Marker(size=6, color=landfill_colors),
            name="Landfills",
            hovertemplate="<b>%{text}</b><extra></extra>",
            text=[
                f"Landfill: {row[col_landfill_county]}, Years to fill: {row[col_landfill_years_to_fill]}"
                for _, row in df_landfills.iterrows()
            ],
        )

        # Add the scatter plot trace to the choropleth figure
        fig.add_trace(scattermapbox_trace)
    # Temporarily convert the column to numeric for comparison, coercing errors to NaN
    temp_numeric_series = pd.to_numeric(
        df_landfills[col_landfill_years_to_fill], errors="coerce"
    )
    # Perform the comparison on numeric values only
    less_than_10_years_mask = temp_numeric_series < 10
    # Plot for landfills with less than 10 years to fill or closure
    if "landfills_10" in selected_pins:
        filtered_landfills = df_landfills[
            less_than_10_years_mask | (df_landfills[col_landfill_planned_closure] < 10)
        ]

        scattermapbox_trace_10 = go.Scattermapbox(
            lon=filtered_landfills[col_landfill_lon],
            lat=filtered_landfills[col_landfill_lat],
            mode="markers",
            marker=go.scattermapbox.Marker(size=8, color="red"),
            name="Landfills <10 Years",
            hovertemplate="<b>%{text}</b><extra></extra>",
            text=[
                f"Landfill: {row[col_landfill_county]}, Years to fill: {row[col_landfill_years_to_fill]}"
                for _, row in filtered_landfills.iterrows()
            ],
        )

        # Add the scatter plot trace for filtered landfills to the choropleth figure
        fig.add_trace(scattermapbox_trace_10)

    # General update of the map, size of the color bar and margins
    fig.update_layout(
        coloraxis_colorbar=dict(
            len=0.8,
        )
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


# other callback function that updates the text box in the bottom right, so all info when clicked on items on the map
@app.callback(
    Output("text_box", "children"),
    [Input("us-map", "clickData")],
    [State("pin-checklist", "value"), State("map_color", "value")],
)
# Function for updating the text box based on user interactions with a map
def update_text_box(clickData, selected_pins, selected_map):
    # Check if there is any click data to process
    if clickData:
        # Extract the first point of click data
        points = clickData.get("points", [{}])
        first_point = points[0]
        # Retrieve the text associated with the clicked point
        text_data = first_point.get("text", None)

        # If the clicked point is a company, display company information
        if text_data and text_data.startswith("Company:"):
            # Extract the company name from the clicked point
            company_name = text_data.split(": ", 1)[1]
            # Retrieve company information from a dataframe
            company_info = df_companies[
                df_companies[col_company_name] == company_name
            ].iloc[0]
            # Prepare the company information to be displayed
            company_description = (
                company_info[col_text] if company_info[col_text] else "No information"
            )
            company_link = company_info[col_link] if company_info[col_link] else "#"

            # Return a layout of HTML elements containing the company information
            return html.Div(
                [
                    html.H4("Company name:"),
                    html.P(company_name),
                    html.H4("Feedstock:"),
                    html.P(company_info[col_feedstock]),
                    html.H4("Products and Services:"),
                    html.P(company_info[col_product_service]),
                    html.H4("Company description:"),
                    html.P(company_description),
                    html.H4("Existing Partnerships:"),
                    html.P(company_info[col_partnerships]),
                    html.H4("Corporate Address:"),
                    html.P(company_info[col_address]),
                    html.A("Visit Website", href=company_link, target="_blank")
                    if company_link != "#"
                    else html.P("No link available"),
                ]
            )

        # If the clicked point is a landfill, display landfill information
        elif text_data and text_data.startswith("Landfill:"):
            # Extract and process landfill information from the clicked point
            _, landfill_text = text_data.split(": ", 1)
            county, years_to_fill_text = landfill_text.split(", Years to fill: ")
            landfill_info = df_landfills[
                (df_landfills[col_landfill_county] == county.strip())
                & (
                    df_landfills[col_landfill_years_to_fill].astype(str)
                    == years_to_fill_text.strip()
                )
            ]

            # Check if the landfill information is found and prepare it for display
            if not landfill_info.empty:
                landfill_info = landfill_info.iloc[0]
                # Return HTML display of the landfills
                return html.Div(
                    [
                        html.H4("Location:"),
                        html.P(
                            f"{landfill_info[col_landfill_county]}, {landfill_info[col_landfill_state]}"
                        ),
                        html.H4("Landfill Closure Year:"),
                        html.P(landfill_info[col_landfill_closure_year]),
                        html.H4("Annual Waste Acceptance Rate (tons per year):"),
                        html.P(landfill_info[col_landfill_acceptance]),
                        html.H4("Percent Available:"),
                        html.P(f"{landfill_info[col_landfill_available]}%"),
                        html.H4("Years to Fill:"),
                        html.P(landfill_info[col_landfill_years_to_fill]),
                        html.H4("Years to Planned Closure:"),
                        html.P(landfill_info[col_landfill_planned_closure]),
                        html.H4("Design Landfill Area (acres):"),
                        html.P(landfill_info[col_landfill_area]),
                        html.H4("Designed Volume (acres^3):"),
                        html.P(landfill_info[col_landfill_volume_design]),
                        html.H4("Waste in Place (tons):"),
                        html.P(landfill_info[col_landfill_waste]),
                    ]
                )
            else:
                return html.Div([html.P("Landfill information not found.")])

        # If the selected map is for state regulations and a state is clicked, display state information
        elif selected_map == "regulations_state" and first_point.get("location", None):
            # Extract the state name from the clicked point
            state_name = first_point["location"]
            # Retrieve state information from a dataframe
            state_info = df_regulations[df_regulations[col_state] == state_name].iloc[0]

            # Return a layout of HTML elements containing the state information
            return html.Div(
                [
                    html.H4("State:"),
                    html.P(state_info[col_state]),
                    html.H4("Laws in Place:"),
                    html.P(state_info[col_laws]),
                    html.H4("Short Description of the Law:"),
                    html.P(state_info[col_law_short_description]),
                    html.H4("Description of the Law:"),
                    html.P(state_info[col_law_description]),
                    html.H4("Other Information:"),
                    html.P(state_info[col_other_info]),
                    html.H4("Sources:"),
                    html.P(state_info[col_law_sources]),
                ]
            )

    # Default return if no valid click data is found
    return ""


# Run app
if __name__ == "__main__":
    app.run_server(debug=True)
