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
import socketio

room = None

sio = socketio.AsyncClient(logger=True, engineio_logger=True)

class roomConnect(commands.Cog):
	
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
	
	@sio.event
	async def addAvatarToDancefloor(data):
		print('Message received: '+str(data))
		roomChannelObj = sio.bot.get_channel(int(config.config['SETTINGS']['roomChannel'].strip()))
		await roomChannelObj.send("New user connected "+str(data["nickname"]))
	
	@sio.event
	async def chatMessage(data):
		print('Message received: '+str(data))
		roomChannelObj = sio.bot.get_channel(int(config.config['SETTINGS']['roomChannel'].strip()))
		await roomChannelObj.send("New chat message from "+str(data["userName"])+":"+str(data["message"]))
	
	@sio.event
	async def connect():
		global room
		
		if not room is None:
		
			#print("Got connection")
			print('Connected to: '+str(room))
			roomChannelObj = sio.bot.get_channel(int(config.config['SETTINGS']['roomChannel'].strip()))
			await roomChannelObj.send('Connected to: '+str(room))
	
	@sio.event
	async def disconnect():
		print('Disconnected from: '+str(room))
		roomChannelObj = sio.bot.get_channel(int(config.config['SETTINGS']['roomChannel'].strip()))
		await roomChannelObj.send('Disconnected from: '+str(room))
	
	@commands.command(pass_context=True, brief="", name='disconnect')
	@commands.check(is_allowedRole)
	async def disconnectFromRoomCMD(self,ctx):
		global room
		
		await sio.disconnect()
		room = None
		
	@commands.command(pass_context=True, brief="", name='connect')
	@commands.check(is_allowedRole)
	async def connectToRoomCMD(self,ctx,*roomName):
		
		global room
		
		url = None
		path = None
		for availableRoom in ctx.bot.extensions['plugins.roomMonitor'].allCurrentRooms: #Use the data from the other cog, since it probably have the info already
			if availableRoom["type"] == "PUBLIC":
				if availableRoom["name"] == str(" ".join(roomName)).strip():
					url = availableRoom["socketDomain"]
					path = availableRoom["socketEndpoint"].replace('https://'+str(url),"")
					break
		
		if url is None:
			await ctx.send("Invalid room name")
			return False
		
		if not room is None:
			await sio.disconnect()
			room = None
		
		headers = {"authorization": "Bearer "+str(config.config['SETTINGS']['auth'].strip())}
		sio.bot = self.bot
		room = str(path)
		await sio.connect('https://'+str(url), socketio_path=path,headers=headers)
		
	def __init__(self,bot):
		
		self.bot = bot
		
		print("Room Connect plugin started")
		
def setup(bot):
	bot.add_cog(roomConnect(bot))