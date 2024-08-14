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

#Aggregation of monetary aggregates per month

def request_money_data(id_variable):
    # API Parameters for Base Money BCRA API endpoint
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)

    # Requesting the base money data from the BCRA API and cleaning the resulting dataframe
    df = request_bcra(id_variable,start_date,end_date)

    df.drop('idVariable',axis=1,inplace=True)

    df['fecha'] = pd.to_datetime(df['fecha'])

    df.set_index('fecha', inplace=True)

    return df

def monthly_variation(df):
    # Resample to get the last value of each month
    monthly_df = df.resample('ME').mean()

    # Calculate the percentage variation month-over-month
    monthly_df['monthly_variation'] = monthly_df['valor'].pct_change()

    monthly_df.reset_index(inplace=True)

    monthly_df =  monthly_df[1:]

    monthly_df['fecha'] = monthly_df['fecha'] - timedelta(days = 28)

    return monthly_df

monthly_deposits = monthly_variation(request_money_data(21))
monthly_base_money = monthly_variation(request_money_data(15))


base_money = request_money_data(15)
deposits = request_money_data(21)

m2 = base_money.join(deposits, how='inner', lsuffix='_base_money', rsuffix= '_deposits')

m2['valor'] = m2['valor_base_money'] + m2['valor_deposits']

m2 = m2[['valor']]

monthly_m2 = monthly_variation(m2)

# Combine both DataFrames
combined_df = pd.concat([
    monthly_base_money.assign(type='Base Money'),
    monthly_deposits.assign(type='Bank Deposits'),
    monthly_m2.assign(type='M2')
])


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


# Create the bar graph with specified colors
money_agg = px.bar(
    combined_df,
    x='fecha',
    y='monthly_variation',
    color='type',  # This distinguishes between Base Money, M2, and Deposits
    title='Base Money, M2, and Deposits - Monthly Var %',
    labels={'fecha': 'Date', 'monthly_variation': 'Var %'},
    barmode='group',  # Groups the bars side by side
    color_discrete_map={
        'Base Money': '#5A6ACF',
        'M2': '#737B8B',
        'Bank Deposits': '#E6E8EC'
    }
)

# Determine the y-axis range to include all values, including negative ones
y_min = combined_df['monthly_variation'].min() - 0.05
y_max = combined_df['monthly_variation'].max() + 0.05

# Update layout to add padding between bars and remove borders
money_agg.update_layout(
    font=dict(
        family="Poppins, sans-serif"
    ),
    title=dict(
        text="Base Money, M2, and Deposits - Monthly Var %",
        yanchor='top',
        xanchor='left',
        y = 0.98
    ),
    margin=dict(t=100),
    legend=dict(
        title="Concepts",
        title_font=dict(size=9, color="gray"),
        orientation="v",
        yanchor="top",
        y=1.3,
        xanchor="left",
        x=0
    ),
    xaxis_title=None,
    yaxis_title=None,
    yaxis_tickformat=',.1%',
    plot_bgcolor='white',
    bargroupgap=0.2,
    xaxis=dict(
        tickfont=dict(color='#737B8B'),
        showgrid=False,
        zeroline=False,
        rangeslider=dict(
            visible=True,
            thickness=0.005,
            bordercolor="lightgrey",
            borderwidth=1
                         ),
        rangeselector=dict(
            yanchor="top",
            xanchor="left",
            x = 0.7,
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
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

# Remove borders from bars by setting line width to 0
money_agg.update_traces(marker=dict(line=dict(width=0)),hovertemplate='<b>Date:</b> %{x|%b %Y}<br><b>Monthly Var%:</b> %{y:.1%}<extra></extra>')

# Create the Inflation graph

# Create the Inflation graph and name "Nivel general" as "Total"
inflation = px.line(ipc, x='Fecha', y='Nivel general', title='Inflation',
                    labels={'Fecha': 'Date', 'Nivel general': 'Inflation %'})

# Update the name of "Nivel general" to "Total"
inflation.update_traces(mode='lines',name='Total', line=dict(color='#5A6ACF'))

# Add traces for "Nucleo", "Estacional", and "Regulados"
inflation.add_traces([
    dict(x=ipc['Fecha'], y=ipc['Núcleo'], mode='lines', name='Core', line=dict(color='#737B8B')),
    dict(x=ipc['Fecha'], y=ipc['Estacional'], mode='lines', name='Seasonal', line=dict(color='#CDCFD2')),
    dict(x=ipc['Fecha'], y=ipc['Regulados'], mode='lines', name='Regulated', line=dict(color='#86AAFF'))
])

# Ensure all traces are visible in the legend
for trace in inflation.data:
    trace.showlegend = True
    trace.hovertemplate = '<b>Date:</b> %{x|%b %Y}<br><b>Monthly Inflation%:</b> %{y:.1%}<extra></extra>'
    trace.visible = 'legendonly' if trace.name != 'Total' else True

# Determine y-axis range
y_min = min(ipc[['Nivel general', 'Núcleo', 'Estacional', 'Regulados']].min()) - 0.05
y_max = max(ipc[['Nivel general', 'Núcleo', 'Estacional', 'Regulados']].max()) + 0.05

end_date = ipc['Fecha'].max()
start_date = end_date - timedelta(days=6*30)

# Update layout
inflation.update_layout(
    font=dict(
        family="Poppins, sans-serif"
    ),
    xaxis_title=None,
    yaxis_title=None,
    yaxis_tickformat=',.1%',
    plot_bgcolor='white',
    xaxis=dict(
        range=[start_date, end_date],
        tickfont=dict(color='#737B8B'),
        showgrid=False,
        zeroline=False,
        rangeslider=dict(
            visible=True,
            thickness=0.005,
            bordercolor="lightgrey",
            borderwidth=1
        ),
        rangeselector=dict(
            yanchor="top",
            xanchor="left",
            x = 0.7,
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
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
    ),
    legend=dict(
        x=-0,  # Adjust this to place the legend at the left margin
        y=1.1,
        xanchor='left',
        yanchor='top',
        title=None,  # Optionally remove the legend title
        orientation="h"
    )
)





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
            figure=money_agg
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