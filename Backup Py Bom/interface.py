
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
