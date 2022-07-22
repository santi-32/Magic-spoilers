import os
import sys
import discord
import requests
import json
import time
import asyncio
from discord.ext import tasks
import logging, traceback
from decouple import config

token = config('TOKEN')
client = discord.Client()
liveSets = ['ea1', 'ha6', 'dmu', 'dmc']

class returnstruct():
    def __init__(self, Name, Mana_cost, Types, Text, Power, Toughness, Image, Modal, SecondFace, Set):
        self.Name = Name
        self.Mana_cost = Mana_cost
        self.Types = Types
        self.Text = Text
        self.Power = Power
        self.Toughness = Toughness
        self.Image = Image
        self.Modal = Modal
        self.SecondFace = SecondFace
        self.Set = Set


@client.event
async def on_ready():
    print("bot is running")
    funca.start()

@tasks.loop(minutes=5)
async def funca():
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
    if (os.path.exists('sets' + '.json')):
      with open('sets' + '.json', 'r', encoding='utf-8') as lastFetch:
        data = json.load(lastFetch)
        await compareCards(lastFetch, request, data)
    else:
      tempJson = '{ "data":[]}'
      data = json.loads(tempJson)
      await compareCards(tempJson, request, data)
    if (len(data['data']) <= len(request['data'])):
      with open('sets' + '.json', 'w', encoding='utf-8') as lastFetch:
        json.dump(request, lastFetch, ensure_ascii=False, indent=4)

async def on_error(event, *args, **kwargs):
  logging.warning(traceback.format_exc())

async def compareCards(lastFetch, request, data):
  e = compareJson(data, request)
  if (len(e) > 0):
    for g in client.guilds:
      if g.name == 'Toronja Chan':
        canal = discord.utils.get(g.channels, name="new-set-previews")
        for i in e:
          await send_card(i, canal)

def parseCard(b, b_pos):
    carta = b['data'][b_pos]
    name = ''
    types = ''
    power = '0'
    toughness = '0'
    mana_cost = '0'
    oracle_text = 'Vanilla'
    image = 'No Image available'
    modal = False
    secondface = None
    Set = b['data'][b_pos]['set_name']
    if 'card_faces' in carta:
        secondface = returnstruct(0, 0, 0, 0, 0, 0, 0, 0, 0)
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
    return (returnstruct(name, mana_cost, types, oracle_text, power, toughness, image, modal, secondface, Set))


def compareJson(a, b):
  b_pos = 0
  arr = []
  if (len(a['data']) <= len(b['data'])):
    for i in range(0, len(a['data'])):
      if b_pos < len(b['data']):
        while ((b_pos < len(b['data']) and (a['data'][i]["collector_number"]) != b['data'][b_pos]["collector_number"])):
          new_card = parseCard(b, b_pos)
          arr.append(new_card)
          b_pos += 1
        b_pos += 1
    while (b_pos < len(b['data'])):
      new_card = parseCard(b, b_pos)
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

client.run(token)