
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import threading

from utils import formatar_valores
from graficos import atualizar_graficos, atualizar_analise
from relatorio import exportar_pdf
from dados import salvar_dados

def iniciar_interface(df, cache):
    # Carregar larguras de colunas do JSON externo
    try:
        with open("config_colunas.json", "r", encoding="utf-8") as f:
            col_widths = json.load(f)
    except Exception:
        col_widths = {
            "Papel": 70,
            "Empresa": 140,
            "Preço Médio": 80,
            "Preço Atual": 80,
            "Quantidade": 70,
            "Total Investido": 100,
            "Valor Atual": 100,
            "Dividendos": 90,
            "Dividendos/Ação": 90,
            "Rentabilidade": 90,
            "PT Bazin": 80
        }

    janela = tk.Tk()
    janela.title("Monitor de Investimentos")
    janela.state('zoomed')

    frame_principal = tk.Frame(janela)
    frame_principal.pack(fill="both", expand=True)

    menu_lateral = tk.Frame(frame_principal, width=200, bg="#1f2937")
    menu_lateral.pack(side="left", fill="y")

    conteudo = tk.Frame(frame_principal, bg="white")
    conteudo.pack(side="right", fill="both", expand=True)

    # Frame para botões de ação
    frame_botoes = tk.Frame(menu_lateral, bg="#1f2937")
    frame_botoes.pack(side="bottom", fill="x", pady=10)

    btn_salvar = tk.Button(frame_botoes, text="💾 Salvar", command=lambda: salvar_dados(df),
                           bg="#10b981", fg="white", relief="flat", font=("Segoe UI", 10))
    btn_salvar.pack(fill="x", pady=5)

    btn_exportar = tk.Button(frame_botoes, text="📄 Exportar PDF", command=lambda: exportar_pdf(df),
                             bg="#3b82f6", fg="white", relief="flat", font=("Segoe UI", 10))
    btn_exportar.pack(fill="x", pady=5)

    def inicializar_precos():
        def tarefa():
            status_var.set("Atualizando cotações...")
            # Aqui você pode inserir lógica real depois
            status_var.set("Cotações atualizadas!")
        threading.Thread(target=tarefa, daemon=True).start()

    btn_atualizar = tk.Button(frame_botoes, text="🔄 Atualizar Cotações",
                              command=inicializar_precos,
                              bg="#f59e0b", fg="black", relief="flat", font=("Segoe UI", 10))
    btn_atualizar.pack(fill="x", pady=5)

    # Abas da interface
    botoes_secoes = ["Ações", "Gráficos", "Análise Geral"]
    frames_secoes = {}

    def mostrar_secao(secao):
        for f in frames_secoes.values():
            f.pack_forget()
        frames_secoes[secao].pack(fill="both", expand=True)
        if secao == "Gráficos":
            atualizar_graficos(frames_secoes["Gráficos"], df)
        elif secao == "Análise Geral":
            atualizar_analise(frames_secoes["Análise Geral"], df)

    for nome in botoes_secoes:
        btn = tk.Button(menu_lateral, text=nome, anchor="w", padx=20, pady=10,
                        relief="flat", fg="white", bg="#1f2937", activeforeground="white",
                        bd=0, font=("Segoe UI", 10, "bold"),
                        command=lambda n=nome: mostrar_secao(n))
        btn.pack(padx=10, pady=6)
        frames_secoes[nome] = tk.Frame(conteudo)

    # Tabela
    colunas_para_mostrar = list(col_widths.keys())
    tabela_acoes = ttk.Treeview(frames_secoes["Ações"], columns=colunas_para_mostrar,
                                show="headings", selectmode="browse")
    for col in colunas_para_mostrar:
        tabela_acoes.heading(col, text=col)
        tabela_acoes.column(col, width=col_widths.get(col, 80), anchor="center")

    scroll_y = ttk.Scrollbar(frames_secoes["Ações"], orient="vertical", command=tabela_acoes.yview)
    tabela_acoes.configure(yscrollcommand=scroll_y.set)

    tabela_acoes.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    def atualizar_tabela():
        for i in tabela_acoes.get_children():
            tabela_acoes.delete(i)
        df_exibicao = df.apply(formatar_valores, axis=1)
        for _, row in df_exibicao.iterrows():
            valores = [row[col] for col in colunas_para_mostrar]
            tabela_acoes.insert("", "end", values=valores)

    status_var = tk.StringVar()
    status_var.set("Pronto")
    status_bar = tk.Label(janela, textvariable=status_var, bd=1, relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")

    mostrar_secao("Ações")
    atualizar_tabela()

    janela.mainloop()
