
from interface import iniciar_interface
from dados import carregar_dados
from cotacoes import CotacaoCache

if __name__ == "__main__":
    print("Iniciando aplicação...")
    df = carregar_dados()
    cache = CotacaoCache()
    iniciar_interface(df, cache)
