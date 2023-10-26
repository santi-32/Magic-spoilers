import requests
from Card import Card

async def buildCardArray(request):
    cardList = list()
    if request['object'] == "list":
        for c in request['data']:
           cardInstance = Card(c)
           cardList.extend(cardInstance.toDict())
    if "next_page" in request:
        request = requests.get(request["next_page"]).json()
        cardList.extend(await buildCardArray(request))
    return cardList

async def getCardsInSet(card_set):
    newCards = dict()
    unparsed = requests.get('https://api.scryfall.com/cards/search?order=set&q=%28' +
                                'set%3A' + card_set + '%29')
    request = unparsed.json()
    newCards = await buildCardArray(request)
    return newCards