import discord
import requests
from Card import Card
from discord.ext import tasks
from decouple import config
from pymongo import MongoClient
from WebAccess import *
from commands import tree

@discordClient.event
async def on_ready():
    print("bot is running")
    await tree.sync() #Update the discord command list in case of changes
    checkForChanges.start()
    

async def insertNewCards(request, cardSet):
    cardsInSet = await buildCardArray(request)
    cardsInDBCursor = cardDB[cardSet].find()
    cardsInDB = list()
    for card in cardsInDBCursor:
        cardsInDB.append(card)
    newCards = getUnstoredCards(cardsInDB, cardsInSet)
    if len(newCards) > 0:
        print(newCards)
        cardDB[cardSet].insert_many(newCards)
    return newCards

def getUnstoredCards(cardsInDB, cardsInSet):
    cardsInDB.sort(key=lambda card: card.get("_id"))
    cardsInSet.sort(key=lambda card: card.get("_id"))
    return compareLists(cardsInDB, cardsInSet)

def compareLists(cardsInDB, cardsInSet):
    newCards = []
    i = 0
    for card in cardsInDB:
        if len(cardsInSet) <= i:
            return newCards
        while len(cardsInSet) > i and card.get("_id") != cardsInSet[i].get("_id"):
            print(card.get("name") + " / " + cardsInSet[i].get("name"))
            newCards.append(cardsInSet.pop(i))
        i += 1
    return newCards

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

async def sendCards(channel, newCardsofSet):
    for c in newCardsofSet:
        channel.send(embed = c.toMsg('front'))
        if c.modal:
            channel.send(embed = c.toMsg('back'))
    
@discordClient.event
async def on_guild_join(guild):
    serverCol.insert_one({'Name': guild.name, 'Sets': {}})

def getServers():
    serversCursor = serverCol.find()
    servers = list()
    for server in serversCursor:
        servers.append(server)
    return servers

def getSetsToBuild(servers):
    setsToBuild = set()
    for server in servers:
        if server.get("Sets"):
            for cardSet in server.get("Sets"):
                setsToBuild.add(cardSet)
    return setsToBuild

async def getNewCards(setsToBuild):
    newCards = dict()
    for cardSet in setsToBuild:
        unparsed = requests.get('https://api.scryfall.com/cards/search?order=set&q=%28' +
                                'set%3A' + cardSet + '%29')
        request = unparsed.json()
        newCards[cardSet] = await insertNewCards(request, cardSet)
    return newCards

async def sendNewCards(servers, newCards):
    for server in servers:
        channel = discordClient.get_channel(server.get("Spoiler_channel"))
        if server.get("Sets"):
            for cardSet in server.get("Sets"):
                await sendCards(channel, newCards[cardSet])

@tasks.loop(minutes=5)
async def checkForChanges():
    servers = getServers()
    setsToBuild = getSetsToBuild(servers)
    newCards = await getNewCards(setsToBuild)
    await sendNewCards(servers, newCards)


discordClient.run(token)
        
