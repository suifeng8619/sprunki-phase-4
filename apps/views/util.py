from functools import wraps
from loguru import logger

from flask import url_for, redirect
from flask_login import logout_user


#  en 不加如链接中
def redirect_if_en(blueprint_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lang = kwargs.get('lang')
            if lang == 'en':
                del kwargs['lang']
                # 使用传入的蓝图名称和函数名称生成URL
                url = url_for(f'{blueprint_name}.{func.__name__}', **kwargs)
                return redirect(url)

            if lang is None:
                kwargs['lang'] = 'en'

            return func(*args, **kwargs)

        return wrapper

    return decorator
