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
            guild = guilds.find_one({"_id": interaction.guild.id})
            if guild.get('Sets'):
                if len(guild['Sets']) < 3:
                    guilds.update_one({'_id': guild['_id']}, {"$set": {'Sets': (guild['Sets'].append(card_set))}})
                    await interaction.response.send_message(setInfo['name'].upper() + ' added to the list')
                else:
                    await interaction.response.send_message('guild exceeds the maximum amount of listened sets, remove one before adding another')
            else:
                guilds.update_one({'_id': guild['_id']}, {"$set": {'Sets': [card_set]}})
                await interaction.response.send_message(setInfo['name'] + ' added to the list')
    else:
        await interaction.response.send_message('Error: set not found. Make sure that you wrote the set code properly and try again')
    
@tree.command(name="remove_set", description="removes a Magic set from the list of listened sets")
async def remove_set(interaction:discord.Interaction, card_set: str):
    guild = guilds.find_one({'_id': interaction.guild.id})
    if card_set in guild['Sets']:
        guilds.update_one({'_id': guild['_id']}, {"$set": {'Sets': (guild['Sets'].remove(card_set))}})
        await interaction.response.send_message('Set removed succesfully')
    else:
        await interaction.response.send_message("Error: set is not in this guild's list")

@tree.command(name="set_channel", description="Sets the guild channel where the new cards will be posted")
async def set_channel(interaction:discord.Interaction):
    guild = guilds.find_one({'Name': interaction.guild.name})
    guilds.update_one({'_id': guild['_id']}, {"$set": {'Spoiler_channel': interaction.channel_id}})
    await interaction.response.send_message("Channel updated succesfully")

@tree.command(name="help", description="Gives you instructions on how to use this bot")
async def help(interaction:discord.Interaction):
    await interaction.response.send_message("First, the bot needs a designated text channel to post the new card, you can \
                                            set or modify this channel with the command set_channel. To manage the sets \
                                            that the bot will keep track of, use the add_set or remove_set command")
