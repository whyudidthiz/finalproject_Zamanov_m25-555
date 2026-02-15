import functools
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__) 

def log_action(verbose: bool = False):
    """
    Декоратор для логирования доменных операций (buy, sell, register, login).
    verbose=True добавляет детали (состояние кошелька "было→стало").
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from valutatrade_hub.core.usecases import get_current_user
            user = get_current_user()
            username = user.username if user else 'anonymous'
            user_id = user.user_id if user else None

            action = func.__name__.upper()  # BUY, SELL, REGISTER, LOGIN
            currency = kwargs.get('currency')
            amount = kwargs.get('amount')
            base = kwargs.get('base_currency', 'USD')  # по умолчанию
            rate = None 

            # Словарь для дополнительной информации при verbose
            extra_info = {}

            try:
                result = func(*args, **kwargs)
                log_level = logging.INFO
                status = 'OK'
                error_msg = ''
            except Exception as e:
                log_level = logging.ERROR
                status = 'ERROR'
                error_msg = f'error_type={type(e).__name__} error_message="{str(e)}"'
                raise  
            else:
                log_parts = [
                    f'action={action}',
                    f'user={username}',
                    f'user_id={user_id}' if user_id else '',
                    f'currency={currency}' if currency else '',
                    f'amount={amount:.4f}' if amount else '',
                    f'base={base}' if base else '',
                    f'result={status}',
                    error_msg
                ]
                log_parts = [p for p in log_parts if p]
                log_message = ' '.join(log_parts)

                logger.log(log_level, log_message)

                if verbose and status == 'OK':
                    pass

                return result
        return wrapper
    return decorator