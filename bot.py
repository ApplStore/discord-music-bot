import discord
import youtube_dl
import asyncio
import random
from discord.channel import VoiceChannel
from discord.ext import commands

#params and high-level variables
client = commands.Bot(command_prefix=".")

embed_red = 0xed4245
embed_blue = 0x319dda
embed_green = 0x3ccb77
embed_yellow = 0xffe366

media_queue = []
looped_track = []

is_looped = False
is_rewind = False


FFEMPG_OPTIONS = {"before_options":"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5","options": "-vn"}
YDL_OPTIONS = {"format": "bestaudio", "--write-thumbnail":True}


#Bot ready
@client.event
async def on_ready():
    print("Frequency by ApplStore - v.1.2")
    print("")
    print("<SYS> | Bot has started service")
    print("-- -- -- -- -- -- -- -- -- -- --")


#non-async functions

#check for generic url
def yturl(url):
    extractors = youtube_dl.extractor.gen_extractors()
    for e in extractors:
        if e.suitable(url) and e.IE_NAME != 'generic':
            return True
    return False


#play next song in the queue
def next_song(ctx):

    try:
        global is_rewind
        if is_rewind == True or is_looped == True:
            is_rewind = False
            source = asyncio.run(discord.FFmpegOpusAudio.from_probe(looped_track[0]["formats"][0]["url"], **FFEMPG_OPTIONS))
            ctx.voice_client.stop()
            ctx.voice_client.play(source, after=lambda e:next_song(ctx))

        elif len(media_queue) == 0:
            media_queue.clear()
            try:
              ctx.voice_client.stop()
            except AttributeError:
              pass

        elif len(media_queue) >= 1 and is_looped == False:
            source = asyncio.run(discord.FFmpegOpusAudio.from_probe(media_queue[0]["formats"][0]["url"], **FFEMPG_OPTIONS))
            looped_track.clear()
            looped_track.append(media_queue[0])
            embed=discord.Embed(title="Now playing:", url=f"https://www.youtube.com/watch?v={media_queue[0]['id']}", description = media_queue[0]["title"], color=embed_green)
            embed.set_thumbnail(url=media_queue[0]["thumbnail"])
            embed.set_footer(text="Frequency bot by ApplStore")
            asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), client.loop)
            media_queue.pop(0)
            ctx.voice_client.stop()
            ctx.voice_client.play(source, after=lambda e:next_song(ctx))

    except Exception as e:
        embed=discord.Embed(title="An unexpected error occurred", description=e, color=embed_red)
        asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), client.loop)


#--------------Main Voice Client----------------

#play, main cmd
@client.command(name="play", aliases=["p"])
async def play(ctx, *, url = None):

    try:

        if url == None:
            embed=discord.Embed(title="Play [media]", description="For playing music in voice chats", color=embed_blue)
            await ctx.send(embed=embed)
            return

        if ctx.author.voice is None:
            embed=discord.Embed(title="Please connect to a voice channel first", description="Could not play media", color=embed_red)
            await ctx.send(embed=embed)
            return
        

        try:
            await ctx.message.add_reaction("⏳")
            
            #check for YouTube
            if yturl(url) == True:
                with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)

                    if "entries" in info:
                        embed=discord.Embed(title="Loading playlist...", description="This might take a while", color=embed_blue)
                        await ctx.send(embed=embed)
                        for individual_info in info["entries"]:
                            media_queue.append(individual_info)

                        if ctx.voice_client is None:
                            embed=discord.Embed(title="Playlist loaded, now playing:", url=f"https://www.youtube.com/watch?v={media_queue[0]['id']}", description = media_queue[0]["title"], color=embed_green)
                            embed.set_thumbnail(url=media_queue[0]["thumbnail"])
                            embed.set_footer(text="Frequency bot by ApplStore")
                            await ctx.send(embed=embed)

                            source = await discord.FFmpegOpusAudio.from_probe(media_queue[0]["formats"][0]["url"], **FFEMPG_OPTIONS)
                            looped_track.clear()
                            looped_track.append(media_queue[0])
                            media_queue.pop(0)

                        else:
                            embed=discord.Embed(title="Playlist loaded", description = "Tracks are places in the queue", color = embed_blue)
                            await ctx.send(embed=embed)
                            return

                    else:
                        source = await discord.FFmpegOpusAudio.from_probe(info["formats"][0]["url"], **FFEMPG_OPTIONS)



            else:
                with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(f"ytsearch:{url}", download=False)['entries'][0]
                    source = await discord.FFmpegOpusAudio.from_probe(info["formats"][0]["url"], **FFEMPG_OPTIONS)
            

        except:
            embed=discord.Embed(title="Please enter a valid media source", description="Could not play media", color=embed_red)
            await ctx.send(embed=embed)
            return
        
        if ctx.voice_client and ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel:
            if ctx.voice_client.source != None:
                media_queue.append(info)
                embed=discord.Embed(title="Media found:", url=f"https://www.youtube.com/watch?v={info['id']}", description = info["title"], color=embed_blue)
                embed.add_field(name="Position in queue:", value=len(media_queue), inline=True)
                embed.set_thumbnail(url=info["thumbnail"])
                embed.set_footer(text="Frequency bot by ApplStore")
                
                await ctx.send(embed=embed)
                return
        
        elif ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        
        else:
            embed=discord.Embed(title="Frequency is already playing in another channel", description="Disconnect it or join the channel where it is located", color=embed_red)
            await ctx.send(embed=embed)
            return
        
        try:
            embed=discord.Embed(title="Now playing:", url=f"https://www.youtube.com/watch?v={info['id']}", description = info["title"], color=embed_green)
            embed.set_thumbnail(url=info["thumbnail"])
            embed.set_footer(text="Frequency bot by ApplStore")
            await ctx.send(embed=embed)
        except:
            pass
    
        looped_track.clear()
        looped_track.append(info)
        ctx.voice_client.stop()
        ctx.voice_client.play(source, after=lambda e:next_song(ctx))

    except Exception as e:
        embed=discord.Embed(title="An unexpected error occurred", description=e, color=embed_red)
        await ctx.send(embed=embed)




#Disconnect
@client.command()
async def disconnect(ctx):
    try:
        if ctx.voice_client is None:
          embed=discord.Embed(title="The player is not connected to a VC.", color=embed_red)
          await ctx.send(embed=embed)
        else:  
          media_queue.clear()
          global is_looped
          is_looped = False
          await ctx.voice_client.disconnect()
          await ctx.send("Successfully disconnected!")
          print("<LOG> | disconnect >>", ctx.author, "has disconnected the player")
    except Exception as e:
        embed=discord.Embed(title="An unexpected error occurred", description=e, color=embed_red)
        await ctx.send(embed=embed)


#Resume
@client.command()
async def resume(ctx):
    try:
      if ctx.voice_client is None:
          embed=discord.Embed(title="The player is not connected to a VC.", color=embed_red)
          await ctx.send(embed=embed)
      else:  
        ctx.voice_client.resume()
        embed=discord.Embed(title="Player resumed", color=embed_blue)
        await ctx.send(embed=embed)
        print("<LOG> | resume >>", ctx.author, "has resumed the player")
    except Exception as e:
        embed=discord.Embed(title="An unexpected error occurred", description=e, color=embed_red)
        await ctx.send(embed=embed)


#Pause
@client.command()
async def pause(ctx):
    try:
      if ctx.voice_client is None:
          embed=discord.Embed(title="The player is not connected to a VC.", color=embed_red)
          await ctx.send(embed=embed)
      else:  
        ctx.voice_client.pause()
        embed=discord.Embed(title="Player paused", color=embed_blue)
        await ctx.send(embed=embed)
        print("<LOG> | pause >>", ctx.author, "paused the player")
    except Exception as e:
        embed=discord.Embed(title="An unexpected error occurred", description=e, color=embed_red)
        await ctx.send(embed=embed)


#stop
@client.command()
async def stop(ctx):
    try:
      if ctx.voice_client is None:
          embed=discord.Embed(title="The player is not connected to a VC.", color=embed_red)
          await ctx.send(embed=embed)
      else:  
          media_queue.clear()
          global is_looped
          is_looped = False
          ctx.voice_client.stop()
          embed=discord.Embed(title="Player stopped", color=embed_blue)
          await ctx.send(embed=embed)
          print("<LOG> | stop >>", ctx.author, "stopped the player")
    except Exception as e:
        embed=discord.Embed(title="An unexpected error occurred", description=e, color=embed_red)
        await ctx.send(embed=embed)



#volume
@client.command(name="volume", aliases=["vol"])
async def volume(ctx, volume_input=None):
    #try:
        if volume_input == "reset" or volume_input == "original":
            await discord.PCMVolumeTransformer.volume(1.0)
            await ctx.send(":speaker: Set volume to original value")
        elif 0 <= float(volume_input) <= 100:
            discord.PCMVolumeTransformer.volume(original=ctx.voice_client.source, volume = float(volume_input) / 100)
            await ctx.send(f":speaker: Set volume to {volume_input}%")
        print("<LOG> | volume >>", ctx.author, "changed the players volume")
    #except Exception as e:
        #embed=discord.Embed(title="An unexpected error occurred", description=e, color=embed_red)
        #await ctx.send(embed=embed)



#skip
@client.command()
async def skip(ctx):
    try:
        if ctx.voice_client.is_playing():
            if len(media_queue) >= 1:
                global is_looped
                is_looped = False
                looped_track.clear()
                ctx.voice_client.stop()
            
            else:
                embed=discord.Embed(title="There are no songs in the queue", description="Add a song to the queue by using the play command", color=embed_red)
                await ctx.send(embed=embed)
    except:
        embed=discord.Embed(title="The player is not currently playing", color=embed_red)
        await ctx.send(embed=embed)


#loop
@client.command()
async def loop(ctx):
    try:
        if ctx.voice_client.is_playing():
            global is_looped
            is_looped = True
            embed=discord.Embed(title="Looped the current song", description = "Use the `unloop` or `skip` command to unloop the track.", color=embed_blue)
            await ctx.send(embed=embed)
            
        else:
            embed=discord.Embed(title="The player is not currently playing", color=embed_red)
            await ctx.send(embed=embed)

    except:
        pass


#unloop
@client.command()
async def unloop(ctx):
    try:
        if ctx.voice_client.is_playing():
            global is_looped
            is_looped = False
            embed=discord.Embed(title="Unlooped the current track", color=embed_blue)
            await ctx.send(embed=embed)
            
        else:
            embed=discord.Embed(title="The player is not currently playing", color=embed_red)
            await ctx.send(embed=embed)

    except:
        pass


#rewind
@client.command()
async def rewind(ctx):
    try:
        if ctx.voice_client.is_playing():
            global is_rewind
            is_rewind = True
            ctx.voice_client.stop()
            
        else:
            embed=discord.Embed(title="The player is not currently playing", color=embed_red)
            await ctx.send(embed=embed)

    except:
        pass


#Queue
@client.command()
async def queue(ctx):
    try:

        if media_queue == []:
            embed=discord.Embed(title="The queue is empty", description="Add a song to the queue by using the play command", color=embed_yellow)
            await ctx.send(embed=embed)
            return

        title_queue = []
        for i in media_queue:
            title_queue.append(i["title"])
        unformatted_queue = ["**%i:** %s" % (index + 1, value) for index, value in enumerate(title_queue)]
        formatted_queue = "\n".join(unformatted_queue)
        embed=discord.Embed(title="Current queue:", description=formatted_queue, color=embed_green)
        embed.set_footer(text="Frequency bot by ApplStore")
        await ctx.send(embed=embed)

    except Exception as e:
        embed=discord.Embed(title="An unexpected error occurred", description=e, color=embed_red)
        await ctx.send(embed=embed)


#skip
@client.command()
async def shuffle(ctx):
    try:
        if ctx.voice_client.is_playing():
            if len(media_queue) >= 1:
                key = random.random()
                random.shuffle(media_queue, lambda: key)

                embed=discord.Embed(title="Queue shuffled", description="Changes will take place with the next source", color=embed_blue)
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title="There are no songs in the queue", description="Add a song to the queue by using the play command", color=embed_red)
                await ctx.send(embed=embed)
    except:
        embed=discord.Embed(title="The player is not currently playing", color=embed_red)
        await ctx.send(embed=embed)



#-----------------------------------------
client.run(#insert token here)
