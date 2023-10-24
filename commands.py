from discord import app_commands
import discord
from pymongo import MongoClient
from decouple import config
from WebAccess import *
import requests

tree = app_commands.CommandTree(discordClient)

@tree.command(name="add_set", description="adds a Magic set to the list of listened sets (max 3)")
async def add_set(interaction:discord.Interaction, card_set: str):
    request = requests.get('https://api.scryfall.com/sets/' + card_set)
    if (request.status_code == 200):
        setInfo = request.json()
        if setInfo['object'] == 'set':
            server = serverCol.find_one({"Name": interaction.guild.name})
            if server.get('Sets'):
                if len(server['Sets']) < 3:
                    serverCol.update_one({'Name': server['Name']}, {"$set": {'Sets': (server['Sets'].append(card_set))}})
                    await interaction.response.send_message(setInfo['name'].upper() + ' added to the list')
                else:
                    await interaction.response.send_message('Server exceeds the maximum amount of listened sets, remove one before adding another')
            else:
                serverCol.update_one({'Name': server['Name']}, {"$set": {'Sets': [card_set]}})
                await interaction.response.send_message(setInfo['name'] + ' added to the list')
    else:
        await interaction.response.send_message('Error: set not found. Make sure that you wrote the set code properly and try again')
    
@tree.command(name="remove_set", description="removes a Magic set from the list of listened sets")
async def remove_set(interaction:discord.Interaction, card_set: str):
    server = serverCol.find_one({'Name': interaction.guild.name})
    if card_set in server['Sets']:
        serverCol.update_one({'Name': server['Name']}, {"$set": {'Sets': (server['Sets'].remove(card_set))}})
        await interaction.response.send_message('Set removed succesfully')
    else:
        await interaction.response.send_message("Error: set is not in this server's list")

@tree.command(name="set_channel", description="Sets the server channel where the new cards will be posted")
async def set_channel(interaction:discord.Interaction):
    server = serverCol.find_one({'Name': interaction.guild.name})
    serverCol.update_one({'Name': server['Name']}, {"$set": {'Spoiler_channel': interaction.channel_id}})
    await interaction.response.send_message("Channel updated succesfully")

    
