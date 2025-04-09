import os
import json
import streamlit as st
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

    # Configurar o título da aplicação
    st.title("Monitor de Investimentos")

    # Menu lateral com botões de ação
    with st.sidebar:
        st.header("Ações")

        # Botão Salvar
        if st.button("💾 Salvar"):
            salvar_dados(df)
            st.success("Dados salvos com sucesso!")

        # Botão Exportar PDF
        if st.button("📄 Exportar PDF"):
            exportar_pdf(df)
            st.success("PDF exportado com sucesso!")

        # Botão Atualizar Cotações
        def inicializar_precos():
            status_placeholder = st.empty()
            status_placeholder.info("Atualizando cotações...")
            # Aqui você pode inserir lógica real depois
            status_placeholder.success("Cotações atualizadas!")

        if st.button("🔄 Atualizar Cotações"):
            # Executar a atualização em uma thread para não bloquear a interface
            threading.Thread(target=inicializar_precos, daemon=True).start()

    # Abas da interface
    tab_names = ["Ações", "Gráficos", "Análise Geral"]
    tabs = st.tabs(tab_names)

    # Seção Ações (Tabela)
    with tabs[0]:
        # Tabela
        colunas_para_mostrar = list(col_widths.keys())
        df_exibicao = df.apply(formatar_valores, axis=1)
        df_exibicao = df_exibicao[colunas_para_mostrar]

        # Exibir a tabela com Streamlit
        st.dataframe(
            df_exibicao,
            use_container_width=True,
            column_config={col: st.column_config.Column(width=col_widths.get(col, 80)) for col in colunas_para_mostrar}
        )

    # Seção Gráficos
    with tabs[1]:
        # Placeholder para os gráficos
        graficos_placeholder = st.empty()
        atualizar_graficos(graficos_placeholder, df)

    # Seção Análise Geral
    with tabs[2]:
        # Placeholder para a análise
        analise_placeholder = st.empty()
        atualizar_analise(analise_placeholder, df)

    # Barra de status
    status_var = st.session_state.get("status", "Pronto")
    st.info(f"Status: {status_var}")

# Para garantir que o status persista entre interações
if "status" not in st.session_state:
    st.session_state["status"] = "Pronto"
