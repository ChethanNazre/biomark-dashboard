import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import json

# Load your JSON data
with open("biomarkers.json", "r") as f:
    data = json.load(f)

# Convert JSON data to DataFrame format
biomarkers_data = []
for biomarker, info in data["biomarkers"].items():
    biomarkers_data.append({
        "Patient Name": data["patient"]["name"],
        "Date": data["patient"]["date"],
        "Biomarker": biomarker,
        "Value": info["value"],
        "Unit": info["unit"],
        "Reference Range": info["reference_range"],
        "Low": info["low"],
        "High": info["high"]
    })

df = pd.DataFrame(biomarkers_data)
df["Date"] = pd.to_datetime(df["Date"])

# Biomarker groups
biomarker_groups = {
    "Lipid Profile": {
        "biomarkers": ["Total Cholesterol", "LDL", "HDL", "Triglycerides"],
        "ranges": {
            "Total Cholesterol": (0, 200),
            "LDL": (0, 100),
            "HDL": (40, 100),
            "Triglycerides": (0, 150)
        }
    },
    "Renal": {
        "biomarkers": ["Creatinine"],
        "ranges": {
            "Creatinine": (0.7, 1.3)
        }
    },
    "Vitamins": {
        "biomarkers": ["Vitamin D", "Vitamin B12"],
        "ranges": {
            "Vitamin D": (30, 100),
            "Vitamin B12": (211, 911)
        }
    },
    "Diabetes": {
        "biomarkers": ["HbA1c"],
        "ranges": {
            "HbA1c": (0, 5.7)
        }
    }
}

def get_patient_overview(df):
    patient_info = data["patient"]
    return html.Div([
        html.H1(f"{patient_info['name']}", className="mb-3"),
        html.H3(f"Age: {patient_info['age']} years", className="mb-2"),
        html.H3(f"Date: {patient_info['date']}", className="mb-2"),
    ])

def get_date_range_selector(df):
    return dcc.DatePickerRange(
        id='date-range',
        min_date_allowed=df["Date"].min(),
        max_date_allowed=df["Date"].max(),
        start_date=df["Date"].min(),
        end_date=df["Date"].max(),
        display_format='YYYY-MM-DD'
    )

def get_main_timeseries(df, start_date, end_date):
    filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    traces = []
    for biomarker in df["Biomarker"].unique():
        biomarker_data = filtered[filtered["Biomarker"] == biomarker]
        traces.append(go.Scatter(
            x=biomarker_data["Date"],
            y=biomarker_data["Value"],
            mode='lines+markers',
            name=biomarker
        ))
    fig = go.Figure(traces)
    fig.update_layout(title="Biomarker Trends", xaxis_title="Date", yaxis_title="Value", hovermode="x unified")
    return dcc.Graph(figure=fig)

def get_biomarker_cards(df):
    cards = []
    for biomarker in df["Biomarker"].unique():
        biomarker_data = df[df["Biomarker"] == biomarker].iloc[-1]
        cards.append(
            dbc.Card([
                dbc.CardHeader(biomarker),
                dbc.CardBody([
                    html.H5(f"{biomarker_data['Value']} {biomarker_data['Unit']}", className="card-title"),
                    html.P(f"Reference Range: {biomarker_data['Reference Range']}", className="card-text")
                ])
            ], className="mb-2")
        )
    return dbc.Stack(cards, gap=2)

def get_footer(df):
    interpretations = []
    for biomarker in df["Biomarker"].unique():
        biomarker_data = df[df["Biomarker"] == biomarker].iloc[-1]
        value = biomarker_data["Value"]
        low = biomarker_data["Low"]
        high = biomarker_data["High"]
        status = "Normal"
        if value < low:
            status = "Low"
        elif value > high:
            status = "High"
        interpretations.append(f"{biomarker}: {value} {biomarker_data['Unit']} ({status})")
    
    return html.Div([
        html.Hr(),
        html.H5("Clinical Interpretations & Recommendations"),
        html.Ul([html.Li(i) for i in interpretations])
    ])

# App setup
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

header = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Biomarker Analytics Dashboard", className="text-white mb-0"),
                html.P("Track and analyze patient biomarker trends", className="text-white-50 mb-0")
            ])
        ], align="center", className="flex-nowrap")
    ]),
    color="primary", dark=True, className="mb-4"
)

footer = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.P("© 2024 Biomarker Analytics. All rights reserved.", className="text-white-50 mb-0"),
                html.P("For medical professionals only", className="text-white-50 mb-0")
            ])
        ])
    ]),
    color="primary", dark=True, className="mt-4"
)

app.layout = dbc.Container([
    header,

    dbc.Row([
        dbc.Col(get_patient_overview(df), width=12, md=8, className="mb-4"),
        dbc.Col(get_date_range_selector(df), width=12, md=4, className="mb-4")
    ]),

    dbc.Row([
        dbc.Col(
            dcc.Loading(id="main-timeseries-loading", children=[
                html.Div(id="main-timeseries")
            ]),
            width=12, md=8,
            className="mb-4 mobile-full"
        ),
        dbc.Col(
            get_biomarker_cards(df),
            width=12, md=4,
            className="mb-4 mobile-full"
        )
    ]),

    dbc.Row([
        dbc.Col(get_footer(df), width=12)
    ]),

    footer
], fluid=True, className="px-0")

@app.callback(
    Output("main-timeseries", "children"),
    [Input("date-range", "start_date"),
     Input("date-range", "end_date")]
)
def update_main_timeseries(start_date, end_date):
    return get_main_timeseries(df, start_date, end_date)

if __name__ == "__main__":
    app.run(debug=True)

