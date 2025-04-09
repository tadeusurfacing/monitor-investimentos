import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk

def atualizar_graficos(frame, df):
    for widget in frame.winfo_children():
        widget.destroy()

    notebook = ttk.Notebook(frame)
    notebook.pack(fill="both", expand=True)

    # Gráfico de Rentabilidade
    frame_rent = ttk.Frame(notebook)
    fig1 = plt.Figure(figsize=(10, 4), dpi=100)
    ax1 = fig1.add_subplot(111)
    df.plot.bar(x='Papel', y='Rentabilidade', ax=ax1)
    ax1.set_title('Rentabilidade por Ativo (%)')
    ax1.tick_params(axis='x', rotation=45)
    canvas1 = FigureCanvasTkAgg(fig1, master=frame_rent)
    canvas1.draw()
    canvas1.get_tk_widget().pack(fill='both', expand=True)
    notebook.add(frame_rent, text="Rentabilidade")

    # Gráfico de Distribuição
    frame_dist = ttk.Frame(notebook)
    fig2 = plt.Figure(figsize=(10, 4), dpi=100)
    ax2 = fig2.add_subplot(111)
    df.plot.pie(y='Valor Atual', labels=df['Papel'], ax=ax2, autopct='%1.1f%%')
    ax2.set_title('Distribuição da Carteira')
    ax2.set_ylabel('')
    canvas2 = FigureCanvasTkAgg(fig2, master=frame_dist)
    canvas2.draw()
    canvas2.get_tk_widget().pack(fill='both', expand=True)
    notebook.add(frame_dist, text="Distribuição")

def atualizar_analise(frame, df):
    for widget in frame.winfo_children():
        widget.destroy()

    total_investido = df["Total Investido"].sum()
    valor_atual = df["Valor Atual"].sum()
    rentabilidade_media = df["Rentabilidade"].mean()
    positivos = df[df["Rentabilidade"] > 0].shape[0]
    negativos = df[df["Rentabilidade"] <= 0].shape[0]
    top_rent = df.sort_values("Rentabilidade", ascending=False).head(3)[["Papel", "Rentabilidade"]]
    top_div = df.sort_values("Dividendos", ascending=False).head(3)[["Papel", "Dividendos"]]

    resumo = f"""📊 ANÁLISE GERAL

💰 Total Investido: R$ {total_investido:,.2f}
📈 Valor Atual: R$ {valor_atual:,.2f}
📊 Rent. Média: {rentabilidade_media:.2f}%
🟢 Positivos: {positivos} | 🔴 Negativos: {negativos}

🥇 Top Rentabilidade:
{top_rent.to_string(index=False)}

💵 Top Dividendos:
{top_div.to_string(index=False)}"""

    tk.Label(frame, text=resumo, justify="left", font=("Courier New", 10)).pack(padx=20, pady=20)
