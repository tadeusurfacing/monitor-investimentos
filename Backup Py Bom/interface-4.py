
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from utils import formatar_valores
import numpy as np
import pandas as pd
from dados import salvar_dados, atualizar_dados_financeiros
from relatorios import exportar_pdf
from graficos import atualizar_graficos, atualizar_analise

col_widths = {
    "Papel": 60,
    "Empresa": 120,
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


def iniciar_interface(df, cache):
    janela = tk.Tk()
    janela.title("Monitor de Investimentos")
    janela.state('zoomed')

    frame_principal = tk.Frame(janela)
    frame_principal.pack(fill="both", expand=True)

    menu_lateral = tk.Frame(frame_principal, width=200, bg="#1f2937")
    menu_lateral.pack(side="left", fill="y")

    conteudo = tk.Frame(frame_principal, bg="white")
    conteudo.pack(side="right", fill="both", expand=True)

    status_var = tk.StringVar()
    status_var.set("Pronto")

    colunas_para_mostrar = ["Papel", "Empresa", "Preço Médio", "Preço Atual",
                            "Quantidade", "Total Investido", "Valor Atual",
                            "Dividendos", "Dividendos/Ação", "Rentabilidade", "PT Bazin"]

    frames_secoes = {nome: tk.Frame(conteudo) for nome in ["Ações", "Gráficos", "Análise Geral"]}
    for frame in frames_secoes.values():
        frame.pack_forget()

    col_widths = {'Papel': 60, 'Empresa': 120, 'Preço Médio': 80, 'Preço Atual': 80, 'Quantidade': 70, 'Total Investido': 100, 'Valor Atual': 100, 'Dividendos': 90, 'Dividendos/Ação': 90, 'Rentabilidade': 90, 'PT Bazin': 80}


    tabela_acoes = ttk.Treeview(frames_secoes["Ações"], columns=colunas_para_mostrar,
                                show="headings", selectmode="browse")
    for col in colunas_para_mostrar:
        tabela_acoes.heading(col, text=col)
        tabela_acoes.column(col, width=col_widths.get(col, 80), anchor="center")


    tabela_acoes.tag_configure("positivo", background="#d4edda")
    tabela_acoes.tag_configure("negativo", background="#f8d7da")
    tabela_acoes.tag_configure("barato", background="#fff3cd")

    scroll_y = ttk.Scrollbar(frames_secoes["Ações"], orient="vertical", command=tabela_acoes.yview)
    scroll_x = ttk.Scrollbar(frames_secoes["Ações"], orient="horizontal", command=tabela_acoes.xview)
    tabela_acoes.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    
    # Campo de busca
    termo_busca = tk.StringVar()
    barra_busca_frame = tk.Frame(frames_secoes["Ações"])
    barra_busca_frame.pack(anchor="nw", padx=10, pady=(10, 0))
    tk.Label(barra_busca_frame, text="Buscar:").pack(side="left")
    tk.Entry(barra_busca_frame, textvariable=termo_busca).pack(side="left", padx=5)

    termo_busca.trace_add("write", lambda *args: atualizar_tabela())

    tabela_acoes.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")

    # formatar_valores agora está em utils.py
# Linha antiga removida

    
    def atualizar_tabela():
        tabela_acoes.delete(*tabela_acoes.get_children())
        df_exibicao = df.apply(formatar_valores, axis=1)
        filtro = termo_busca.get().lower()
        for idx, row in df_exibicao.iterrows():
            if filtro and filtro not in str(row).lower():
                continue
            valores = [row[col] for col in colunas_para_mostrar]
            rentabilidade_valor = df.loc[idx, "Rentabilidade"]
            preco_atual = pd.to_numeric(df.loc[idx, "Preço Atual"], errors="coerce")
            pt_bazin = pd.to_numeric(df.loc[idx, "PT Bazin"], errors="coerce")
            if not pd.isna(preco_atual) and not pd.isna(pt_bazin) and preco_atual < pt_bazin:
                tag = "barato"
            else:
                tag = "positivo" if rentabilidade_valor > 0 else "negativo"
            tabela_acoes.insert("", "end", iid=str(idx), values=valores, tags=(tag,))
        return

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
            nonlocal df
            df = atualizar_dados_financeiros(df, cache)
            janela.after(0, atualizar_tabela)
            janela.after(0, verificar_alertas_bazin)
            janela.after(0, lambda: status_var.set("Cotações atualizadas!"))
        threading.Thread(target=tarefa, daemon=True).start()

    def editar_celula(event):
        item_id = tabela_acoes.identify_row(event.y)
        col = tabela_acoes.identify_column(event.x)
        if not item_id or not col:
            return

        col_index = int(col[1:]) - 1
        col_nome = colunas_para_mostrar[col_index]
        if col_nome not in ["Quantidade", "Total Investido"]:
            return

        bbox = tabela_acoes.bbox(item_id, column=col)
        if not bbox:
            return

        x, y, width, height = bbox
        valor_atual = tabela_acoes.item(item_id, "values")[col_index]

        entry = tk.Entry(frames_secoes["Ações"])
        entry.place(x=x, y=y + tabela_acoes.winfo_y(), width=width, height=height)
        entry.insert(0, valor_atual.replace("R$ ", "").replace("%", "").replace(",", ""))
        entry.focus_set()

        def salvar_edicao(event=None):
            nonlocal df
            novo_valor = entry.get()
            try:
                novo_valor = float(novo_valor)
                idx = int(item_id)
                if col_nome == "Quantidade" and novo_valor == 0:
                    df.drop(index=idx, inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    salvar_dados(df)
                    atualizar_tabela()
                    entry.destroy()
                    return

                df.at[idx, col_nome] = novo_valor

                preco = df.at[idx, "Preço Atual"] if pd.notna(df.at[idx, "Preço Atual"]) else 0
                df.at[idx, "Valor Atual"] = preco * df.at[idx, "Quantidade"]
                if df.at[idx, "Total Investido"] > 0:
                    val = df.at[idx, "Valor Atual"]
                    inv = df.at[idx, "Total Investido"]
                    df.at[idx, "Rentabilidade"] = round(((val - inv) / inv) * 100, 2)
                else:
                    df.at[idx, "Rentabilidade"] = 0.0

                salvar_dados(df)
                atualizar_tabela()
            except Exception as e:
                messagebox.showerror("Erro", f"Valor inválido: {e}")
            finally:
                entry.destroy()

        entry.bind("<Return>", salvar_edicao)
        entry.bind("<FocusOut>", salvar_edicao)

    tabela_acoes.bind("<Double-1>", editar_celula)

    def mostrar_secao(secao):
        for f in frames_secoes.values():
            f.pack_forget()
        frame = frames_secoes[secao]
        frame.pack(fill="both", expand=True)
        if secao == "Gráficos":
            atualizar_graficos(frame, df)
        elif secao == "Análise Geral":
            atualizar_analise(frame, df)

    botoes_secoes = ["Ações", "Gráficos", "Análise Geral"]
    for nome in botoes_secoes:
        btn = tk.Button(menu_lateral, text=nome, anchor="w", padx=20, pady=10,
                        relief="flat", fg="white", bg="#1f2937",
                        activeforeground="white", font=("Segoe UI", 10),
                        command=lambda n=nome: mostrar_secao(n))
        btn.pack(padx=10, pady=6)

    frame_botoes = tk.Frame(menu_lateral, bg="#1f2937")
    frame_botoes.pack(side="bottom", fill="x", pady=10)

    tk.Button(frame_botoes, text="💾 Salvar", command=lambda: salvar_dados(df), bg="#10b981",
               fg="white", relief="flat", font=("Segoe UI", 10)).pack(fill="x", pady=5)

    tk.Button(frame_botoes, text="📄 Exportar PDF", command=lambda: exportar_pdf(df), bg="#3b82f6",
               fg="white", relief="flat", font=("Segoe UI", 10)).pack(fill="x", pady=5)

    tk.Button(frame_botoes, text="🔄 Atualizar Cotações", fg="white", relief="flat", font=("Segoe UI", 10)).pack(fill="x", pady=5)

    status_bar = tk.Label(janela, textvariable=status_var, bd=1, relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")

    mostrar_secao("Ações")
    inicializar_precos()

    janela.mainloop()
