import requests
from decouple import config

from django.db import transaction
from django.utils import timezone

from .models import Stock, Player, PlayerStock


def fetch_quotes(symbol):
    """Fetch stock prices from list of symbols"""

    quotes = {}
    link = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey={}".format(symbol, config('API_SECRET_TOKEN'))
    # # print(link)
    
    try:
        response = requests.get(link)
    except:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    quotes['price'] = data['Global Quote']['05. price']
    quotes['diff'] = data['Global Quote']['09. change']
    # quotes['price'] = 35
    # quotes['diff'] = 24

    return quotes


@transaction.atomic
def update_all_stock_prices():
    all_stocks = Stock.objects.all()
    #symbol_list = [s.code for s in all_stocks]
    for stock in all_stocks:
        quotes = fetch_quotes(stock.code)
        stock.price = quotes['price']
        stock.diff = quotes['diff']
        stock.last_updated = timezone.now()
        stock.save()


@transaction.atomic
def update_all_player_assets():
    all_players = Player.objects.all()
    for player in all_players:
        playerObj = Player.objects.select_for_update().filter(
            user=player.user)[0]
        playerObj.value_in_stocks = 0
        for j in PlayerStock.objects.select_for_update().filter(player=playerObj):  # noqa
            playerObj.value_in_stocks += j.stock.price * j.quantity
        playerObj.save()
        print("updated ", playerObj)
