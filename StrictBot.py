'''
Created on Sep 14, 2020

@author: willg
'''

import discord
from discord.ext import tasks


import Shared
import sys
import atexit
import signal
import os
import GuildRestriction
import dill as p
from itertools import cycle

bot_invite_link = "https://discord.com/api/oauth2/authorize?client_id=774866940950872095&permissions=268544000&scope=bot"


has_loaded = False
testing_server = False
bot_key = None
testing_bot_key = None
private_info_file = "private.txt"

status_cycle = cycle(["Be nice!", "Admins do !info", "DM me for an invite link"])
    
restriction_data = None
restriction_data_file_path = Shared.restricted_data_pickle_path



client = discord.Client(intents=discord.Intents.all())


@client.event
async def on_message_edit(before, message:discord.Message):
    if message.guild == None:
        return
    if restriction_data == None:
        return
    if message.author.bot:
        return
    if message.guild.id not in restriction_data:
        restriction_data[message.guild.id] = GuildRestriction.GuildRestriction(message.guild)

    await restriction_data[message.guild.id].restriction_filter_check(message)
        
    
@client.event
async def on_message(message: discord.Message):            
    if message.author.id == 706120725882470460 and message.content == "!debug":
        await badwolf_debug(message)
        return
    if message.author.id == 706120725882470460 and message.content == "!addtablebotterms":
        old_len = len(restriction_data[message.guild.id].whitelists[0])
        await add_all_tablebot_terms(restriction_data[message.guild.id].whitelists[0])
        new_len = len(restriction_data[message.guild.id].whitelists[0])
        await message.channel.send(f"Done. Added {new_len - old_len} terms.")
        return
    if restriction_data == None:
        return
    if message.author.bot:
        return
    
    if message.guild == None:
        try:
            await message.channel.send(bot_invite_link)
            return
        except:
            return


    
    if message.guild.id not in restriction_data:
        restriction_data[message.guild.id] = GuildRestriction.GuildRestriction(message.guild)

    if await restriction_data[message.guild.id].settings_menu(message):
        return
    
    await restriction_data[message.guild.id].restriction_filter_check(message)
        

@tasks.loop(seconds=30)
async def routine_unmute_checks():
    if restriction_data != None:
        for guild_instance in restriction_data.values():
            await guild_instance.unmute_check()


@tasks.loop(hours=3)
async def backup_data():
    Shared.backup_files(Shared.backup_file_list)
    dump_restriction_data()

async def badwolf_debug(message):
    global has_loaded
    to_send = "Has loaded: " + str(has_loaded) + "\n\n"
    if has_loaded:
        try:
            for g in restriction_data.values():
                try:
                    to_send += str(g)
                except Exception as ex:
                    to_send += Shared.traceback_str(ex)
                to_send += "\n\n\n\n"
        except Exception as ex_2:
            to_send += Shared.traceback_str(ex_2)
        
        if to_send == "":
            to_send += "NO DATA?"
            
    Shared.log_event(to_send)
    await Shared.safe_send(message, to_send)
    
async def add_all_tablebot_terms(the_set):
    zero_arg_commands = ["?reset", "?undo", "?races", "?vr", "?wws", "?ctwws", "?mii", "?battles", "?fc", "?allplayers", "?ap", "?fcs", "?rxx", "?races", "?tt", "?wp", "?dcs"]
    for cur_command in zero_arg_commands:
        the_set.add(cur_command)
        
    one_arg_commands = [("?theme", range(1, 12)),
                        ("?graph", range(1, 3)),
                        ("?earlydc", range(1, 4)),
                        ("?size", range(1, 13)),
                        ("?removerace", range(1, 13)),
                        ("?rr", range(1, 13)),
                        ("?sw", ["FFA 12", "2v2 6", "3v3 4", "4v4 3", "6v6 2"])]
    for command_pack in one_arg_commands:
        the_set.add(command_pack[0])
        cur_command = command_pack[0]
        for x in command_pack[1]:
            the_set.add(f"{command_pack[0]} {x}")
    
    two_arg_commands = [("?changeroomsize", range(1, 13), range(1, 13)),
                        ("?penalty", range(1, 14), range(-20, 21)),
                        ("?dc", range(1, 12), ["on", "before"]),
                        ("?changetag", range(1,14), [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]),
                        ("?changeroomsize", range(1, 13), range(1, 13))]
    for command_pack in two_arg_commands:
        the_set.add(command_pack[0])
        cur_command = command_pack[0]
        for x in command_pack[1]:
            for y in command_pack[2]:
                the_set.add(f"{command_pack[0]} {x} {y}")
                            
    
    three_arg_commands = [("?quickedit", range(1, 14),  range(1, 13),  range(1, 13)),
                          ("?edit", range(1, 14),  range(1, 13),  range(0, 61))]
    for command_pack in three_arg_commands:
        the_set.add(command_pack[0])
        cur_command = command_pack[0]
        for x in command_pack[1]:
            for y in command_pack[2]:
                for z in command_pack[3]:
                    the_set.add(f"{command_pack[0]} {x} {y} {z}")
    


@tasks.loop(seconds=20)
async def statuses():
    game = discord.Game(next(status_cycle))
    await client.change_presence(status=discord.Status.online, activity=game)
    
@tasks.loop(hours=24)
async def clear_spam_filters():
    global restriction_data
    try:
        for guild in restriction_data.values():
            try:
                guild.clear_spam()
            except:
                pass
    except: #Dict changed on iteration
        pass
            
            
        
def private_data_init():
    global testing_bot_key
    global bot_key
    with open(private_info_file, "r") as f:
        testing_bot_key = f.readline().strip("\n")
        bot_key = f.readline().strip("\n")



def dump_restriction_data():
    if restriction_data != None:
        ready_for_pickle = {}
        for guild_id, guild_instance in restriction_data.items():
            try:
                ready_for_pickle[guild_id] = guild_instance.get_pickle_ready()
            except Exception as ex:
                Shared.log_event("Traceback for guild id: " + str(guild_id))
                Shared.log_traceback(ex)
        with open(restriction_data_file_path, "wb") as pickle_out:
            try:
                p.dump(ready_for_pickle, pickle_out)
            except Exception as ex:
                print("Could not dump pickle for restriction data.")
                Shared.log_traceback(ex)

async def load_restriction_data():
    global restriction_data
    if os.path.exists(restriction_data_file_path):
        with open(restriction_data_file_path, "rb") as pickle_in:
            try:
                temp = p.load(pickle_in)
                if temp == None:
                    temp = {}
                
                guilds = client.guilds
                for guild_instance in temp.values():
                    curGuild = discord.utils.get(guilds, id=guild_instance.guild)
                    if curGuild == None:
                        continue
                    try:
                        await guild_instance.unpickle_self(curGuild)
                    except Exception as ex:
                        Shared.log_traceback(ex)
                restriction_data = temp
            except:
                print("Could not read in pickle for restriction data.")
                raise
    if restriction_data == None or len(restriction_data) == 0:
        restriction_data = {}
        print("Loaded empty dict for restriction data.")

            

@client.event
async def on_ready():
    global has_loaded
    if has_loaded == False:
        await load_restriction_data()
        routine_unmute_checks.start()
        backup_data.start()
        statuses.start()
        clear_spam_filters.start()
        has_loaded = True
        print("Finished on ready.")
                    
                    

def on_exit():
    print("Exiting...")
    Shared.backup_files(Shared.backup_file_list)
    dump_restriction_data()
    
def handler(signum, frame):
    sys.exit()

signal.signal(signal.SIGINT, handler)

atexit.register(on_exit)

private_data_init()
if testing_server:
    client.run(testing_bot_key)
else:
    client.run(bot_key)
