import yfinance as yf
import matplotlib.pyplot as plt
from fuzzywuzzy import process
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext

class Cartera:
    def __init__(self):
        self.acciones = {}

    def agregar_accion(self, ticker, fecha_compra, precio_compra, cantidad):
        if ticker not in self.acciones:
            self.acciones[ticker] = {
                'fecha_compra': fecha_compra,
                'precio_compra': precio_compra,
                'cantidad': cantidad
            }
            print(f"{ticker} agregado a la cartera.")
        else:
            print(f"{ticker} ya está en la cartera. Considera eliminarlo primero si deseas agregarlo nuevamente.")

    def eliminar_accion(self, ticker):
        if ticker in self.acciones:
            del self.acciones[ticker]
            print(f"{ticker} eliminado de la cartera.")
        else:
            print(f"{ticker} no se encuentra en la cartera.")

    def rendimiento_cartera(self):
        rendimiento_total = 0
        for ticker, detalles in self.acciones.items():
            try:
                stock = yf.Ticker(ticker)
                precio_actual = stock.history(period="1d")['Close'][0]
                rendimiento = (precio_actual - detalles['precio_compra']) * detalles['cantidad']
                rendimiento_total += rendimiento
                print(f"Rendimiento de {ticker}: ${rendimiento:.2f}")
            except:
                print(f"No se pudo obtener el rendimiento de {ticker}.")
        print(f"Rendimiento total de la cartera: ${rendimiento_total:.2f}")

    def historial_precio(self, ticker, periodo="1y"):
        try:
            stock = yf.Ticker(ticker)
            historical_data = stock.history(period=periodo)
            print(historical_data)
        except:
            print(f"No se pudo obtener el historial de precios de {ticker}.")

    def detalles_accion(self, ticker):
        if ticker in self.acciones:
            detalles = self.acciones[ticker]
            print(f"Detalles de {ticker}:")
            for key, value in detalles.items():
                print(f"{key}: {value}")
        else:
            print(f"{ticker} no se encuentra en la cartera.")
            
    def valor_actual_cartera(self):
        valor_total = 0
        for ticker, detalles in self.acciones.items():
            try:
                stock = yf.Ticker(ticker)
                precio_actual = stock.history(period="1d")['Close'][0]
                valor_total += precio_actual * detalles['cantidad']
            except:
                pass
        return valor_total

    def capital_invertido(self):
        capital = sum([detalles['precio_compra'] * detalles['cantidad'] for detalles in self.acciones.values()])
        return capital

    def rendimiento_global(self):
        return self.valor_actual_cartera() - self.capital_invertido()

def buscar_ticker_por_nombre(nombre):
        tickers = yf.Tickers().tickers
        matches = process.extract(nombre, tickers, limit=5)
        return [match[0] for match in matches]

def interfaz_grafica():
    window = tk.Tk()
    window.title("Gestor de Cartera")
    window.geometry("800x600")

    mi_cartera = Cartera()
    
    def actualizar_lista_acciones():
        lista_acciones.delete(0, tk.END)
        for ticker in mi_cartera.acciones:
            lista_acciones.insert(tk.END, ticker)

    def agregar_accion():
        ticker = simpledialog.askstring("Agregar acción", "Introduce el ticker de la acción:")
        fecha_compra = simpledialog.askstring("Agregar acción", "Introduce la fecha de compra (YYYY-MM-DD):")
        precio_compra = simpledialog.askfloat("Agregar acción", "Introduce el precio de compra:")
        cantidad = simpledialog.askinteger("Agregar acción", "Introduce la cantidad comprada:")
        mi_cartera.agregar_accion(ticker, fecha_compra, precio_compra, cantidad)
        actualizar_lista_acciones()

    def eliminar_accion():
        ticker = lista_acciones.get(lista_acciones.curselection())
        mi_cartera.eliminar_accion(ticker)
        actualizar_lista_acciones()

    def mostrar_rendimiento():
        rendimiento = mi_cartera.rendimiento_global()
        messagebox.showinfo("Rendimiento Global", f"El rendimiento global de la cartera es: ${rendimiento:.2f}")

    def mostrar_grafico_rendimiento():
        tickers = list(mi_cartera.acciones.keys())
        rendimientos = [yf.Ticker(ticker).history(period="1y")['Close'].pct_change().cumsum().iloc[-1] for ticker in tickers]
        
        plt.bar(tickers, rendimientos)
        plt.ylabel('Rendimiento acumulado')
        plt.title('Rendimiento por acción en la cartera')
        plt.show()

    # Widgets
    frame_acciones = ttk.LabelFrame(window, text="Acciones", padding=(10, 5))
    frame_acciones.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    lista_acciones = tk.Listbox(frame_acciones)
    lista_acciones.grid(row=0, column=0, rowspan=4, padx=5, pady=5, sticky="nsew")

    btn_agregar = ttk.Button(frame_acciones, text="Agregar acción", command=agregar_accion)
    btn_eliminar = ttk.Button(frame_acciones, text="Eliminar acción", command=eliminar_accion)
    btn_grafico_rendimiento = ttk.Button(frame_acciones, text="Ver gráfico de rendimiento", command=mostrar_grafico_rendimiento)

    btn_agregar.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    btn_eliminar.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    btn_grafico_rendimiento.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    frame_resumen = ttk.LabelFrame(window, text="Resumen", padding=(10, 5))
    frame_resumen.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    txt_resumen = scrolledtext.ScrolledText(frame_resumen, width=40, height=10)
    txt_resumen.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    def actualizar_resumen():
        txt_resumen.delete(1.0, tk.END)
        txt_resumen.insert(tk.END, f"Capital invertido: ${mi_cartera.capital_invertido():.2f}\n")
        txt_resumen.insert(tk.END, f"Valor actual: ${mi_cartera.valor_actual_cartera():.2f}\n")
        txt_resumen.insert(tk.END, f"Rendimiento global: ${mi_cartera.rendimiento_global():.2f}\n")

    btn_actualizar_resumen = ttk.Button(frame_resumen, text="Actualizar Resumen", command=actualizar_resumen)
    btn_actualizar_resumen.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    window.mainloop()

if __name__ == "__main__":
    interfaz_grafica()