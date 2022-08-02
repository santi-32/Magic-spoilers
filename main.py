from ctypes import sizeof
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

cluster = MongoClient(config('MONGOACCESS'))
db = cluster["MS"]
collection = db["Cards"]

token = config('DISCORDTOKEN')
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
    newCards = await compareCards(request, collection)
    dicted_arr = []
    if len(newCards) > 0:
      for i in newCards:
        if i.Modal:
          i.SecondFace = i.SecondFace.__dict__
        dicted_arr.append(i.__dict__)
      collection.insert_many(dicted_arr)
  else:
    print("something went wrong")

async def on_error(event, *args, **kwargs):
  logging.warning(traceback.format_exc())

async def compareCards(request, collection):
  newCards = getNewCards(collection, request)
  if (len(newCards) > 0):
    for g in discordClient.guilds:
      canal = discord.utils.get(g.channels, name="new-set-previews")
      for i in newCards:
        await send_card(i, canal)
  return newCards

def parseCard(card):
    name = ''
    types = ''
    power = '0'
    toughness = '0'
    mana_cost = '0'
    oracle_text = 'Vanilla'
    image = 'No Image available'
    modal = False
    secondface = None
    _id = card['id']
    set = card['set']
    set_name = card['set_name']
    collector_number = card['collector_number']
    if 'card_faces' in card:
        secondface = returnstruct(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        modal = True
        card = card['card_faces']
        name = card[0]['name']
        types = card[0]['type_line']
        if 'power' in card[0]:
            power = card[0]['power']
            toughness = card[0]['toughness']
        if 'mana_cost' in card[0]:
            mana_cost = card[0]['mana_cost']
        if "oracle_text" in card[0]:
            oracle_text = card[0]['oracle_text']
        if 'image_uris' in card[0]:
            image = card[0]['image_uris']['png']
        secondface.Name = card[1]['name']
        secondface.Types = card[1]['type_line']
        if 'power' in card[1]:
            secondface.Power = card[1]['power']
            secondface.Toughness = card[1]['toughness']
        if 'mana_cost' in card[1]:
            secondface.Mana_cost = card[1]['mana_cost']
        if "oracle_text" in card[1]:
            secondface.Text = card[1]['oracle_text']
        if 'image_uris' in card[1]:
            secondface.Image = card[1]['image_uris']['png']
    else:
        name = card['name']
        types = card['type_line']
        if 'power' in card:
            power = card['power']
            toughness = card['toughness']
        if 'mana_cost' in card:
            mana_cost = card['mana_cost']
        if "oracle_text" in card:
            oracle_text = card['oracle_text']
        if 'image_uris' in card:
            image = card['image_uris']['png']
    return (returnstruct(name, _id, mana_cost, types, oracle_text, power, toughness, image, modal, secondface, set, set_name, collector_number))


def getNewCards(collection, newFetch):
  arr = []
  for card in newFetch['data']:
    isInDatabase = collection.find_one({"_id": card['id']}) 
    if isInDatabase == None:
      print(isInDatabase)
      new_card = parseCard(card)
      arr.append(new_card)
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