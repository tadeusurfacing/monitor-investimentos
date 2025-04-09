from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from tkinter import messagebox

def exportar_pdf(df):
    try:
        df_exportar = df.copy()
        df_exportar = df_exportar[["Papel", "Empresa", "Preço Médio", "Preço Atual",
                                   "Quantidade", "Total Investido", "Valor Atual",
                                   "Dividendos", "Dividendos/Ação", "Rentabilidade"]]

        pdf_path = "relatorio_acoes.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 800, "Relatório de Ações")

        c.setFont("Helvetica-Bold", 10)
        headers = df_exportar.columns
        for i, header in enumerate(headers):
            c.drawString(50 + i * 100, 770, header)

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
