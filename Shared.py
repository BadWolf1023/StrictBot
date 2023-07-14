'''
Created on Sep 26, 2020

@author: willg
'''
import discord
import os
from pathlib import Path
import shutil
from datetime import datetime
from typing import Set
import traceback

prefix = "!"
MKW_LOUNGE_SERVER_ID = 387347467332485122

def get_max_term_limit(server_id):
    if server_id == MKW_LOUNGE_SERVER_ID:
        return 15000
    else:
        return 2000


backup_folder = "backups/"
restricted_data_pickle_path = "restricted_data.pkl"
backup_file_list = [restricted_data_pickle_path]

def has_prefix(message:str, prefix:str=prefix):
    message = message.strip()
    return message.startswith(prefix)

def strip_prefix(message:str, prefix:str=prefix):
    message = message.strip()
    if message.startswith(prefix):
        return message[len(prefix):]
    
def is_in(message:str, valid_terms:set, prefix:str=prefix):
    if (has_prefix(message, prefix)):
        message = strip_prefix(message, prefix).strip()
        args = message.split()
        if len(args) == 0:
            return False
        return args[0].lower().strip() in valid_terms
            
    return False
    
def strip_prefix_and_command(message:str, valid_terms:set, prefix:str=prefix):
    message = strip_prefix(message, prefix)
    args = message.split()
    if len(args) == 0:
        return message
    if args[0].lower().strip() in valid_terms:
        message = message[len(args[0].lower().strip()):]
    return message.strip()




def can_access_settings(author:discord.Member):
    if author.guild_permissions.administrator:
        return True
    return author.id == 706120725882470460


def roles_have_role(roles, role_ids:Set[int]):
    if isinstance(role_ids, int):
        role_ids = {role_ids}
        
        
    for role_id in roles:
        role_id = str(role_id)
        if role_id.isnumeric():
            if int(role_id) in role_ids:
                return True
    return False

def get_role(guild:discord.Guild, role_id:int):
    mapping, _ = get_role_mapping(role_id, guild)
    if role_id in mapping:
        return mapping[role_id]
    return None

def has_any_role_ids(member:discord.Member, role_ids:Set[int]):
    if isinstance(role_ids, int):
        role_ids = {role_ids}
        
    for role in member.roles:
        if role.id in role_ids:
            return True
    return False  

def get_role_mapping(role_ids, guild:discord.guild):
    if isinstance(role_ids, int):
        role_ids = {role_ids}
    mappings = {}
    for role in guild.roles:
        if role.id in role_ids:
            mappings[role.id] = role
    if role_ids != set(mappings.keys()):
        return mappings, False
    return mappings, True 


async def safe_send_missing_permissions(message:discord.Message, delete_after=None):
    try:
        await message.channel.send("I'm missing permissions or your role hierarchy is wrong. Contact your admins. The bot needs the following permissions:\n- Send Messages\n- Manage Messages\n- Manage Roles\n- Attach files\n**I also need to be above the muted role in the role hierarchy.**", delete_after=delete_after)
    except discord.errors.Forbidden: #We can't send messages
        pass
    
async def safe_send_file(message:discord.Message, content):
    file_name = str(message.id) + ".txt"
    Path('./attachments').mkdir(parents=True, exist_ok=True)
    file_path = "./attachments/" + file_name
    with open(file_path, "w") as f:
        f.write(content)
        
    txt_file = discord.File(file_path, filename=file_name)
    try:
        await message.channel.send(content="My message was too long, so I've attached it as a txt file instead.", file=txt_file)
    except discord.errors.Forbidden:
        await safe_send_missing_permissions(message)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


#Won't throw exceptions if we're missing permissions, it's "safe"
async def safe_send(message:discord.Message, content=None, embed=None, delete_after=None):
    if content != None and len(content) > 1998:
        await safe_send_file(message, content)
        return

    try:
        await message.channel.send(content=content, embed=embed, delete_after=delete_after)
    except discord.errors.Forbidden: #Missing permissions
        await safe_send_missing_permissions(message, delete_after=10)


def log_event(text, file_name="event_log.txt"):
    if not os.path.isfile(file_name):
        f = open(file_name, "w")
        f.close()
    with open(file_name, "a+") as f:
        f.write("\n")
        f.write(str(datetime.now()))
        f.write(": ")
        try:
            f.write(text)
        except:
            pass
        
def log_traceback(ex, ex_traceback=None):
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [ line.rstrip('\n') for line in
                 traceback.format_exception(ex.__class__, ex, ex_traceback)]
    log_event("\n".join(tb_lines))
    
def traceback_str(ex, ex_traceback=None):
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [ line.rstrip('\n') for line in
                 traceback.format_exception(ex.__class__, ex, ex_traceback)]
    return "\n".join(tb_lines)


    
#============== PICKLES AND BACKUPS ==============         
def check_create(file_name):
    if not os.path.isfile(file_name):
        f = open(file_name, "w")
        f.close()
  
def backup_files(to_back_up=backup_file_list):
    Path(backup_folder).mkdir(parents=True, exist_ok=True)
    todays_backup_path = backup_folder + str(datetime.date(datetime.now())) + "/"
    Path(todays_backup_path).mkdir(parents=True, exist_ok=True)
    for file_name in to_back_up:
        try:
            if not os.path.exists(file_name):
                continue
            temp_file_n = file_name
            if os.path.exists(todays_backup_path + temp_file_n):
                for i in range(200):
                    temp_file_n = file_name + "_" + str(i) 
                    if not os.path.exists(todays_backup_path + temp_file_n):
                        break
            shutil.copy2(file_name, todays_backup_path + temp_file_n)
        except Exception as e:
            print(e)
