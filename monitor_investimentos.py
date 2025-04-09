import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import yfinance as yf
import threading
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
import matplotlib

matplotlib.use('TkAgg')  # Definir backend antes de importar pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ====================== CONFIGURAÇÃO INICIAL ======================
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            RotatingFileHandler('investimentos.log', maxBytes=1024 * 1024, backupCount=3, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info("Aplicação iniciada")


setup_logging()


# ====================== CLASSE DE CACHE ======================
class CotacaoCache:
    def __init__(self):
        self._cache = {}
        self.CACHE_VALIDADE = timedelta(minutes=30)

    def obter_cotacao(self, ticker):
        agora = datetime.now()
        if ticker in self._cache:
            dados, timestamp = self._cache[ticker]
            if agora - timestamp < self.CACHE_VALIDADE:
                return dados

        try:
            nova_cotacao = self._buscar_yfinance(ticker)
            self._cache[ticker] = (nova_cotacao, agora)
            return nova_cotacao
        except Exception as e:
            logging.warning(f"Falha ao buscar {ticker}: {str(e)}")
            return self._cache.get(ticker, (None, None))[0]

    @staticmethod
    def _buscar_yfinance(ticker):
        try:
            dados = yf.Ticker(ticker).history(period="1d")
            return {
                'preco': round(dados['Close'].iloc[-1], 2),
                'variacao': round(dados['Close'].pct_change().iloc[-1] * 100, 2)
            }
        except Exception as e:
            raise Exception(f"Erro Yahoo Finance para {ticker}: {str(e)}")

    def limpar_cache(self):
        self._cache = {}
        logging.info("Cache limpo")


cache_cotacoes = CotacaoCache()

# ====================== CONFIGURAÇÕES GERAIS ======================
CAMINHO_PLANILHA = "CONTROLE DE ATIVOS.xlsx"
CAMINHO_DADOS = "dados_salvos.json"


# ====================== FUNÇÕES PRINCIPAIS ======================
def carregar_dados():
    try:
        if os.path.exists(CAMINHO_DADOS):
            logging.info(f"Carregando dados de {CAMINHO_DADOS}")
            df = pd.read_json(CAMINHO_DADOS)
        else:
            logging.warning(f"{CAMINHO_DADOS} não encontrado, usando planilha Excel")
            df = pd.read_excel(CAMINHO_PLANILHA, sheet_name="AÇÕES", header=1)
            df = df.dropna(how="all").reset_index(drop=True)
            colunas_renomeadas = {
                "PAPEL": "Papel", "EMPRESA": "Empresa", "P MÉD": "Preço Médio",
                "P ATUAL $": "Preço Atual", "P TETO $": "Preço Teto",
                "TOTAL": "Quantidade", "APORTADO": "Total Investido",
                "ATUAL": "Valor Atual", "TOTAIS": "Dividendos",
                "POR AÇÃO": "Dividendos/Ação", "TOTAL %": "Rentabilidade"
            }
            df = df.rename(columns=colunas_renomeadas)
            df = df[list(colunas_renomeadas.values())].copy()
            df.to_json(CAMINHO_DADOS, orient="records", indent=2)

        logging.info(f"Dados carregados com {len(df)} ativos")
        return df
    except Exception as e:
        logging.critical(f"Falha ao carregar dados: {str(e)}", exc_info=True)
        messagebox.showerror("Erro", f"Falha ao carregar dados:\n{str(e)}")
        raise


def salvar_dados():
    try:
        df.to_json(CAMINHO_DADOS, orient="records", indent=2)
        logging.info("Dados salvos com sucesso")
        messagebox.showinfo("Salvo", "Alterações salvas com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao salvar dados: {str(e)}", exc_info=True)
        messagebox.showerror("Erro", f"Falha ao salvar:\n{str(e)}")


def exportar_pdf():
    try:
        df_exportar = df.copy()
        df_exportar = df_exportar[["Papel", "Empresa", "Preço Médio", "Preço Atual",
                                   "Quantidade", "Total Investido", "Valor Atual",
                                   "Dividendos", "Dividendos/Ação", "Rentabilidade"]]

        pdf_path = "relatorio_acoes.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 800, "Relatório de Ações")

        # Cabeçalho
        c.setFont("Helvetica-Bold", 10)
        headers = df_exportar.columns
        for i, header in enumerate(headers):
            c.drawString(50 + i * 100, 770, header)

        # Dados
        c.setFont("Helvetica", 8)
        y = 750
        for _, row in df_exportar.iterrows():
            for i, val in enumerate(row):
                c.drawString(50 + i * 100, y, str(val))
            y -= 20
            if y < 50:
                c.showPage()
                y = 800

        c.save()
        messagebox.showinfo("Sucesso", f"PDF exportado para:\n{pdf_path}")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao exportar PDF:\n{str(e)}")


def formatar_valores(row):
    row["Preço Médio"] = f"R$ {row['Preço Médio']:.2f}"
    row["Preço Atual"] = f"R$ {row['Preço Atual']:.2f}"
    row["Preço Teto"] = f"R$ {row['Preço Teto']:.2f}"
    row["Total Investido"] = f"R$ {row['Total Investido']:.2f}"
    row["Valor Atual"] = f"R$ {row['Valor Atual']:.2f}"
    row["Dividendos"] = f"R$ {pd.to_numeric(row['Dividendos'], errors='coerce'):.2f}" if pd.notna(
        row['Dividendos']) else "R$ 0.00"
    row["Rentabilidade"] = f"{row['Rentabilidade']:.2f}%"
    row["Dividendos/Ação"] = f"R$ {pd.to_numeric(row['Dividendos/Ação'], errors='coerce'):.2f}" if pd.notna(
        row['Dividendos/Ação']) else "R$ 0.00"
    return row


def atualizar_dados_financeiros(df):
    for idx, row in df.iterrows():
        papel = row["Papel"]
        ticker = f"{papel}.SA" if not str(papel).endswith(".SA") else papel

        try:
            cotacao = cache_cotacoes.obter_cotacao(ticker)
            if cotacao and cotacao['preco']:
                preco_atual = cotacao['preco']
                df.at[idx, "Preço Atual"] = preco_atual
                df.at[idx, "Valor Atual"] = round(row["Quantidade"] * preco_atual, 2)

                if row["Total Investido"] > 0:
                    rentabilidade = ((df.at[idx, "Valor Atual"] - row["Total Investido"]) / row[
                        "Total Investido"]) * 100
                    df.at[idx, "Rentabilidade"] = round(rentabilidade, 2)
        except Exception as e:
            logging.error(f"Erro ao processar {ticker}: {str(e)}")
            continue

    return df


# ====================== INTERFACE GRÁFICA ======================
# Preparar dados
df = carregar_dados()
df = df[df["Papel"].notna()]
for col in ["Preço Médio", "Preço Teto"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').round(2)

df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)
df["Total Investido"] = pd.to_numeric(df["Total Investido"], errors="coerce").fillna(0)
df["Preço Atual"] = np.nan
df["Valor Atual"] = 0
df["Rentabilidade"] = 0.0
df["PT Bazin"] = pd.to_numeric(df["Dividendos/Ação"], errors="coerce") * (100 / 6)
df["PT Bazin"] = df["PT Bazin"].round(2)

# Interface principal
janela = tk.Tk()
janela.title("Monitor de Investimentos")
janela.state('zoomed')

frame_principal = tk.Frame(janela)
frame_principal.pack(fill="both", expand=True)

menu_lateral = tk.Frame(frame_principal, width=200, bg="#1f2937")
menu_lateral.pack(side="left", fill="y")

# Frame para botões de ação
frame_botoes = tk.Frame(menu_lateral, bg="#1f2937")
frame_botoes.pack(side="bottom", fill="x", pady=10)

# Botões de ação
btn_salvar = tk.Button(frame_botoes, text="💾 Salvar", command=salvar_dados,
                       bg="#1f2937", fg="white", relief="flat", font=("Segoe UI", 10))
btn_salvar.pack(fill="x", pady=5)

btn_exportar = tk.Button(frame_botoes, text="📄 Exportar PDF", command=exportar_pdf,
                         bg="#1f2937", fg="white", relief="flat", font=("Segoe UI", 10))
btn_exportar.pack(fill="x", pady=5)

btn_atualizar = tk.Button(frame_botoes, text="🔄 Atualizar Cotações",
                          command=lambda: threading.Thread(target=inicializar_precos, daemon=True).start(),
                          bg="#1f2937", fg="white", relief="flat", font=("Segoe UI", 10))
btn_atualizar.pack(fill="x", pady=5)

conteudo = tk.Frame(frame_principal, bg="white")
conteudo.pack(side="right", fill="both", expand=True)

# Abas simplificadas
botoes_secoes = ["Ações", "Gráficos", "Análise Geral", "Adicionar/Remover"]
frames_secoes = {}

botao_estilo_menu = {
    "anchor": "w",
    "padx": 20,
    "pady": 10,
    "relief": "flat",
    "fg": "white",
    "bg": "#1f2937",
    "activeforeground": "white",
    "bd": 0,
    "font": ("Segoe UI", 10, "bold")
}


def estilo_menu_hover(event, botao, cor="#374151"):
    botao.config(bg=cor)


def estilo_menu_sair(event, botao, cor="#1f2937"):
    botao.config(bg=cor)


# Primeiro cria todos os frames
for nome in botoes_secoes:
    btn = tk.Button(menu_lateral, text=nome, width=20, **botao_estilo_menu,
                    command=lambda n=nome: mostrar_secao(n))
    btn.pack(padx=10, pady=4)
    btn.bind("<Enter>", lambda e, b=btn: estilo_menu_hover(e, b))
    btn.bind("<Leave>", lambda e, b=btn: estilo_menu_sair(e, b))
    frames_secoes[nome] = tk.Frame(conteudo)

# Configuração da tabela
colunas_para_mostrar = ["Papel", "Empresa", "Preço Médio", "Preço Atual",
                        "Quantidade", "Total Investido", "Valor Atual",
                        "Dividendos", "Dividendos/Ação", "Rentabilidade", "PT Bazin"]

tabela_acoes = ttk.Treeview(frames_secoes["Ações"], columns=colunas_para_mostrar,
                            show="headings", selectmode="browse")
for col in colunas_para_mostrar:
    tabela_acoes.heading(col, text=col)
    tabela_acoes.column(col, width=100, anchor="center")

tabela_acoes.tag_configure("positivo", background="#d4edda")
tabela_acoes.tag_configure("negativo", background="#f8d7da")
tabela_acoes.tag_configure("barato", background="#fff3cd")

scroll_y = ttk.Scrollbar(frames_secoes["Ações"], orient="vertical", command=tabela_acoes.yview)
scroll_x = ttk.Scrollbar(frames_secoes["Ações"], orient="horizontal", command=tabela_acoes.xview)
tabela_acoes.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

tabela_acoes.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")


def atualizar_tabela():
    for i in tabela_acoes.get_children():
        tabela_acoes.delete(i)
    df_exibicao = df.apply(formatar_valores, axis=1)
    for idx, row in df_exibicao.iterrows():
        valores = [row[col] for col in colunas_para_mostrar]
        rentabilidade_valor = df.loc[idx, "Rentabilidade"]
        preco_atual = pd.to_numeric(df.loc[idx, "Preço Atual"], errors="coerce")
        pt_bazin = pd.to_numeric(df.loc[idx, "PT Bazin"], errors="coerce")
        if not pd.isna(preco_atual) and not pd.isna(pt_bazin) and preco_atual < pt_bazin:
            tag = "barato"
        else:
            tag = "positivo" if rentabilidade_valor > 0 else "negativo"
        tabela_acoes.insert("", "end", values=valores, tags=(tag,))


def verificar_alertas_bazin():
    oportunidades = []
    for idx, row in df.iterrows():
        preco_atual = pd.to_numeric(row["Preço Atual"], errors="coerce")
        pt_bazin = pd.to_numeric(row["PT Bazin"], errors="coerce")
        if not pd.isna(preco_atual) and not pd.isna(pt_bazin) and preco_atual <= pt_bazin:
            oportunidades.append(f"{row['Papel']} (Atual: R$ {preco_atual:.2f} | Teto Bazin: R$ {pt_bazin:.2f})")
    if oportunidades:
        mensagem = "Atenção! Oportunidades abaixo do PT Bazin:\n\n" + "\n".join(oportunidades)
        janela.after(0, lambda: messagebox.showinfo("Oportunidade", mensagem))


def inicializar_precos():
    def tarefa():
        try:
            global df
            df = atualizar_dados_financeiros(df)
            janela.after(0, atualizar_tabela)
            janela.after(0, verificar_alertas_bazin)
            janela.after(0, lambda: status_var.set("Cotações atualizadas!"))
            logging.info("Cotações atualizadas")
        except Exception as e:
            logging.error(f"Erro ao atualizar cotações: {str(e)}", exc_info=True)
            janela.after(0, lambda: messagebox.showerror("Erro", "Erro ao atualizar dados"))

    threading.Thread(target=tarefa, daemon=True).start()


def mostrar_secao(secao):
    for f in frames_secoes.values():
        f.pack_forget()
    frames_secoes[secao].pack(fill="both", expand=True)
    if secao == "Gráficos":
        atualizar_graficos()
    elif secao == "Análise Geral":
        atualizar_analise()
    elif secao == "Adicionar/Remover":
        montar_aba_edicao()


def atualizar_analise():
    frame = frames_secoes["Análise Geral"]
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


def atualizar_graficos():
    frame = frames_secoes["Gráficos"]
    for widget in frame.winfo_children():
        widget.destroy()

    try:
        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True)

        # Gráfico de Rentabilidade
        frame_rent = ttk.Frame(notebook)
        fig1 = plt.Figure(figsize=(10, 4), dpi=100)
        ax1 = fig1.add_subplot(111)
        df.plot.bar(x='Papel', y='Rentabilidade', ax=ax1, color='skyblue')
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

    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao gerar gráficos:\n{str(e)}")


def montar_aba_edicao():
    frame = frames_secoes["Adicionar/Remover"]
    for widget in frame.winfo_children():
        widget.destroy()

    tk.Label(frame, text="➕ Adicionar Ativo", font=("Segoe UI", 11, "bold")).pack(pady=10)
    form = tk.Frame(frame)
    form.pack(pady=5)

    campos = {
        "Papel": tk.StringVar(),
        "Empresa": tk.StringVar(),
        "Preço Médio": tk.DoubleVar(),
        "Quantidade": tk.IntVar(),
        "Preço Teto": tk.DoubleVar()
    }

    for i, (label, var) in enumerate(campos.items()):
        tk.Label(form, text=label).grid(row=i, column=0, sticky="e", padx=5, pady=2)
        tk.Entry(form, textvariable=var).grid(row=i, column=1, pady=2)

    def adicionar():
        global df
        novo = {k: v.get() for k, v in campos.items()}
        novo["Preço Atual"] = np.nan
        novo["Valor Atual"] = 0
        novo["Total Investido"] = novo["Preço Médio"] * novo["Quantidade"]
        novo["Rentabilidade"] = 0.0
        novo["Dividendos"] = 0.0
        novo["Dividendos/Ação"] = 0.0
        novo["PT Bazin"] = round((novo["Dividendos/Ação"] * 100 / 6), 2)

        df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
        salvar_dados()
        atualizar_tabela()
        messagebox.showinfo("Sucesso", f"{novo['Papel']} adicionado!")

    tk.Button(form, text="Adicionar", command=adicionar).grid(row=len(campos), columnspan=2, pady=10)
    tk.Button(frame, text="🔄 Limpar Cache", command=cache_cotacoes.limpar_cache).pack(pady=10)


# Barra de status
status_var = tk.StringVar()
status_var.set("Pronto")
status_bar = tk.Label(janela, textvariable=status_var, bd=1, relief="sunken", anchor="w")
status_bar.pack(side="bottom", fill="x")

# Inicialização
mostrar_secao("Ações")
inicializar_precos()

janela.mainloop()