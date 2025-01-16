# CurbeeBot

Бот для быстрой конвертации валют и криптовалют с использованием [Inline Query](https://core.telegram.org/bots/features#inline-requests)

Бот позволяет конвертировать валюты fiat => fiat, crypto => fiat, fiat => crypto, crypto => crypto

> [!NOTE]
> Ссылка на прод бота: <временно отсутствует>

## Используемые технологии

- Бот построен на [Aiogram](https://aiogram.dev/) с использованием [Python](https://www.python.org/)
- В качестве данных о курсах фиатных валют подтягивается [json с курсами ЦБРФ](https://www.cbr-xml-daily.ru/)
- В качестве данных о курсах криптовалют делается запрос к [API ресурса Cryptocompare](https://min-api.cryptocompare.com/)

## Как работает бот

### Alpha 0.1

При запуске бот подтягивает актуальные курсы валют, делая запросы к Cryptocompare и cbr-xml-daily, кеширует их на час и хендлит инлайн-запросы с 2 или 3 аргументами вида: <pre>@curbeebot (количество) (исходная валюта) [валюта конвертации]</pre>

К примеру: <pre>@CurbeeBot 1 USD</pre>Выведет все доступные конвертации из USD

<pre>@CurbeeBot 1 ETH RUB</pre>Выведет курс для 1 ETH в рублях.

В дальнейшем, каждые 3600 секунд бот будет обновлять актуальные данные и кешировать их до следующего обновления. 

## Как использовать исходники бота у себя

> [!TIP]
> tl;dr скачайте исходники, заполните ADMIN_IDS, BOT_TOKEN и укажите свой API Key Cryptocompare в currency_rates; запустите удобным образом.

### Добавление новых валют

Всё просто! 

Добавьте необходимые вам тикеры валют в @dp.inline_handler (fiat_symbols, crypto_symbols), а также в CurrencyRates => get_crypto_rates (fsyms и tsyms) 
(не забудьте проверить, доступны ли эти тикеры в Cryptocompare)

Теперь, при инициализации бота и обновлении курсов будут подтягиваться новые валюты.

## Как контрибьютить

Форк -> Новая ветка от prod -> Пулл реквест 

## Лицензия

Бот распространяется по лицензии WTFPL. Больше деталей в файле [LICENSE](/LICENSE.txt)

## Благодарности

За идею - оригинальному боту [@ccurbot](https://t.me/ccurbot)

За образец файла, который вы сейчас читаете - [SecondThundeR](https://github.com/SecondThundeR)
