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

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio as PubNub
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubException
import uuid
import aiohttp

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
		roomChannelObj = sio.bot.get_channel(int(config.config['SETTINGS']['eventsChannel'].strip()))
		await roomChannelObj.send("New user connected "+str(data["nickname"]))
	
	@sio.event
	async def sendNextTrackToPlay(data):
		if str(config.config['SETTINGS']['shouldSaveTrackConfig'].strip()).lower() == "true":
			filename = "tracks/"+str(data["track"]["isrc"])+".json"
			if not os.path.isfile(filename):
				with open(filename, 'w') as outfile:
					json.dump(data["track"], outfile)
			
	''' #Using pubnub for chats
	@sio.event
	async def chatMessage(data):
		print('Message received: '+str(data))
		roomChannelObj = sio.bot.get_channel(int(config.config['SETTINGS']['roomChannel'].strip()))
		await roomChannelObj.send("New chat message from "+str(data["userName"])+":"+str(data["message"]))
	'''
	
	@sio.event
	async def connect():
		global room
		
		if not room is None:
		
			print('Connected to: '+str(room))
			roomChannelObj = sio.bot.get_channel(int(config.config['SETTINGS']['eventsChannel'].strip()))
			await roomChannelObj.send('Connected to: '+str(room))
	
	@sio.event
	async def disconnect():
		print('Disconnected from: '+str(room))
		roomChannelObj = sio.bot.get_channel(int(config.config['SETTINGS']['eventsChannel'].strip()))
		await roomChannelObj.send('Disconnected from: '+str(room))
	
	@commands.command(pass_context=True, brief="", name='disconnect')
	@commands.check(is_allowedRole)
	async def disconnectFromRoomCMD(self,ctx):
		global room
		
		await sio.disconnect()
		self.bot.currentDjSpot = None
		room = None
		if not self.bot.pubnub is None:
			if not self.bot.pubnubRoom is None:
				self.bot.pubnub.unsubscribe().channels(self.bot.pubnubRoom).execute()
				self.bot.pubnubRoom = None
		
	async def connectPubNub(self,channel):
		
		if self.bot.pubnub is None:
		
			pnconfig = PNConfiguration()
			
			session_timeout = aiohttp.ClientTimeout(total=5)
			headers = {"authorization": "Bearer "+str(config.config['SETTINGS']['auth'].strip())}
			try:
				async with aiohttp.ClientSession(timeout=session_timeout) as session:
					async with session.get("https://api.prod.tt.fm/pubnub/token",headers=headers) as responseRaw:
						response = await responseRaw.json()
			except:
				response = {}
			
			self.bot.auth_key=response["pubnubAuthToken"]
			self.bot.publish_key=response["pubnubPublishKey"]
			self.bot.subscribe_key=response["pubnubSubscribeKey"]
			self.bot.uuid=response["userUuid"]
			
			pnconfig.subscribe_key = self.bot.subscribe_key
			pnconfig.publish_key = self.bot.publish_key
			pnconfig.uuid = self.bot.uuid
			pnconfig.auth_key = self.bot.auth_key
			
			pubnub = PubNub(pnconfig)
			
			def pubnub_publish_callback(self,envelope, status):
				if not status.is_error():
					print("Message sent ok with pubnub")
					pass
				else:
					print("Message sent error with pubnub")
					pass
			
			class PubNubSubscribeCallback(SubscribeCallback):
				def presence(self, pubnub, presence):
					pass

				def status(self, pubnub, status):
					if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
						print("Connection lost to pubnub")
						pass
						
					elif status.category == PNStatusCategory.PNConnectedCategory:
						print("Is connected to pubnub")
						pubnub.bot.pubnubRoom = str(channel) 
						pass
						
					elif status.category == PNStatusCategory.PNReconnectedCategory:
						print("Reconnected to pubnub")
						pass
						
					elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
						print("Decrypt error with pubnub")
						pass

				def message(self, pubnub, message):
					print("New pubnub msg: "+str(message.message))
					roomChannelObj = pubnub.bot.get_channel(int(config.config['SETTINGS']['chatChannel'].strip()))
					
					pubnub.bot.loop.create_task(roomChannelObj.send("New chat message from "+str(message.message["userName"])+": " +str(message.message["content"])))
			
			pubnub.add_listener(PubNubSubscribeCallback())
			pubnub.bot = self.bot
			self.bot.pubnub = pubnub
			self.bot.pubnub_publish_callback = pubnub_publish_callback
		
		session_timeout = aiohttp.ClientTimeout(total=5)
		headers = {"authorization": "Bearer "+str(config.config['SETTINGS']['auth'].strip())}
		try:
			async with aiohttp.ClientSession(timeout=session_timeout) as session:
				async with session.get("https://api.prod.tt.fm/users/profile",headers=headers) as responseRaw:
					response = await responseRaw.json()
		except:
			response = {}
		
		self.bot.pubnub_chat_userId=response["userId"]
		self.bot.pubnub_chat_userName=response["nickname"]
		self.bot.pubnub_chat_avatarId=int(response["avatarId"]) -1 #Seems like pubnub is starting from 0 but profile from 1?
		
		self.bot.pubnub.subscribe().channels(str(channel)).execute()
	
	@commands.command(pass_context=True, brief="", name='leaveDJ')
	@commands.check(is_allowedRole)
	async def leaveDjCMD(self,ctx):
		await sio.emit("leaveDjSeat",{"userId":int(self.bot.pubnub_chat_userId)})
		self.bot.currentDjSpot = None
		await ctx.send("Dj Spot Left")
	
	@commands.command(pass_context=True, brief="", name='joinDJ')
	@commands.check(is_allowedRole)
	async def joinDjCMD(self,ctx,spot):
		
		try:
			spot = int(spot)-1 #Begins at 0 in the socket
		except:
			return await ctx.send("Invalid spot, needs to be a number from 1 to 3")
		
		if spot < 0:
			return await ctx.send("Invalid spot, needs to be a number from 1 to 3")
		if spot > 2:
			return await ctx.send("Invalid spot, needs to be a number from 1 to 3")
		
		trackData = None
		random_file=random.choice(os.listdir("tracks"))
		with open("tracks/"+random_file) as json_file:
			trackData = json.load(json_file)
		trackTemp = {"nextDjSeatKey": int(spot),"trackUrl": "not applicable","track": trackData}
		
		#42["takeDjSeat",{"djSeatKey":0,"userId":2809,"avatarId":"7","nextTrack":{"nextDjSeatKey":0,"trackUrl":"not applicable","track":{"version":2,"duration":226.76,"genre":"","id":"1440734692","musicProvider":"apple","title":"Amerika","user":{"id":"unknown","name":"Rammstein"},"isNextToPlay":false,"isrc":"DEN120404987"}},"nickname":"Simon"}]
		await sio.emit("takeDjSeat",{"djSeatKey":int(spot),"userId":int(self.bot.pubnub_chat_userId),"avatarId":int(self.bot.pubnub_chat_avatarId),"nextTrack":trackTemp,"nickname":str(self.bot.pubnub_chat_userName)})
		self.bot.currentDjSpot = spot
		await ctx.send("Dj Spot Joined")
	
	@commands.command(pass_context=True, brief="", name='addTrack')
	@commands.check(is_allowedRole)
	async def addTrackCMD(self,ctx,isrc=None):
		
		if self.bot.currentDjSpot is None:
			return await ctx.send("You need to be dj to do this")
		
		trackData = None
		if isrc is None:
			random_file=random.choice(os.listdir("tracks"))
			with open("tracks/"+random_file) as json_file:
				trackData = json.load(json_file)
		else:
			try:
				with open("tracks/"+str(isrc)+".json") as json_file:
					trackData = json.load(json_file)
			except:
				return await ctx.send("Invalid isrc")
		
		trackTemp = {
			"track": trackData,
			"trackUrl": "not applicable",
			"userId": int(self.bot.pubnub_chat_userId),
			"userUuid": str(self.bot.uuid),
			"djSeatKey": int(self.bot.currentDjSpot)
		}		
		
		await sio.emit("sendNextTrackToPlay",trackTemp)
		await ctx.send("Track added")
	
	@commands.command(pass_context=True, brief="", name='sendChat')
	@commands.check(is_allowedRole)
	async def sendChatCMD(self,ctx,*msg):
		
		chatMessage = " ".join(msg)
		if not self.bot.pubnub is None:
			if not self.bot.pubnubRoom is None:
				asyncio.ensure_future(self.bot.pubnub.publish().channel(str(self.bot.pubnubRoom)).message({"content":str(chatMessage),"id":str(uuid.uuid4()),"avatarId":str(self.bot.pubnub_chat_avatarId),"userName":str(self.bot.pubnub_chat_userName),"userId":int(self.bot.pubnub_chat_userId),"color":"#2DF997","userUuid":str(self.bot.uuid)}).future()).add_done_callback(self.bot.pubnub_publish_callback)
			else:
				await ctx.send("Error not connected to chat")
		else:
			await ctx.send("Error not connected to chat")
		
	@commands.command(pass_context=True, brief="", name='connect')
	@commands.check(is_allowedRole)
	async def connectToRoomCMD(self,ctx,*roomName):
		
		global room
		
		url = None
		path = None
		slug = None
		for availableRoom in ctx.bot.extensions['plugins.roomMonitor'].allCurrentRooms: #Use the data from the other cog, since it probably have the info already
			if availableRoom["type"] == "PUBLIC":
				if (availableRoom["name"] == str(" ".join(roomName)).strip()) or (availableRoom["slug"] == str(" ".join(roomName)).strip()):
					url = availableRoom["socketDomain"]
					#path = availableRoom["socketEndpoint"].replace('https://'+str(url),"") #No longer working, socketEndpoint is no longer in the api.
					path = str(availableRoom["slug"])+'/socket.io'
					slug = str(availableRoom["slug"])
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
		
		await self.connectPubNub(availableRoom["slug"])
		
	def __init__(self,bot):
		
		self.bot = bot
		self.bot.pubnub = None
		self.bot.pubnubRoom = None
		self.bot.currentDjSpot = None
		
		print("Room Connect plugin started")
		
def setup(bot):
	bot.add_cog(roomConnect(bot))