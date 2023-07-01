import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import numpy as np

st.title("Análisis de Acciones en Tiempo Real")
st.markdown("Introduzca el símbolo del ticker, el monto de inversión, elija el tipo de media móvil y el tamaño de la ventana, luego haga clic en 'Descargar y Analizar'")

ticker = st.text_input("Símbolo del Ticker:", "AAPL")
investment = st.number_input("Monto de inversión ($):", value=1000)
window_size = st.number_input("Tamaño de la ventana para SMA y EMA:", value=20)
ma_type = st.selectbox("Tipo de Media Móvil:", options=['SMA', 'EMA'], index=0)

analyze_button = st.button('Descargar y Analizar')
reset_button = st.button('Restablecer')

if analyze_button:
    ticker_info = yf.Ticker(ticker).info
    ticker = ticker_info['symbol']
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

    st.plotly_chart(fig)
    st.plotly_chart(fig_candle)
    st.subheader("Resumen de los datos")
    st.dataframe(metrics_table)
elif reset_button:
    st.empty()
