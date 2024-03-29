import discord
from discord.ext import tasks
from WebAccess import *
from commands import tree
import time
from card_array_builder import getCardsInSet


@discordClient.event
async def on_ready():
    print("bot is running")
    await updateServerList()
    await tree.sync() #Update the discord command list in case of changes
    checkForChanges.start()
    

async def insertNewCards(cardsInSet, cardSet):
    cardsInDBCursor = cardDB[cardSet].find()
    cardsInDB = list()
    for card in cardsInDBCursor:
        cardsInDB.append(card)
    newCards = getUnstoredCards(cardsInDB, cardsInSet)
    if len(newCards) > 0:
        cardDB[cardSet].insert_many(newCards)
    return newCards

def getUnstoredCards(cardsInDB, cardsInSet):
    cardsInDB.sort(key=lambda card: card.get("_id"))
    cardsInSet.sort(key=lambda card: card.get("_id"))
    return compareLists(cardsInDB, cardsInSet)

def compareLists(cardsInDB, cardsInSet: list):
    newCards = []
    i = 0
    for card in cardsInDB:
        if len(cardsInSet) <= i:
            return newCards
        temp = []
        while len(cardsInSet) > i and card.get("_id") != cardsInSet[i].get("_id"):
            print(card.get('name') + " / " + cardsInSet[i].get('name')) #in case of testing
            discrepancy = cardsInSet.pop(i)
            temp.append(discrepancy)
        if len(cardsInSet) == i: #this ocurrs if 'card' is in cardsInDB, but not in cardsInSet, this ocurrs due to mistakes from scryfall's database and must be handleded as an exception
            cardsInSet.extend(temp)
        else:
            newCards.extend(temp)
            i += 1
    for j in range(i, len(cardsInSet)):
        newCards.append(cardsInSet[j])
    return newCards

async def sendCards(channel, newCardsofSet):
    for c in newCardsofSet:
        await channel.send(embed = toMsg(c))

def toMsg(card):
    pt = ''
    if (card.get("power") and card.get("toughness")):
        pt = ('\n' + card.get("power") + '/' + card.get("toughness"))
    Embed = discord.Embed(title=card["name"], description=(str(card["mana_cost"]) + '\n' + str(card["type_line"]) + '\n' + str(card["oracle_text"]) + str(pt) + '\n' + '\n' + str(card["set_name"])))
    if card.get("image") != "No Image available":
        Embed.set_image(url=card.get("image"))
    return Embed
    
@discordClient.event
async def on_guild_join(guild):
    guilds.insert_one({'_id': guild.id, 'Name': guild.name, 'Sets': {}})

def getServers():
    serversCursor = guilds.find()
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

async def getSpoiledCards(setsToBuild):
    newCards = dict()
    for cardSet in setsToBuild:
        cardsInSet = await getCardsInSet(cardSet)
        newCards[cardSet] = await insertNewCards(cardsInSet, cardSet)
    return newCards

async def sendNewCards(servers, newCards):
    for server in servers:
        channel = discordClient.get_channel(server.get("Spoiler_channel"))
        if server.get("Sets") and channel: #if the server has a list of sets and a dedicated channel defined
            for cardSet in server.get("Sets"):
                await sendCards(channel, newCards[cardSet])


async def updateServerList():
    async for guild in discordClient.fetch_guilds():
        server = guilds.find_one({"_id": guild.id})
        if not server:
            guilds.insert_one({'_id': guild.id, 'Name': guild.name, 'Sets': {}})

@tasks.loop(minutes=5)
async def checkForChanges():
    
    start = time.time()
    servers = getServers()
    setsToBuild = getSetsToBuild(servers)
    newCards = await getSpoiledCards(setsToBuild)
    await sendNewCards(servers, newCards)
    end = time.time()
    print("update cycle realized succesfully in " + str(end - start) + " seconds")


discordClient.run(token)
        
