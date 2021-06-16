import discord
from discord.ext import commands
import time
import config
import asyncio
import sys
import datetime
import os
import random
import copy
import json
import traceback
import requests
import util

roomEmbeds = {}
allCurrentRooms = {}

class roomMonitor(commands.Cog):
	
	def is_allowedRole(ctx):
				
		groups = ctx.message.author.roles
		admin = False
		for group in groups:
			if group.permissions.manage_guild:
				admin = True
		if str(ctx.message.guild.owner_id) == str(ctx.message.author.id):
			admin = True
		if admin:
			return True
				
		return False
	
	async def updateRoomsFromAPI(self):
		
		global allCurrentRooms
		
		try:
			#To prevent misconfigured bots spamming the api
			roomChannelObj = self.bot.get_channel(int(config.config['SETTINGS']['roomChannel'].strip()))
			if roomChannelObj is None:
				print("Unable to get room channel, skipping api lookup")
				return {}
			if str(config.config['SETTINGS']['auth'].strip()) == "":
				print("Auth not set, skipping api lookup")
				return {}
			if str(config.config['SETTINGS']['auth'].strip()) == "put auth here":
				print("Auth not set, skipping api lookup")
				return {}
			
			print("Fetching info from api")
			headers = {"authorization": "Bearer "+str(config.config['SETTINGS']['auth'].strip())}
			response = requests.get('https://rooms.prod.tt.fm/rooms',headers=headers)
			result = response.json()
			
			allCurrentRooms = result["rooms"]
			return result["rooms"]
		except:
			traceback.print_exc()
			return {}
	
	async def doUpdate(self):
		global roomEmbeds
		
		try:
		
			if roomEmbeds == {}:
				roomEmbeds["rooms"] = {}
			
			roomChannelObj = self.bot.get_channel(int(config.config['SETTINGS']['roomChannel'].strip()))
			
			rooms = await self.updateRoomsFromAPI()
			
			for room in rooms:
				if room["type"] == "PUBLIC":
					users = int(room["numberOfUsersInRoom"])
					if (str(room["neverSuspended"]) == "True") or (users > 0):
						roomDesc = str(room["description"])
						currentSong = str(room["songInfo"]["title"])
						emoji=""
						
						if room["name"] in roomEmbeds["rooms"]:
							if int(roomEmbeds["rooms"][room["name"]]["users"]) < int(users):
								emoji="⬆️"
							elif int(roomEmbeds["rooms"][room["name"]]["users"]) > int(users):
								emoji="⬇️"
						
						embed = discord.Embed(title=str(room["name"]),description="Description: "+str(roomDesc)+"\nIn Room: "+str(users)+" "+str(emoji)+"\nCurrent Song: "+str(currentSong))
						if not room["name"] in roomEmbeds["rooms"]:
							sentMsg = await roomChannelObj.send(embed=embed)
							roomEmbeds["rooms"][room["name"]] = {}
							roomEmbeds["rooms"][room["name"]]["msgID"] = sentMsg.id
							roomEmbeds["rooms"][room["name"]]["users"] = int(users)
						else:
							try:
								messageObj = await roomChannelObj.fetch_message(int(roomEmbeds["rooms"][room["name"]]["msgID"]))
								await messageObj.edit(embed=embed)
							except:
								sentMsg = await roomChannelObj.send(embed=embed)
								roomEmbeds["rooms"][room["name"]]["msgID"] = sentMsg.id
			
			#Delete embeds of rooms no longer existing
			roomEmbedsCOPY = copy.deepcopy(roomEmbeds)
			for oldRoom in roomEmbedsCOPY["rooms"]:
				roomFound = False
				for newRoom in rooms:
					if oldRoom == newRoom["name"]:
						roomFound = True
						break
				
				if not roomFound:
					try:
						messageObjToDelete = await roomChannelObj.fetch_message(int(roomEmbeds["rooms"][oldRoom]["msgID"]))
						await messageObjToDelete.delete()
					except:
						traceback.print_exc()
						print("Unable to delete old embed, maybe manually removed?")
					del roomEmbeds["rooms"][oldRoom]
			
			util.save_data(roomEmbeds, "roomEmbeds")
		except:
			traceback.print_exc()
	
	@commands.command(pass_context=True, brief="", name='manualUpdate')
	@commands.check(is_allowedRole)
	async def manualUpdateCMD(self,ctx):
		await self.doUpdate()
		await ctx.send("Rooms updated")
		
	async def monitor(self,bot):
		
		await asyncio.sleep(30)
		
		while True:
			await self.doUpdate()
			
			await asyncio.sleep(int(config.config['SETTINGS']['updateSpeedInSeconds'].strip()))
			
	def __init__(self,bot):
		global roomEmbeds
		
		self.bot = bot
		
		try:
			roomEmbeds = util.load_data('roomEmbeds')
		except:
			roomEmbeds = {}
		
		bot.loop.create_task(self.monitor(bot))
		
		print("Room Monitor plugin started")
		
def setup(bot):
	bot.add_cog(roomMonitor(bot))