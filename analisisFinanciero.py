from dash import Dash, dcc, html, dash_table, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import numpy as np

app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

app.layout = dbc.Container([
    html.H1("Análisis de Acciones en Tiempo Real", className="text-center"),
    html.H4("Introduzca el símbolo del ticker, el monto de inversión, elija el tipo de media móvil y el tamaño de la ventana, luego haga clic en 'Descargar y Analizar'", className="text-center"),
    dbc.Row([
        dbc.Col([
            dbc.Label("Símbolo del Ticker:"),
            dcc.Input(id='ticker-input', type='text', value='AAPL', className="form-control"),
            dbc.Label("Monto de inversión ($):"),
            dcc.Input(id='investment-input', type='number', value=1000, className="form-control"),
            dbc.Label("Tamaño de la ventana para SMA y EMA:"),
            dcc.Input(id='window-input', type='number', value=20, className="form-control"),
            dbc.Label("Tipo de Media Móvil:"),
            dcc.Dropdown(
                id='ma-type',
                options=[
                    {'label': 'SMA', 'value': 'SMA'},
                    {'label': 'EMA', 'value': 'EMA'}
                ],
                value='SMA'
            ),
            dbc.Button('Descargar y Analizar', id='analyze-button', color="primary", className="mt-2", n_clicks=0),
            dbc.Button('Restablecer', id='reset-button', color="danger", className="mt-2 ml-2", n_clicks=0)
        ], width=4),
        dbc.Col([
            dcc.Graph(id='stock-graph'),
            dcc.Graph(id='candlestick-graph')
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            html.H2("Resumen de los datos", className="text-center"),
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in ['Metric', 'Value']],
                data=[],
            )
        ])
    ]),
], fluid=True)


@app.callback(
    [Output('stock-graph', 'figure'),
     Output('candlestick-graph', 'figure'),
     Output('table', 'data')],
    [Input('analyze-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    [State('ticker-input', 'value'),
     State('investment-input', 'value'),
     State('window-input', 'value'),
     State('ma-type', 'value')]
)
def update_graph(analyze_clicks, reset_clicks, ticker, investment, window_size, ma_type):
    ctx = callback_context
    if not ctx.triggered:
        return go.Figure(), go.Figure(), []
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'analyze-button' and analyze_clicks > 0:
        ticker = yf.Ticker(ticker).info['symbol']
        data = yf.download(ticker, start='2020-01-01', end='2023-12-31')
        data['SMA'] = data['Close'].rolling(window=int(window_size)).mean()
        data['EMA'] = data['Close'].ewm(span=int(window_size), adjust=False).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'))
        fig.add_trace(go.Scatter(x=data.index, y=data[ma_type], mode='lines', name=ma_type))
        fig.update_layout(autosize=True, margin=dict(l=20, r=20, t=20, b=20), title=f"Gráfico de precios con {ma_type}")

        fig_candle = go.Figure(data=[go.Candlestick(x=data.index,
                                                    open=data['Open'],
                                                    high=data['High'],
                                                    low=data['Low'],
                                                    close=data['Close'])])
        fig_candle.update_layout(autosize=True, margin=dict(l=20, r=20, t=20, b=20), title="Gráfico de velas")

        metrics = {
            'Cambio del último día (%)': round(((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100, 2),
            'Cambio de los últimos 5 días (%)': round(((data['Close'].iloc[-1] - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100, 2),
            'Cambio de los últimos 30 días (%)': round(((data['Close'].iloc[-1] - data['Close'].iloc[-31]) / data['Close'].iloc[-31]) * 100, 2),
            'Volatilidad (30 días)': round(data['Close'].pct_change().rolling(window=30).std()[(len(data['Close'])-1)] * 100, 2),
            'Volumen promedio (30 días)': round(data['Volume'].rolling(window=30).mean()[(len(data['Volume'])-1)], 2),
            'Retorno total (%)': round(((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100, 2),
            'Rendimiento anualizado compuesto (%)': round((np.power((data['Close'].iloc[-1] / data['Close'].iloc[0]), (1 / ((data.index[-1] - data.index[0]).days / 365.25))) - 1) * 100, 2),
        }

        data['MA'] = data['Close'].rolling(window=int(window_size)).mean()
        metrics['Tendencia'] = 'Alcista' if data['Close'].iloc[-1] > data['MA'].iloc[-1] else 'Bajista'

        # Calculate potential profit for the last 30 days
        data_last_30_days = data[-30:]
        start_price = data_last_30_days['Open'][0]
        end_price = data_last_30_days['Close'][-1]
        shares_bought = investment / start_price
        final_value = shares_bought * end_price
        profit = final_value - investment

        metrics['Profit Last 30 Days ($)'] = round(profit, 2)

        metrics_table = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])

        return fig, fig_candle, metrics_table.to_dict('records')
    elif button_id == 'reset-button' and reset_clicks > 0:
        return go.Figure(), go.Figure(), []


if __name__ == '__main__':
    app.run_server(debug=True)
