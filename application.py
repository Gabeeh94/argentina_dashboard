# Importing libraries

import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import dash
from dash import html
from dash import dcc
import plotly.express as px
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
from IPython.display import display, HTML



#BCRA API REQUESTS



# Define BCRA API request function

def request_bcra(id_variable,start_date,end_date):
    
    base_url = "https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable"

    url = f"{base_url}/{id_variable}/{start_date}/{end_date}"

    response = requests.get(url, verify = 'bcra-gob-ar.pem')  # Set verify=False to ignore SSL verification CHANGE

    if response.status_code == 200:

        data = response.json()

        results = data['results']

        df_results = pd.DataFrame(results)
        
        return df_results

    else:
        # Print the complete error message
        print(f"Request failed with status code {response.status_code}")
        print(response.text)



# API Parameters for Base Money BCRA API endpoint

id_variable = 15
end_date = datetime.now().date()
start_date = end_date - timedelta(days=365)

# Requesting the base money data from the BCRA API and cleaning the resulting dataframe
base_money = request_bcra(id_variable,start_date,end_date)

base_money.drop('idVariable',axis=1,inplace=True)

base_money['fecha'] = pd.to_datetime(base_money['fecha'])

base_money.set_index('fecha', inplace=True)

# Resample to get the last value of each month
monthly_base_money = base_money.resample('ME').last()

# Calculate the percentage variation month-over-month
monthly_base_money['monthly_variation'] = monthly_base_money['valor'].pct_change()

monthly_base_money.reset_index(inplace=True)

monthly_base_money =  monthly_base_money[1:]



# API Parameters for Nominal Monetary Policy Rate BCRA API endpoint

id_variable = 6
end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

# Requesting the policy rate data from the BCRA API and cleaning the resulting dataframe

policy_rate = request_bcra(id_variable, start_date, end_date)

policy_rate.drop('idVariable',axis=1,inplace=True)

policy_rate = policy_rate['valor'].iloc[-1]

monthly_policy_rate = str(round(policy_rate/12, 2)) + '%'



# API Parameters for REM expected inflation BCRA API endpoint

id_variable = 29
end_date = datetime.today().replace(day=1) - relativedelta(days=1) #Get the last day of the prior month (publication dates for the data)
start_date = end_date - timedelta(days=10)

# Requesting the REM data from the BCRA API and cleaning the resulting dataframe

rem_12_month = request_bcra(id_variable, start_date, end_date)

if isinstance(rem_12_month, pd.DataFrame):
    pass
else:
    # In case the request fails, try with the prior month as it could be the case the data for last month was not published yet
    end_date = (datetime.today().replace(day=1) - relativedelta(months=1)).replace(day=1) - relativedelta(days=1)
    start_date = end_date - timedelta(days=10)
    rem_12_month = request_bcra(id_variable, start_date, end_date)



rem_12_month.drop('idVariable',axis=1,inplace=True)

rem_12_month = rem_12_month['valor'].iloc[-1]

# Substract the rem to the annual nominal policy rate to get the expected inflation adjusted or "real" policy rate

real_policy_rate = round(policy_rate - rem_12_month,2)

rem_12_month = str(rem_12_month) + '%'

real_policy_rate = str(real_policy_rate) + '%'



# API endpoint and parameters for the retail dollar exchange rate BCRA API endpoint

id_variable = 4
end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

min_official_dollar = request_bcra(id_variable, start_date, end_date)

min_official_dollar.drop('idVariable',axis=1,inplace=True)

min_official_dollar = min_official_dollar['valor'].iloc[-1]






# MATBA ROFEX API REQUESTS


# Getting the prior month of the next year and refactoring the format to pass it as a request to the MATBA-ROFEX API

prior_month = datetime.now().date().month - 1

current_year = datetime.now().date().year

month_str = (datetime(current_year,prior_month,1)).strftime("%b").upper()

next_year = str(current_year + 1)[2:]

prior_month_next_year = month_str + next_year

current_day = str(datetime.now().date())

# Creating the URL to request the MATBA ROFEX API
url = "https://rofex.primary.ventures/api/v2/series/securities/rx_DDF_DLR_" + prior_month_next_year + "?resolution=1&from=" + current_day + "T13%3A00%3A00.000Z&to=" + current_day + "T21%3A00%3A00.000Z"

response = requests.get(url)

data = response.json()

results = data['series']

# As data might not be available at times the market is closed (like weekends) we might have to retry with different dates to get a valid repsonse
for days_prior in range(1,10):
    if results != []:
        break
    else:
        # Creating the URL to request the MATBA ROFEX API
        date = str(datetime.now().date() - timedelta(days=days_prior))

        url = "https://rofex.primary.ventures/api/v2/series/securities/rx_DDF_DLR_" + prior_month_next_year + "?resolution=1&from=" + date + "T13%3A00%3A00.000Z&to=" + date + "T21%3A00%3A00.000Z"

        response = requests.get(url)

        data = response.json()

        results = data['series']


dollar_future = pd.DataFrame(results)

dollar_future = dollar_future['c'][0]

# Calculate the expected devaluation rate and then adjust the policy rate to that expected devaluation rate

expected_devaluation = min_official_dollar/dollar_future*100

exp_dev_adj_rate = round(policy_rate - expected_devaluation,2)

exp_dev_adj_rate = str(exp_dev_adj_rate) + '%'





# INDEC DATA 

# Get inflation data from the INDEC

url = "https://www.indec.gob.ar/Nivel4/Tema/3/5/31"

response = requests.get(url)

# Parse the HTML content of the page
soup = BeautifulSoup(response.content, 'html.parser')

# Find the specific <a> tag by its class and partial href
link_tag = soup.find("a", class_="a-color2", href=True, target="_blank")

# Get the href attribute
if link_tag:
    ipc_file_href = link_tag.get('href')
else:
    print("Link not found")
url = "https://www.indec.gob.ar" + ipc_file_href

response = requests.get(url)

data = BytesIO(response.content)

# Clean the resulting dataframe

ipc = pd.read_excel(data)

ipc = ipc.iloc[4:34]

ipc = ipc.transpose()

ipc.reset_index(inplace=True,drop=True)

ipc.columns = ipc.iloc[0]

ipc = ipc[1:]

ipc.dropna(axis=1, how='all', inplace=True)

ipc.rename(columns={'Total nacional': 'Fecha'}, inplace=True)

columns_to_divide = ipc.columns[ipc.columns != 'Fecha']

ipc[columns_to_divide] = ipc[columns_to_divide] / 100




# GRAPHS



# Inject HTML to load Poppins font from Google Fonts

display(HTML("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
"""))


# Create the Base Money graph 

base_money = px.bar(monthly_base_money, x='fecha', y='monthly_variation', title='Base Money - Monthly Var % ',
                    labels={'fecha': 'Date', 'monthly_variation': 'Var %'})

# Determine the y-axis range to include all values, including negative ones
y_min = min(monthly_base_money['monthly_variation']) - 0.05
y_max = max(monthly_base_money['monthly_variation']) + 0.05

base_money.update_layout(
    font = dict(
        family = "Poppins, sans-serif"
    ),
    xaxis_title=None,
    yaxis_title=None,
    yaxis_tickformat=',.1%',
    plot_bgcolor='white',
    xaxis=dict(
        tickfont=dict(color='#737B8B'),
        showgrid=False,
        zeroline=False
    ),
    yaxis=dict(
        range=[y_min, y_max],
        tickfont=dict(color='#737B8B'),
        showgrid=True,
        gridcolor='lightgrey',
        gridwidth=1,
        griddash='dash',
        zeroline=True,
        zerolinecolor='lightgrey',
        ticksuffix="  "
    )
)

# Update bar color
base_money.update_traces(marker_color='#5A6ACF')


# Create the Inflation graph

inflation = px.line(ipc, x='Fecha', y='Nivel general', title='Inflation',
                    labels={'Fecha': 'Date', 'Nivel general': 'Inflation %'})

y_min = min(ipc['Nivel general']) - 0.05
y_max = max(ipc['Nivel general']) + 0.05

inflation.update_layout(
    font = dict(
        family = "Poppins, sans-serif"
    ),
    xaxis_title=None,
    yaxis_title=None,
    yaxis_tickformat=',.1%',
    plot_bgcolor='white',
    xaxis=dict(
        tickfont=dict(color='#737B8B'),
        showgrid=False,
        zeroline=False
    ),
    yaxis=dict(
        range=[y_min, y_max],
        tickfont=dict(color='#737B8B'),
        showgrid=True,
        gridcolor='lightgrey',
        gridwidth=1,
        griddash='dash',
        zeroline=True,
        zerolinecolor='lightgrey',
        ticksuffix="  "
    )
)

inflation.update_traces(line=dict(color='#5A6ACF'))





# DASH APP


app = dash.Dash(__name__)
application = app.server

# Define styles for consistent formatting

h4_style = {
    'textAlign': 'center',
    'margin': '2px 0px 2px 0px',
    'marginBottom': '1px',
    'fontFamily': 'Poppins, sans-serif',
    'fontSize': '14px',
    'fontWeight': '300',
    'padding': '0 5px',
    'color': 'white',
    'zIndex': '2',
    'position': 'relative'
}

p_style = {
    'textAlign': 'center',
    'padding': '2px 10px',
    'marginBottom': '1px',
    'fontFamily': 'Poppins, sans-serif',
    'fontSize': '38px',
    'fontWeight': '300',
    'color': 'white',
    'zIndex': '2',
    'position': 'relative'
}

div_style = {
    'textAlign': 'center',
    'marginBottom': '120px',
    'position': 'relative'
}

circle_style = {
    'position': 'absolute',
    'width': '170px',
    'height': '170px',
    'background-color': 'rgba(100, 99, 214, 0.8)',
    'border-radius': '50%',
    'top': '-30px',
    'bottom' : '5px',
    'left': '50%',
    'transform': 'translateX(-50%)',
    'zIndex': '1'
}

# Layout of the app

app.layout = html.Div(style={'backgroundColor': 'white'}, children=[
    html.Link(
        rel='stylesheet',
        href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap'
    ),
    html.Div(style={'width': '65%', 'display': 'inline-block', 'paddingRight': '20px', 'fontFamily': 'Poppins, sans-serif', 'marginRight': '5%'}, children=[
        dcc.Graph(
            id='base-money',
            figure=base_money
        ),
        dcc.Graph(
            id='inflation-graph',
            figure=inflation
        )
    ]),
    html.Div(style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}, children=[
        html.Div(style=div_style, children=[
            html.P(f'{monthly_policy_rate}', style=p_style),
            html.Div(style=circle_style),
            html.H4(['Monthly Nominal', html.Br(),'Policy Rate'], style=h4_style)
        ]),
        html.Div(style=div_style, children=[
            html.P(f'{rem_12_month}', style=p_style),
            html.Div(style=circle_style),
            html.H4(['Expected Inflation', html.Br(),'Next 12 Months'], style=h4_style)
        ]),
        html.Div(style=div_style, children=[
            html.P(f'{real_policy_rate}', style=p_style),
            html.Div(style=circle_style),
            html.H4(['Exp. Inflation Adjusted', html.Br(), 'Policy Rate'], style=h4_style)
        ]),
        html.Div(style={'textAlign': 'center','position': 'relative'}, children=[
            html.P(f'{exp_dev_adj_rate}', style=p_style),
            html.Div(style=circle_style),
            html.H4(['Devaluation adjusted', html.Br(), 'Policy Rate'], style=h4_style)
        ]),
    ]),
])

if __name__=='__main__':
    application.run(host='0.0.0.0', port='8080')