from dash import html, dcc
import plotly.express as px
from datetime import timedelta
from backend import (
    get_combined_data, get_inflation_data, get_policy_rate_data, 
    get_rem_data, get_dollar_data, get_dollar_future, calculate_exp_dev_adj_rate
)

def create_layout():
    combined_df = get_combined_data()
    ipc = get_inflation_data()

    policy_rate, monthly_policy_rate = get_policy_rate_data()
    rem_12_month, real_policy_rate = get_rem_data(policy_rate)
    min_official_dollar = get_dollar_data()
    dollar_future = get_dollar_future()

    if min_official_dollar is not None and dollar_future is not None:
        exp_dev_adj_rate = calculate_exp_dev_adj_rate(min_official_dollar, dollar_future, policy_rate)
    else:
        exp_dev_adj_rate = "N/A"  

    money_agg = create_money_agg_graph(combined_df)
    inflation = create_inflation_graph(ipc)

    return html.Div(className='main-container', children=[
        html.Link(
            rel='stylesheet',
            href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap'
        ),
        html.Div(className='sidebar', children=[
            html.Div(className='logo-container', children=[
                html.Img(src='/assets/logo.png', className='logo'),  
                html.H2("Argentina KPIs", className='logo-text')
            ]),
            html.Div(className='menu-section', children=[
                html.H4("Dashboards", className='menu-title'),
                html.Ul(className='menu-list', children=[
                    html.Li(html.A("Money", href="#", className='menu-item active')),
                    html.Li(html.A("Fiscal (WIP)", href="#", className='menu-item')),
                    html.Li(html.A("Financial (WIP)", href="#", className='menu-item')),
                    html.Li(html.A("Real Economy (WIP)", href="#", className='menu-item')),
                ]),
                html.H4("Menu", className='menu-title'),
                html.Ul(className='menu-list', children=[
                    html.Li(html.A("Methodology", href="#", className='menu-item')),
                    html.Li(html.A("Donations", href="#", className='menu-item')),
                ])
            ])
        ]),
        html.Div(className='content-container', children=[
            dcc.Graph(
                id='base-money',
                figure=money_agg,
                className='dash-graph'
            ),
            dcc.Graph(
                id='inflation-graph',
                figure=inflation,
                className='dash-graph'
            )
        ]),
        html.Div(className='sidebar-right', children=[
            html.Div(className='stat-container', children=[
                html.P(f'{monthly_policy_rate}', className='stat-value'),
                html.H4(['Monthly Nominal', html.Br(), 'Policy Rate'], className='stat-title')
            ]),
            html.Div(className='stat-container', children=[
                html.P(f'{rem_12_month}', className='stat-value'),
                html.H4(['Expected Inflation', html.Br(), 'Next 12 Months'], className='stat-title')
            ]),
            html.Div(className='stat-container', children=[
                html.P(f'{real_policy_rate}', className='stat-value'),
                html.H4(['Exp. Inflation Adjusted', html.Br(), 'Policy Rate'], className='stat-title')
            ]),
            html.Div(className='stat-container', children=[
                html.P(f'{exp_dev_adj_rate}', className='stat-value'),
                html.H4(['Devaluation adjusted', html.Br(), 'Policy Rate'], className='stat-title')
            ]),
        ]),
    ])

def create_money_agg_graph(combined_df):
    money_agg = px.bar(
        combined_df,
        x='fecha',
        y='monthly_variation',
        color='type',
        title='Base Money, M2, and Deposits - Monthly Var %',
        labels={'fecha': 'Date', 'monthly_variation': 'Var %'},
        barmode='group',
        color_discrete_map={
            'Base Money': '#5A6ACF',
            'M2': '#737B8B',
            'Bank Deposits': '#E6E8EC'
        }
    )
    y_min = combined_df['monthly_variation'].min() - 0.05
    y_max = combined_df['monthly_variation'].max() + 0.05

    money_agg.update_layout(
        font=dict(
            family="Poppins, sans-serif"
        ),
        title=dict(
            text="Base Money, M2, and Deposits - Monthly Var %",
            yanchor='top',
            xanchor='left',
            y=0.98
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
                x=0.7,
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

    money_agg.update_traces(marker=dict(line=dict(width=0)), hovertemplate='<b>Date:</b> %{x|%b %Y}<br><b>Monthly Var%:</b> %{y:.1%}<extra></extra>')
    return money_agg

def create_inflation_graph(ipc):
    inflation = px.line(ipc, x='Fecha', y='Nivel general', title='Inflation',
                        labels={'Fecha': 'Date', 'Nivel general': 'Inflation %'})

    inflation.update_traces(mode='lines', name='Total', line=dict(color='#5A6ACF'))

    inflation.add_traces([
        dict(x=ipc['Fecha'], y=ipc['Núcleo'], mode='lines', name='Core', line=dict(color='#737B8B')),
        dict(x=ipc['Fecha'], y=ipc['Estacional'], mode='lines', name='Seasonal', line=dict(color='#CDCFD2')),
        dict(x=ipc['Fecha'], y=ipc['Regulados'], mode='lines', name='Regulated', line=dict(color='#86AAFF'))
    ])

    for trace in inflation.data:
        trace.showlegend = True
        trace.hovertemplate = '<b>Date:</b> %{x|%b %Y}<br><b>Monthly Inflation%:</b> %{y:.1%}<extra></extra>'
        trace.visible = 'legendonly' if trace.name != 'Total' else True

    y_min = min(ipc[['Nivel general', 'Núcleo', 'Estacional', 'Regulados']].min()) - 0.05
    y_max = max(ipc[['Nivel general', 'Núcleo', 'Estacional', 'Regulados']].max()) + 0.05

    end_date = ipc['Fecha'].max()
    start_date = end_date - timedelta(days=6 * 30)

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
                x=0.7,
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

    return inflation
