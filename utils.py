
import pandas as pd

def formatar_valores(row):
    row = row.copy()
    row["Preço Médio"] = f"R$ {row['Preço Médio']:.2f}"
    row["Preço Atual"] = f"R$ {row['Preço Atual']:.2f}" if pd.notna(row["Preço Atual"]) else "-"
    row["Preço Teto"] = f"R$ {row['Preço Teto']:.2f}" if "Preço Teto" in row else "-"
    row["Total Investido"] = f"R$ {row['Total Investido']:.2f}"
    row["Valor Atual"] = f"R$ {row['Valor Atual']:.2f}"
    row["Dividendos"] = f"R$ {pd.to_numeric(row['Dividendos'], errors='coerce'):.2f}" if pd.notna(row['Dividendos']) else "R$ 0.00"
    row["Rentabilidade"] = f"{row['Rentabilidade']:.2f}%"
    row["Dividendos/Ação"] = f"R$ {pd.to_numeric(row['Dividendos/Ação'], errors='coerce'):.2f}" if pd.notna(row['Dividendos/Ação']) else "R$ 0.00"
    row["PT Bazin"] = f"R$ {row['PT Bazin']:.2f}" if pd.notna(row["PT Bazin"]) else "-"
    return row
