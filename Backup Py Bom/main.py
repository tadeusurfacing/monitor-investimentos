from interface import iniciar_interface
from dados import carregar_dados
from cotacoes import CotacaoCache
from config import LOG_FILE
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=3, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info("Aplicação iniciada")

def main():
    setup_logging()
    df = carregar_dados()
    cache = CotacaoCache()
    iniciar_interface(df, cache)

if __name__ == "__main__":
    main()
