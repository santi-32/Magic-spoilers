import os
import sys
import discord
import requests
import json
import time
import asyncio
from discord.ext import tasks
import logging, traceback
import pymongo
from decouple import config
from pymongo import MongoClient

cluster = MongoClient("mongodb+srv://santi_32:santi_32@ms.gy385.mongodb.net/?retryWrites=true&w=majority")
db = cluster["MS"]
collection = db["Cards"]

token = config('TOKEN')
discordClient = discord.Client()
liveSets = ['ea1', 'ha6', 'dmu', 'dmc']

class returnstruct():
    def __init__(self, Name, _id, Mana_cost, Types, Text, Power, Toughness, Image, Modal, SecondFace, Set, Set_name, Collector_number):
        self.Name = Name
        self._id = _id
        self.Mana_cost = Mana_cost
        self.Types = Types
        self.Text = Text
        self.Power = Power
        self.Toughness = Toughness
        self.Image = Image
        self.Modal = Modal
        self.SecondFace = SecondFace
        self.Set = Set
        self.Set_name = Set_name
        self.Collector_number = Collector_number


@discordClient.event
async def on_ready():
    print("bot is running")
    checkForChanges.start()

@tasks.loop(minutes=5)
async def checkForChanges():
  sumString = ''
  for set in liveSets:
    if sumString == '':
      sumString += 'set%3A' + set
    else:
      sumString += '+OR+' + 'set%3A' + set
  unparsed = requests.get('https://api.scryfall.com/cards/search?order=set&q=%28' + sumString + '%29')
  print(unparsed)
  request = unparsed.json()
  if request['object'] == "list":
    data = collection.find().sort([("Set", 1), ("Collector_Number", 1)])
    dataSize = collection.count_documents({})
    newCards = await compareCards(request, data, dataSize)
    dicted_arr = []
    for i in newCards:
      if i.Modal:
        i.SecondFace = i.SecondFace.__dict__
      dicted_arr.append(i.__dict__)
    collection.insert_many(dicted_arr)
  else:
    print("something went wrong")

async def on_error(event, *args, **kwargs):
  logging.warning(traceback.format_exc())

async def compareCards(request, data, dataSize):
  newCards = getNewCards(data, request, dataSize)
  if (len(newCards) > 0):
    for g in discordClient.guilds:
      canal = discord.utils.get(g.channels, name="new-set-previews")
      for i in newCards:
        await send_card(i, canal)
  return newCards

def parseCard(newFetch, b_pos):
    carta = newFetch['data'][b_pos]
    name = ''
    types = ''
    power = '0'
    toughness = '0'
    mana_cost = '0'
    oracle_text = 'Vanilla'
    image = 'No Image available'
    modal = False
    secondface = None
    _id = carta['id']
    set = carta['set']
    set_name = carta['set_name']
    collector_number = carta['collector_number']
    if 'card_faces' in carta:
        secondface = returnstruct(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        modal = True
        carta = carta['card_faces']
        name = carta[0]['name']
        types = carta[0]['type_line']
        if 'power' in carta[0]:
            power = carta[0]['power']
            toughness = carta[0]['toughness']
        if 'mana_cost' in carta[0]:
            mana_cost = carta[0]['mana_cost']
        if "oracle_text" in carta[0]:
            oracle_text = carta[0]['oracle_text']
        if 'image_uris' in carta[0]:
            image = carta[0]['image_uris']['png']
        secondface.Name = carta[1]['name']
        secondface.Types = carta[1]['type_line']
        if 'power' in carta[1]:
            secondface.Power = carta[1]['power']
            secondface.Toughness = carta[1]['toughness']
        if 'mana_cost' in carta[1]:
            secondface.Mana_cost = carta[1]['mana_cost']
        if "oracle_text" in carta[1]:
            secondface.Text = carta[1]['oracle_text']
        if 'image_uris' in carta[1]:
            secondface.Image = carta[1]['image_uris']['png']
    else:
        name = carta['name']
        types = carta['type_line']
        if 'power' in carta:
            power = carta['power']
            toughness = carta['toughness']
        if 'mana_cost' in carta:
            mana_cost = carta['mana_cost']
        if "oracle_text" in carta:
            oracle_text = carta['oracle_text']
        if 'image_uris' in carta:
            image = carta['image_uris']['png']
    return (returnstruct(name, _id, mana_cost, types, oracle_text, power, toughness, image, modal, secondface, set, set_name, collector_number))


def getNewCards(database, newFetch, dataSize):
  b_pos = 0
  arr = []
  if (dataSize) <= len(newFetch['data']):
    for i in database:
      if b_pos < len(newFetch['data']):
        while ((b_pos < len(newFetch['data'])) and (i["Collector_number"] != newFetch['data'][b_pos]["collector_number"])):
          new_card = parseCard(newFetch, b_pos)
          arr.append(new_card)
          b_pos += 1
        b_pos += 1
    while (b_pos < len(newFetch['data'])):
      new_card = parseCard(newFetch, b_pos)
      arr.append(new_card)
      b_pos += 1
  return arr

async def send_card(i, canal):
	pt = ''
	if "Creature" in i.Types:
		pt = ('\n' + i.Power + '/' + i.Toughness)
	Embed = discord.Embed(title=i.Name, description=(i.Mana_cost + '\n' + i.Types + '\n' + i.Text + pt + '\n' + '\n' + i.Set))
	if i.Image != "No Image available":
		Embed.set_image(url=i.Image)
	await canal.send(embed=Embed)
	if i.Modal == True:
		i.Modal = False
		send_card(i.secondface)

discordClient.run(token)