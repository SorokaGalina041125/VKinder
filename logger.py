import os
from functools import wraps

from datetime import datetime


def logger(old_function):
    @wraps(old_function)
    def new_function(*args, **kwargs):
        result = old_function(*args, **kwargs)
        now = datetime.now()
        log_message = f'Вызывается функция {old_function.__name__} с аргументами {args} и {kwargs}\n{result=}\nвремя вызова {now.strftime("%Y-%m-%d %H:%M:%S")}'
        with open('main.log', 'a', encoding='utf-8') as log_file:
            log_file.write(log_message + '\n')
        return result

    return new_function