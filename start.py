import discord
import os
import asyncio
import config
from discord.ext import commands
import sys

from os import listdir
from os.path import isfile, join
import traceback
import time
import datetime

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=str(config.prefix), case_insensitive=True,heartbeat_timeout=300,intents=intents)
bot.remove_command("help")

@bot.event
async def on_ready():
	print("\nLogged in as:")
	print(" Username",bot.user.name)
	print(" User ID",bot.user.id)
	print("To invite the bot in your server use this link:\n https://discordapp.com/oauth2/authorize?&client_id="+str(bot.user.id)+"&scope=bot&permissions=0")

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		pass
	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send("Invalid syntax")
	elif isinstance(error, commands.BadArgument):
		await ctx.send("Invalid syntax")
	else:
		print(error, ctx)

def run_client(token):
	global bot
	
	while True:
		loadPlugins()
		loop = asyncio.get_event_loop()
		try:
			loop.run_until_complete(bot.start(token))
		except Exception as e:
			print("Error", e)
			loop.run_until_complete(bot.logout())

def loadPlugins():
	
	bot.load_extension("plugins.roomMonitor")
	bot.load_extension("plugins.roomConnect")	
	
if __name__ == "__main__":
			
	run_client(config.discordtoken)