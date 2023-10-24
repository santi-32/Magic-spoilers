from discord import app_commands
import discord
from pymongo import MongoClient
from decouple import config

cluster = MongoClient(config('MONGOACCESS'))
serverCol = cluster["Discord"]["Servers"]
discordClient = discord.Client(intents=discord.Intents.default())
cardDB = cluster["Sets"]
token = config('TESTTOKEN')


