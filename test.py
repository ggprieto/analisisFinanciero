import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from pandas.tseries.offsets import BDay
from datetime import timedelta

st.title("Análisis de Acciones en Tiempo Real")
st.markdown("Introduzca el símbolo del ticker, el monto de inversión, elija el tipo de media móvil y el tamaño de la ventana, luego haga clic en 'Descargar y Analizar'")

ticker = st.text_input("Símbolo del Ticker:", "AAPL")
investment = st.number_input("Monto de inversión ($):", value=1000)
date_selection = st.selectbox("Selección de fecha:", ('Último día', 'Último mes', 'Última semana', 'Último año', 'Rango de fechas'))

# Define la fecha de inicio y fin
start_date, end_date = None, None
if date_selection == 'Último día':
    end_date = pd.datetime.today().date()
    start_date = (end_date - BDay(1)).date()
elif date_selection == 'Último mes':
    end_date = pd.datetime.today().date()
    start_date = (end_date - pd.DateOffset(months=1)).date()
elif date_selection == 'Última semana':
    end_date = pd.datetime.today().date()
    start_date = (end_date - pd.DateOffset(weeks=1)).date()
elif date_selection == 'Último año':
    end_date = pd.datetime.today().date()
    start_date = (end_date - pd.DateOffset(years=1)).date()
else:
    start_date = st.date_input("Fecha de inicio:")
    end_date = st.date_input("Fecha de fin:")

window_size = st.number_input("Tamaño de la ventana para SMA y EMA:", value=20)
ma_type = st.selectbox("Tipo de Media Móvil:", options=['SMA', 'EMA'], index=0)

analyze_button = st.button('Descargar y Analizar')
reset_button = st.button('Restablecer')

if analyze_button:
    ticker_info = yf.Ticker(ticker).info
    ticker = ticker_info['symbol']

    while True:
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            if len(data) == 0:
                raise ValueError("No data available")
            break
        except ValueError:
            end_date = (pd.to_datetime(end_date) - BDay(1)).date()
            if date_selection == 'Último día':
                start_date = (pd.to_datetime(start_date) - BDay(1)).date()

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
    'Volatilidad': round(data['Close'].pct_change().rolling(window=20).std().dropna().iloc[-1] * 100, 2),
    'Volumen promedio': round(data['Volume'].rolling(window=len(data)).mean()[(len(data['Volume'])-1)], 2),
    'Retorno total (%)': round(((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100, 2),
    'Rendimiento anualizado compuesto (%)': round((np.power((data['Close'].iloc[-1] / data['Close'].iloc[0]), (1 / ((data.index[-1] - data.index[0]).days / 365.25))) - 1) * 100, 2),
    }   

    price_summary = {
    'Precio Máximo': round(data['Close'].max(), 2),
    'Precio Mínimo': round(data['Close'].min(), 2),
    'Precio Promedio': round(data['Close'].mean(), 2),
    'Precio Mediano': round(data['Close'].median(), 2)
    }

    data['MA'] = data['Close'].rolling(window=int(window_size)).mean()
    metrics['Tendencia'] = 'Alcista' if data['Close'].iloc[-1] > data['MA'].iloc[-1] else 'Bajista'

    start_price = data['Open'].iloc[0]
    end_price = data['Close'].iloc[-1]
    shares_bought = investment / start_price
    final_value = shares_bought * end_price
    profit = final_value - investment
    profit_percentage = (profit / investment) * 100

    metrics['Profit Selected Range ($)'] = round(profit, 2)
    metrics['Profit Percentage (%)'] = round(profit_percentage, 2)

    # Calculate price estimation for the next 5 periods
    next_periods = 5
    next_dates = pd.bdate_range(start=data.index.max(), periods=next_periods + 1)[1:]
    price_estimations = data[ma_type].values.tolist()[-window_size:]  # Use the last window_size values for the initial estimation

    for i in range(next_periods):
        if ma_type == 'SMA':
            price_estimation = np.mean(price_estimations[-window_size:])
        else:  # EMA
            alpha = 2 / (window_size + 1)
            price_estimation = alpha * price_estimations[-1] + (1 - alpha) * price_estimations[-2]

        price_estimations.append(price_estimation)

    price_estimation_table = pd.DataFrame({'Fecha': next_dates, 'Estimación de Precio': price_estimations[-next_periods:]})

    st.plotly_chart(fig)
    st.plotly_chart(fig_candle)
    st.subheader("Resumen de los Últimos Precios")
    st.dataframe(pd.DataFrame(list(price_summary.items()), columns=['Métrica', 'Valor']))
    st.subheader("Resumen de los datos")
    st.dataframe(pd.DataFrame(list(metrics.items()), columns=['Métrica', 'Valor']))
    st.subheader("Estimación de Precio para los Próximos Períodos")
    st.dataframe(price_estimation_table.style.format({'Estimación de Precio': '{:.2f}'}))
    st.subheader("Profit y Porcentaje de Profit")
    st.write("Profit: $", round(profit, 2))
    st.write("Porcentaje de Profit: ", round(profit_percentage, 2), "%")
elif reset_button:
    st.empty()

