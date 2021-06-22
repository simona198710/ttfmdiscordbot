Input discord and tt.fm auth info in config.ini

Dont put updateSpeedInSeconds too low, it is not a async request and will lock up your bot.

May make it async later if the api is too slow.

If shouldSaveTrackConfig is enabled the bot will save the track configuration in a json-file for dj in tracks-folder, to avoid having to make api requests to the apple or spotify apis to get track info.

Its doing this because tt.fm is very picky about the format, it needs more info than just a track id or track isrc, it also needs track length, name, artist etc. 

So the bot saves this information when its emitted on the socket, so it can be reused later. 

Adding support for fetching this from the apple, spotify and soundcloud apis later may be possible.

Commads:

```
!manualUpdate
```

Used to manually update rooms info.

```
!connect <roomName>
```

To connect to a room, use room name or room slug

```
!disconnect
```

Disconect from room

```
!joinDj <djSlot>
```

Will pick a random track from your tracks-folder, so will need at least one track in there.

```
!addTrack <isrc>
```

isrc is optional, if skipped it will pick a random track from track folder.

```
!leaveDJ
```
Leave the dj position

```
!sendChat <message>
```

Chat messages will be sent to the channel configured in chatChannel, all other events will be sent to eventsChannel.
Room updates(new rooms and room number of members) will be posted to roomChannel, old embeds will be edited.
