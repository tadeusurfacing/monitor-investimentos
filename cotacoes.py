
import yfinance as yf
import os
import json
import logging
from datetime import datetime, timedelta

CACHE_FILE = "cotacoes_cache.json"

class CotacaoCache:
    def __init__(self):
        self._cache = {}
        self.CACHE_VALIDADE = timedelta(minutes=30)
        self._carregar_cache()

    def obter_cotacao(self, ticker):
        agora = datetime.now()
        if ticker in self._cache:
            dados, timestamp = self._cache[ticker]
            if agora - timestamp < self.CACHE_VALIDADE:
                return dados

        try:
            nova_cotacao = self._buscar_yfinance(ticker)
            self._cache[ticker] = (nova_cotacao, agora)
            self._salvar_cache()
            return nova_cotacao
        except Exception as e:
            logging.warning(f"Falha ao buscar {ticker}: {str(e)}")
            return self._cache.get(ticker, (None, None))[0]

    @staticmethod
    def _buscar_yfinance(ticker):
        dados = yf.Ticker(ticker).history(period="1d")
        return {
            'preco': round(dados['Close'].iloc[-1], 2),
            'variacao': round(dados['Close'].pct_change().iloc[-1] * 100, 2)
        }

    def limpar_cache(self):
        self._cache = {}
        self._salvar_cache()
        logging.info("Cache limpo")

    def _salvar_cache(self):
        try:
            serializavel = {
                k: {
                    "dados": v[0],
                    "timestamp": v[1].isoformat()
                } for k, v in self._cache.items()
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(serializavel, f, indent=2)
        except Exception as e:
            logging.error(f"Erro ao salvar cache: {str(e)}")

    def _carregar_cache(self):
        if not os.path.exists(CACHE_FILE):
            return
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                raw_cache = json.load(f)
                for k, v in raw_cache.items():
                    dados = v["dados"]
                    timestamp = datetime.fromisoformat(v["timestamp"])
                    self._cache[k] = (dados, timestamp)
        except Exception as e:
            logging.warning(f"Erro ao carregar cache salvo: {str(e)}")
