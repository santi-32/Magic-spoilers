from discord import app_commands
import discord
from WebAccess import *
import requests
from card_array_builder import getCardsInSet


tree = app_commands.CommandTree(discordClient)

@tree.command(name="add_set", description="adds a Magic set to the list of listened sets (max 3)")
async def add_set(interaction:discord.Interaction, card_set: str):
    card_set = card_set.upper()
    request = requests.get('https://api.scryfall.com/sets/' + card_set)
    if (request.status_code == 200):
        setInfo = request.json()
        if setInfo['object'] == 'set':
            if not card_set in cardDB.list_collection_names():
                await interaction.response.send_message("Building card database, this might take a bit...")
                newCards = await getCardsInSet(card_set)
                cardDB[card_set].insert_many(newCards)
            else:
                await interaction.response.send_message("Adding set to the list...")
            guild = guilds.find_one({"_id": interaction.guild.id})
            if guild.get('Sets'):
                if card_set in guild['Sets']:
                    await interaction.edit_original_response(content="This set is alredy on the list")
                elif len(guild['Sets']) < 3:
                    temp = guild['Sets'] #for some reason, 
                    temp.append(card_set)
                    guilds.update_one({'_id': guild['_id']}, {"$set": {'Sets': (temp)}})
                    await interaction.edit_original_response(content=(setInfo['name'] + ' added to the list'))
                else:
                    await interaction.edit_original_response(content='guild exceeds the maximum amount of listened sets, remove one before adding another')
            else:
                guilds.update_one({'_id': guild['_id']}, {"$set": {'Sets': [card_set]}})
                await interaction.edit_original_response(content=(setInfo['name'] + ' added to the list'))
        else:
            await interaction.response.send_message("Error: set not found. Make sure that you wrote the set code properly and try again") 
    else:
        await interaction.response.send_message('Error: set not found. Make sure that you wrote the set code properly and try again')
    
@tree.command(name="remove_set", description="removes a Magic set from the list of listened sets")
async def remove_set(interaction:discord.Interaction, card_set: str):
    card_set = card_set.upper()
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
    await interaction.response.send_message("First, the bot needs a designated text channel to post the new card, you can set or modify this channel with the command set_channel. To manage the sets that the bot will keep track of, use the add_set or remove_set command")
                                            
@tree.command(name="show_sets", description="Shows the list of sets that this server is subscribed to")
async def help(interaction:discord.Interaction):
    guild = guilds.find_one({"_id": interaction.guild.id})
    sets = guild.get('Sets')
    if not sets:
        print("is none")
        await interaction.response.send_message("this server is not subscribed to any set")
    elif len(sets) > 0:
        message = ""
        for s in sets:
            if message == "":
                message += s
            else:
                message += ", " + s
        await interaction.response.send_message("(" + message + ")")
    else:
        await interaction.response.send_message("this server is not subscribed to any set")
                                            
