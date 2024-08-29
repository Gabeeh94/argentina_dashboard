import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from io import BytesIO

# BCRA API REQUESTS
def request_bcra(id_variable, start_date, end_date):
    base_url = "https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable"
    url = f"{base_url}/{id_variable}/{start_date}/{end_date}"

    response = requests.get(url, verify='bcra-gob-ar.pem')

    if response.status_code == 200:
        data = response.json()
        df_results = pd.DataFrame(data['results'])
        return df_results
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)
        return None

def request_money_data(id_variable):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    df = request_bcra(id_variable, start_date, end_date)
    if df is not None:
        df.drop('idVariable', axis=1, inplace=True)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df.set_index('fecha', inplace=True)
    return df

def monthly_variation(df):
    monthly_df = df.resample('ME').mean()
    monthly_df['monthly_variation'] = monthly_df['valor'].pct_change()
    monthly_df.reset_index(inplace=True)
    monthly_df = monthly_df[1:]
    monthly_df['fecha'] = monthly_df['fecha'] - timedelta(days=28)
    return monthly_df

def get_combined_data():
    monthly_deposits = monthly_variation(request_money_data(21))
    monthly_base_money = monthly_variation(request_money_data(15))

    base_money = request_money_data(15)
    deposits = request_money_data(21)

    m2 = base_money.join(deposits, how='inner', lsuffix='_base_money', rsuffix='_deposits')
    m2['valor'] = m2['valor_base_money'] + m2['valor_deposits']
    m2 = m2[['valor']]

    monthly_m2 = monthly_variation(m2)

    combined_df = pd.concat([
        monthly_base_money.assign(type='Base Money'),
        monthly_deposits.assign(type='Bank Deposits'),
        monthly_m2.assign(type='M2')
    ])

    return combined_df

def get_policy_rate_data():
    id_variable = 6
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    policy_rate_df = request_bcra(id_variable, start_date, end_date)
    policy_rate_df.drop('idVariable', axis=1, inplace=True)

    policy_rate = policy_rate_df['valor'].iloc[-1]
    monthly_policy_rate = str(round(policy_rate / 12, 2)) + '%'

    return policy_rate, monthly_policy_rate

def get_rem_data(policy_rate):
    id_variable = 29
    end_date = datetime.today().replace(day=1) - relativedelta(days=1)
    start_date = end_date - timedelta(days=10)

    rem_12_month = request_bcra(id_variable, start_date, end_date)

    if not isinstance(rem_12_month, pd.DataFrame):
        end_date = (datetime.today().replace(day=1) - relativedelta(months=1)).replace(day=1) - relativedelta(days=1)
        start_date = end_date - timedelta(days=10)
        rem_12_month = request_bcra(id_variable, start_date, end_date)

    rem_12_month.drop('idVariable', axis=1, inplace=True)
    rem_12_month_value = rem_12_month['valor'].iloc[-1]
    real_policy_rate = round(policy_rate - rem_12_month_value, 2)

    return str(rem_12_month_value) + '%', str(real_policy_rate) + '%'

def get_dollar_data():
    id_variable = 4
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    min_official_dollar = request_bcra(id_variable, start_date, end_date)
    min_official_dollar.drop('idVariable', axis=1, inplace=True)

    return min_official_dollar['valor'].iloc[-1]

def get_dollar_future():
    prior_month = datetime.now().date().month - 1
    current_year = datetime.now().date().year
    month_str = (datetime(current_year, prior_month, 1)).strftime("%b").upper()
    next_year = str(current_year + 1)[2:]
    prior_month_next_year = month_str + next_year

    current_day = str(datetime.now().date())
    url = f"https://rofex.primary.ventures/api/v2/series/securities/rx_DDF_DLR_{prior_month_next_year}?resolution=1&from={current_day}T13%3A00%3A00.000Z&to={current_day}T21%3A00%3A00.000Z"
    response = requests.get(url)
    data = response.json()

    results = data['series']
    for days_prior in range(1, 10):
        if results:
            break
        else:
            date = str(datetime.now().date() - timedelta(days=days_prior))
            url = f"https://rofex.primary.ventures/api/v2/series/securities/rx_DDF_DLR_{prior_month_next_year}?resolution=1&from={date}T13%3A00%3A00.000Z&to={date}T21%3A00%3A00.000Z"
            response = requests.get(url)
            data = response.json()
            results = data['series']

    dollar_future = pd.DataFrame(results)
    return dollar_future['c'][0] if not dollar_future.empty else None

def calculate_exp_dev_adj_rate(min_official_dollar, dollar_future, policy_rate):
    expected_devaluation = min_official_dollar / dollar_future * 100
    exp_dev_adj_rate = round(policy_rate - expected_devaluation, 2)
    return str(exp_dev_adj_rate) + '%'

def get_inflation_data():
    url = "https://www.indec.gob.ar/Nivel4/Tema/3/5/31"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    link_tag = soup.find("a", class_="a-color2", href=True, target="_blank")

    if link_tag:
        ipc_file_href = link_tag.get('href')
    else:
        print("Link not found")
        return None

    url = "https://www.indec.gob.ar" + ipc_file_href
    response = requests.get(url)
    data = BytesIO(response.content)

    ipc = pd.read_excel(data)
    ipc = ipc.iloc[4:34].transpose().reset_index(drop=True)
    ipc.columns = ipc.iloc[0]
    ipc = ipc[1:]
    ipc.dropna(axis=1, how='all', inplace=True)
    ipc.rename(columns={'Total nacional': 'Fecha'}, inplace=True)
    columns_to_divide = ipc.columns[ipc.columns != 'Fecha']
    ipc[columns_to_divide] = ipc[columns_to_divide] / 100

    return ipc
