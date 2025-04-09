
import unittest
from utils import formatar_valores

class TestFormatarValores(unittest.TestCase):
    def test_preco_medio_formatado(self):
        row = {"Preço Médio": 12.3456, "Preço Atual": 10.0, "Total Investido": 1000.0,
               "Valor Atual": 900.0, "Dividendos": 50.0, "Rentabilidade": -10.0,
               "Dividendos/Ação": 2.5, "PT Bazin": 38.0}
        resultado = formatar_valores(row)
        self.assertEqual(resultado["Preço Médio"], "R$ 12.35")
        self.assertEqual(resultado["Rentabilidade"], "-10.00%")
        self.assertTrue(resultado["Dividendos"].startswith("R$"))
        self.assertTrue(resultado["PT Bazin"].startswith("R$"))

if __name__ == "__main__":
    unittest.main()
