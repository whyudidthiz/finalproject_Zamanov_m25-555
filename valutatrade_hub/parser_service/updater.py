import logging
from typing import List, Dict, Any

from .api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
from .storage import RatesStorage
from .config import ParserConfig
from valutatrade_hub.core.exceptions import ApiRequestError

logger = logging.getLogger(__name__)


class RatesUpdater:
    """Координатор процесса обновления курсов."""

    def __init__(self, config: ParserConfig, storage: RatesStorage):
        self.config = config
        self.storage = storage
        self.clients: List[BaseApiClient] = [
            CoinGeckoClient(config),
            ExchangeRateApiClient(config)
        ]
        # Для сопоставления пары и источника
        self.source_map = {}

    def run_update(self) -> Dict[str, Any]:
        """
        Запускает обновление от всех клиентов.
        Возвращает статистику: количество успешных, ошибки.
        """
        logger.info("Starting rates update...")
        all_rates = {}
        errors = []

        for client in self.clients:
            client_name = client.__class__.__name__
            try:
                rates = client.fetch_rates()
                logger.info(f"{client_name}: OK ({len(rates)} rates)")
                # Сохраняем историю для каждого источника
                source = "CoinGecko" if isinstance(client, CoinGeckoClient) else "ExchangeRate-API"
                if rates:
                    self.storage.save_historical_rates(rates, source)
                    all_rates.update(rates)
                    # Запоминаем источник для каждой пары
                    for pair in rates:
                        self.source_map[pair] = source
            except ApiRequestError as e:
                logger.error(f"{client_name}: ERROR - {str(e)}")
                errors.append(f"{client_name}: {str(e)}")
            except Exception as e:
                logger.error(f"{client_name}: Unexpected error - {str(e)}")
                errors.append(f"{client_name}: unexpected error")

        if all_rates:
            self.storage.update_cache(all_rates, self.source_map)
            logger.info(f"Cache updated with {len(all_rates)} rates")
        else:
            logger.warning("No rates were fetched")

        return {
            "total": len(all_rates),
            "errors": errors,
            "last_refresh": datetime.utcnow().isoformat() + 'Z' if all_rates else None
        }