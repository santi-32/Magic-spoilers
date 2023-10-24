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
    await tree.sync()
    checkForChanges.start()

@tasks.loop(minutes=5)
async def checkForChanges():
    serversCursor = serverCol.find()
    servers = list()
    for server in serversCursor:
        servers.append(server)
    print(servers)
    setsToBuild = set()
    for server in servers:
        if server.get("Sets"):
            for cardSet in server.get("Sets"):
                setsToBuild.add(cardSet)
    newCards = dict()

    for cardSet in setsToBuild:
        unparsed = requests.get('https://api.scryfall.com/cards/search?order=set&q=%28' +
                                'set%3A' + cardSet + '%29')
        request = unparsed.json()
        newCards[cardSet] = await getNewCards(request, cardSet)

    for server in servers:
        channel = discordClient.get_channel(server.get("Spoiler_channel"))
        if server.get("Sets"):
            for cardSet in server.get("Sets"):
                await sendCards(channel, newCards[cardSet])

async def getNewCards(request, cardSet):
    cardArray = await buildCardArray(request)
    for c in dictedArr:
        print(type(c))
    newCards = cardDB[cardSet].insert_many(dictedArr)
    return newCards

async def buildCardArray(request):
    cardList = list()
    if request['object'] == "list":
        for c in request['data']:
           cardInstance = Card(c)
           cardList.append(cardInstance)
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

discordClient.run(token)
        
