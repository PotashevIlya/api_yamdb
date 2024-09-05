import re
from datetime import datetime

from django.core.exceptions import ValidationError

from api_yamdb.settings import SELF_ENDPOINT


MESSAGE_WRONG_SYMBOLS = (
    'Допустимы буквы, цифры и символы @ . + - _ .'
    ' Обнаружено: {wrong_symbols}'
)
MESSAGE_RESTRICTED_USERNAME = '"Имя {username} недопустимо'
MESSAGE_YEAR_VALIDATION_ERROR = (
    'Убедитесь, что введённое значение года {year} не превышает '
    'текущее значение года {current_year}'
)


def validate_username(value) -> str:
    wrong_symbols = re.findall(r'[^\w.@+-]', value)
    if len(wrong_symbols):
        wrong_symbols = set(wrong_symbols)
        symbols_for_message = ''.join(set(wrong_symbols))
        raise ValidationError(
            MESSAGE_WRONG_SYMBOLS.format(
                wrong_symbols=symbols_for_message
            )
        )
    if value == SELF_ENDPOINT:
        raise ValidationError(
            MESSAGE_RESTRICTED_USERNAME.format(username=SELF_ENDPOINT)
        )
    return value


def year_validator(year):
    current_year = datetime.now().year
    if year > current_year:
        raise ValidationError(
            MESSAGE_YEAR_VALIDATION_ERROR.format(
                current_year=current_year,
                year=year
            )
        )
    return year
