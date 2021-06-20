'''
Created on Nov 12, 2020

@author: willg
'''
from datetime import timedelta, datetime
import Shared
import discord
from discord import member
from collections import defaultdict

default_missing_perms_time = 10


info_message = ""
info_message += "\n\nStrictBot is a powerful bot that will 'restrict' people with a certain role so they can only say certain things. Here are 3 examples:"
info_message += "\n\n- You are in a gaming server where certain players are toxic. You want to stop their toxicity, but still allow them to say certain things in the server."
info_message += "\n- You have a channel that should only be used for finding matches for a game, so members should only be allowed to send 1v1, 2v2, 3v3, 4v4 etc in this channel. If they send something else, you want to mute them in this channel only (but allow them to send messages elsewhere in the server)."
info_message += "\n- You have a channel that should only be used for certain bot commands and nothing else. You want to remove messages that aren't whitelisted, but you don't want people to be muted for violations in this channel."
info_message += "\n\n**StrictBot can do all of these with ease, even doing all at the same time.**\n\nDo `!cmds` for more information"


help_message =  "**Only server administrators are allowed to display/change the settings.**\n"
help_message += "\nStrictBot comes with a server wide setting, and 5 setting slots. Strictbot does not apply serverwide settings to your specific slots. (Eg !mmr is whitelisted serverwide - but if slot #1 is enabled, !mmr **will not** be whitelisted in the channel specified in slot #1.) **Specific settings slot must be 1, 2, 3, 4, or 5.** Slot settings are applied in reverse order, with server settings being applied last."
help_message += "\nAll terms are not case sensitive. For example, if you add the term \"!mmr\", !MMR will be allowed too."
help_message += "\nDo not include the brackets in your command. The brackets in this help message simply mean it is required."
help_message += "\n\n`!settings` to display server wide settings"
help_message += "\n`!settings_slot [#]` to display settings slot"
help_message += "\n`!restrict_off` to turn the *server wide* restriction filter off"
help_message += "\n`!restrict_on` to turn the *server wide* restriction filter on."
help_message += "\n`!restrict_off_slot [#]` to turn the restriction filter off for a specific setting slot"
help_message += "\n`!restrict_on_slot [#]` to turn the restriction filter on for a specific setting slot"
help_message += "\n\n`!add_term [term]` to add a server wide whitelisted term."
help_message += "\n`!add_term_slot [#] [term]` to add a whitelisted term for a channel specific settings slot"
help_message += "\n`!remove_term [term]` to remove a whitelisted term."
help_message += "\n`!remove_term_slot [#] [term]` to remove a whitelisted term for a channel specific settings slot"
help_message_2 = "\n`!terms` to display server wide whitelisted terms"
help_message_2 += "\n`!terms_slot [#]` to displayed whitelisted terms for a channel specific settings slot"

help_message_2 += "\n`!mention_limit [number_of_mentions]` to set the maximum number of mentions a message can have server wide."
help_message_2 += "\n`!mention_limit_slot [#] [number_of_mentions]` to set the maximum number of mentions a message can have for a channel specific settings slot."


help_message_2 += "\n`!spam_limit [number_of_messages]` to set the number of messages allowed per minute server wide. Set this to 0 if you don't want this feature enabled."

help_message_2 += "\n`!spam_limit_slot [#] [number_of_messages]` to set the number of messages allowed per minute for a channel specific settings slot. Set this to 0 if you don't want this feature enabled."

help_message_2 += "\n`!mute_time [total_seconds]` to set the mute length."
help_message_2 += "\n`!mute_time_slot [#] [total_seconds]` to set the mute length for a channel specific settings slot"
help_message_2 += "\n`!set_channel_id_slot [#] [channel_id]` to set the channel id for a specified settings slot (to get channel ID, right click channel, Copy ID)"
help_message_2 += "\n`!set_muted_role_id [roleid]` for server wide settings, to set which role is the muted role to assign if their message is not in the whitelist. Set this to -1 if you don't want them to receive a role."
help_message_2 += "\n`!set_muted_role_id_slot [#] [roleid]` for specific slot, to set which role is the muted role to assign if their message is not in the slot's whitelist. Set this to -1 if you don't want them to receive a role."

help_message_2 += "\n`!set_restricted_role_id [roleid]` for server wide settings, to set which role is the restricted role"
help_message_2 += "\n`!set_restricted_role_id_slot [#] [roleid]` for specific slot, to set which role is the restricted role"

help_message_2 += "\n`!violations` to display the *current* members muted due to violations. (If you want a full history of violations, check the server audit log.)"
help_message_2 += "\n`!restrict_reset` to reset everything to defaults - **This cannot be undone.**"
help_message_2 += "\n`!info` to display information and examples on how to use StrictBot."
help_message_2 += "\n`!cmds` to display this message."

slot_commands = set(("mention_limit_slot", "spam_limit_slot", "terms_slot", "settings_slot", "add_all_terms_slot", "restrict_off_slot", "restrict_on_slot", "add_term_slot", "remove_term_slot",
                     "mute_time_slot", "set_restricted_role_id_slot",
                     "set_muted_role_id_slot", "set_channel_id_slot"))

rest_commands = set(("mention_limit", "spam_limit", "terms", "add_all_terms", "settings", "restrict_off", "restrict_on", "add_term", "remove_term",
                     "mute_time", "set_muted_role_id", "set_restricted_role_id", "violations", "restrict_reset",
                     "info", "cmds"))

valid_slot_nums = {"1":1,"2":2,"3":3,"4":4,"5":5}




all_commands = slot_commands.union(rest_commands)

async def send_slot_num_error(slot_num, message:discord.Message):
    if slot_num != "":
        await Shared.safe_send(message, "\"" + str(slot_num) + "\" is not a valid slot number. Slot number must be 1, 2, 3, 4, or 5.")
    else:
        await Shared.safe_send(message, "You must specify a settings slot number. Slot number  1, 2, 3, 4, or 5.")



class GuildRestriction(object):

    def __init__(self, guild:discord.Guild, old_dict=None):
        self.is_pickled = False
        self.guild = guild
        if old_dict != None:
            self.load_old_dict(old_dict)
        else:
            self.load_default_data_settings()
            
            
    def load_default_data_settings(self):
        self.on = [False, False, False, False, False, False]
        self.whitelists = [set(), set(), set(), set(), set(), set()]
        self.channel_ids = [-1, -1, -1, -1, -1, -1]
        self.restricted_role_ids = [-1, -1, -1, -1, -1, -1]
        self.mute_times = [timedelta(minutes=5), timedelta(minutes=5), timedelta(minutes=5), timedelta(minutes=5), timedelta(minutes=5), timedelta(minutes=5)]
        self.mute_role_ids = [-1, -1, -1, -1, -1, -1]
        self.muted_members = {}
        self.allowed_mentions = [1, 1, 1, 1, 1, 1]
        self.allowed_files = [False, False, False, False, False, False]
        self.is_pickled = False
        
        
        self.spam_limit = [0, 0, 0, 0, 0, 0]
        
        self.message_time_counter = defaultdict(list)
        self.spam_time = timedelta(minutes=1)
    
    
    def get_slot_settings(self, slotNum):
        slot_settings_str = "**Slot #" + str(slotNum) + " settings**"
        slot_settings_str += "\nSlot Enabled: " + ("*Yes*" if self.on[slotNum] else "*No*")
        slot_settings_str += "\nChannel ID to monitor: *" + (str(self.channel_ids[slotNum]) if self.channel_ids[slotNum] != -1 else "No channel ID set") + "*"
        slot_settings_str += "\nRole ID to restrict in channel: *" + (str(self.restricted_role_ids[slotNum]) if self.restricted_role_ids[slotNum] != -1 else "No restricted role ID set") + "*"
        slot_settings_str += "\n(Muted) role ID to assign: *" + (str(self.mute_role_ids[slotNum]) if self.mute_role_ids[slotNum] != -1 else "No muted role ID set (not muting for violations in this channel)") + "*"
        slot_settings_str += "\nViolation mute time: *" + str(int(self.mute_times[slotNum].total_seconds())) + " seconds*"
        slot_settings_str += "\nMaximum allowed mentions for this role: *" + str(self.allowed_mentions[slotNum]) + "*"
        slot_settings_str += "\nAllowed to send files: *" + ("Yes" if self.allowed_files[slotNum] else "No") + "*"
        slot_settings_str += "\nSpam message limit: *" + ("Off" if self.spam_limit[slotNum] == 0 else (str(self.spam_limit[0]) + " messages per minute")) + "*"
        return slot_settings_str
    
    def get_server_wide_settings(self):
        slot_settings_str = "**Serverwide settings (these do not apply to channels in enabled slots)**"
        slot_settings_str += "\nEnabled: " + ("*Yes*" if self.on[0] else "*No*")
        slot_settings_str += "\nRole ID to restrict: *" + (str(self.restricted_role_ids[0]) if self.restricted_role_ids[0] != -1 else "No restricted role ID set") + "*"
        slot_settings_str += "\n(Muted) role ID to assign: *" + (str(self.mute_role_ids[0]) if self.mute_role_ids[0] != -1 else "No muted role ID set (not muting for violations)") + "*"
        slot_settings_str += "\nViolation mute time: *" + str(int(self.mute_times[0].total_seconds())) + " seconds*"
        slot_settings_str += "\nMaximum allowed mentions for this role: *" + str(self.allowed_mentions[0]) + "*"
        slot_settings_str += "\nSpam message limit: *" + ("Off" if self.spam_limit[0] == 0 else (str(self.spam_limit[0]) + " messages per minute")) + "*"
        slot_settings_str += "\nAllowed to send files: *" + ("Yes" if self.allowed_files[0] else "No") + "*"
        return slot_settings_str
    
    def get_whitelisted_terms(self, slotNum):
        whitelisted_terms_str = "Server wide whitelisted terms (these don't apply in enabled slot channels):\n"
        if slotNum > 0:
            whitelisted_terms_str = "Slot #" + str(slotNum) + " whitelisted terms (only apply in slot's specified channel):\n"
        whitelisted_terms_str += ", ".join(sorted(self.whitelists[slotNum]))
        if len(self.whitelists[slotNum]) == 0:
            whitelisted_terms_str += "**No white listed terms**"
        return whitelisted_terms_str
    
    def get_violations_str(self):
        total_str = "\nViolations (mute times are Pacific Coast Time):\n\n"
        muted_members_str = ""
        for member_id, (member, mute_time, information) in self.muted_members.items():
            member_str = ""
            if isinstance(member, discord.Member):
                member_str += " (Nickname: " + member.display_name + " | Discord: " + str(member) + ")" 
            muted_members_str += "ID: " + str(member_id) + member_str + " | Violation time: " + str(mute_time) + " | Muted role assigned: " + ("None" if information[0] == -1 else (str(information[0]) + " | Unmute time: " + str(information[2]))) + " | Reason: " + information[1]
            muted_members_str += "\n\n"
        if len(muted_members_str) == 0:
            muted_members_str = "No muted members"
        return total_str + muted_members_str
    
    
    async def settings_menu(self, message:discord.Message):
        if Shared.has_prefix(message.content) and Shared.can_access_settings(message.author):
            bot_command = Shared.strip_prefix(message.content.lower()).strip()
            args = bot_command.split()
            if len(args) > 0:
                command = args[0]
                if command not in all_commands:
                    return False
                slotNum = None
                if command in slot_commands:
                    if len(args) < 2 or args[1] not in valid_slot_nums:
                        await send_slot_num_error("" if len(args) < 2 else args[1], message)
                        return True
                    slotNum = int(args[1])
                
                ending = bot_command[len(args[0]):]
                if slotNum != None:
                    ending = ending[ending.index(str(slotNum))+1:]
                ending = ending.strip()
                
                if command == "cmds":
                    await Shared.safe_send(message, help_message)
                    await Shared.safe_send(message, help_message_2)
                elif command == "info":
                    await Shared.safe_send(message, info_message)
                    
                elif command == "restrict_reset":
                    self.load_default_data_settings()
                    await Shared.safe_send(message, "Reset settings.")
                elif command == "terms":
                    await Shared.safe_send(message, self.get_whitelisted_terms(0))
                elif command == "terms_slot":
                    await Shared.safe_send(message, self.get_whitelisted_terms(slotNum))
                elif command == "settings":
                    await Shared.safe_send(message, self.get_server_wide_settings())
                elif command == "settings_slot":
                    await Shared.safe_send(message, self.get_slot_settings(slotNum))

                elif command == "restrict_off":
                    self.on[0] = False
                    await Shared.safe_send(message, "Server wide restriction turned off.")
                elif command == "restrict_on":
                    self.on[0] = True
                    await Shared.safe_send(message, "Server wide restriction turned on.")
                elif command == "restrict_off_slot":
                    self.on[slotNum] = False
                    await Shared.safe_send(message, "Restriction turned off for slot #" + str(slotNum))
                elif command == "restrict_on_slot":
                    self.on[slotNum] = True
                    await Shared.safe_send(message, "Restriction turned on for slot #" + str(slotNum))
                
                elif command == "mention_limit":
                    if ending == "":
                        await Shared.safe_send(message, "Provide a number. This is the maximum number of mentions allowed in the message.")
                    elif not ending.isnumeric():
                        await Shared.safe_send(message, f"{ending} is not a number. This is the maximum number of mentions allowed in the message.")
                    else:
                        ending = int(ending)
                        if ending < 0:
                            await Shared.safe_send(message, "Negative mentions don't make sense.")
                        elif ending > 30:
                            await Shared.safe_send(message, "A maximum of 30 mention limit is allowed.")
                        else:
                            self.allowed_mentions[0] = int(ending)
                            await Shared.safe_send(message, "Set maximum allowed mentions to: " + str(ending) + " mentions")
                        
                elif command == "mention_limit_slot":
                    if ending == "":
                        await Shared.safe_send(message, "Provide a number. This is the maximum number of mentions allowed in the message.")
                    elif not ending.isnumeric():
                        await Shared.safe_send(message, f"{ending} is not a number. This is the maximum number of mentions allowed in the message.")
                    else:
                        ending = int(ending)
                        if ending < 0:
                            await Shared.safe_send(message, "Negative mentions don't make sense.")
                        elif ending > 30:
                            await Shared.safe_send(message, "A maximum of 30 mention limit is allowed.")
                        else:
                            self.allowed_mentions[slotNum] = int(ending)
                            await Shared.safe_send(message, "Set maximum allowed mentions to: " + str(ending) + " mentions for slot #" + str(slotNum))
                    
                
                elif command == "spam_limit":
                    if ending == "":
                        await Shared.safe_send(message, "Provide a number. This is the number of messages allowed per minute. If you want this feature off, the number should be 0.")
                    elif not ending.isnumeric():
                        await Shared.safe_send(message, f"{ending} is not a number. This is the maximum number of mentions allowed in the message.  If you want this feature off, the number should be 0.")
                    else:
                        ending = int(ending)
                        if ending < 0:
                            await Shared.safe_send(message, "Negative numbers don't make sense for messages allowed per minute.")
                        elif ending > 100:
                            await Shared.safe_send(message, "A maximum of 100 messages per minute is allowed.")
                        else:
                            self.spam_limit[0] = int(ending)
                            await Shared.safe_send(message, "Set message limit to: " + str(ending) + " messages per minute")
                        
                elif command == "spam_limit_slot":
                    if ending == "":
                        await Shared.safe_send(message, "Provide a number. This is the number of messages allowed per minute. If you want this feature off, the number should be 0.")
                    elif not ending.isnumeric():
                        await Shared.safe_send(message, f"{ending} is not a number. This is the maximum number of mentions allowed in the message.  If you want this feature off, the number should be 0.")
                    else:
                        ending = int(ending)
                        if ending < 0:
                            await Shared.safe_send(message, "Negative numbers don't make sense for messages allowed per minute.")
                        elif ending > 100:
                            await Shared.safe_send(message, "A maximum of 100 messages per minute is allowed.")
                        else:
                            self.spam_limit[slotNum] = int(ending)
                            await Shared.safe_send(message, "Set message limit to: " + str(ending) + " messages per minute for slot #" + str(slotNum))
                        
                
                    
                elif command == "add_term":
                    if ending == "":
                        await Shared.safe_send(message, "Provide a term to add.")
                    else:
                        if len(self.whitelists[0]) >= 2000:
                            await Shared.safe_send(message, "You already have 2000 terms added. This is the maximum amount of terms you can whitelist for server wide settings.")
                        elif len(ending) > 200:
                            await Shared.safe_send(message, "Whitelisted terms cannot be more than 200 characters long.")
                        else:
                            self.whitelists[0].add(ending)
                            await Shared.safe_send(message, "Added: " + ending)
                
                elif command == "add_term_slot":
                    if ending == "":
                        await Shared.safe_send(message, "Provide a term to add to allow in this slot's channel.")
                    else:
                        if len(self.whitelists[0]) >= 500:
                            await Shared.safe_send(message, "You already have 500 terms added for this slot. This is the maximum amount of terms you can whitelist for each slot.")
                        elif len(ending) > 200:
                            await Shared.safe_send(message, "Whitelisted terms cannot be more than 200 characters long.")
                        else:
                            self.whitelists[slotNum].add(ending)
                            await Shared.safe_send(message, "Added term to slot #" + str(slotNum) + ": " + ending)
                    
                elif command == "add_all_terms":
                    if ending == "":
                        await Shared.safe_send(message, "Provide terms to add (separated by commas).")
                    else:
                        terms_to_add = ending.split(",")
                        term_set = set()
                        for term in terms_to_add:
                            term = term.strip(" \n\t")
                            if len(term) > 0:
                                term_set.add(term)
                            if len(term) > 200:
                                await Shared.safe_send(message, "Each whitelisted term must be 200 characters or less.")
                                return True
                            if (len(term_set) + len(self.whitelists[0])) > 500:
                                await Shared.safe_send(message, "This would exceed the maximum 500 terms allowed for this slot. No terms added.")
                                return True
                        self.whitelists[0].update(term_set)
                        await Shared.safe_send(message, str(len(term_set)) + " terms added to server wide whitelist")

                elif command == "add_all_terms_slot":
                    if ending == "":
                        await Shared.safe_send(message, "Provide terms to add (separated by commas).")
                    else:
                        terms_to_add = ending.split(",")
                        term_set = set()
                        for term in terms_to_add:
                            term = term.strip(" \n\t")
                            if len(term) > 0:
                                term_set.add(term)
                            if len(term) > 200:
                                await Shared.safe_send(message, "Each whitelisted term must be 200 characters or less.")
                                return True
                        if (len(term_set) + len(self.whitelists[slotNum])) > 500:
                            await Shared.safe_send(message, "This would exceed the maximum 500 terms allowed for this slot. No terms added.")
                            return True
                        self.whitelists[slotNum].update(term_set)
                        await Shared.safe_send(message, str(len(term_set)) + " terms added to slot #" + str(slotNum) + " whitelist")

                elif command == "remove_term":
                    if ending == "":
                        await Shared.safe_send(message, "Provide a term to remove.")
                    elif ending not in self.whitelists[0]:
                        await Shared.safe_send(message, "This was not a previously whitelisted term server wide: " + ending)
                    else:
                        self.whitelists[0].remove(ending)
                        await Shared.safe_send(message, "Removed server wide whitelisted term: " + ending)
                

                elif command == "remove_term_slot":
                    if ending == "":
                        await Shared.safe_send(message, "Provide a term to remove from this slot.")
                    elif ending not in self.whitelists[slotNum]:
                        await Shared.safe_send(message, "This was not a previously whitelisted term for slot #" + str(slotNum) + ": " + ending)
                        
                    else:
                        self.whitelists[slotNum].remove(ending)
                        await Shared.safe_send(message, "Removed whitelisted term from slot #" + str(slotNum) + ": " + ending)
                
                
                elif command == "mute_time":
                    mute_length = ending
                    if not mute_length.isnumeric():
                        await Shared.safe_send(message, "Specify the mute length in number of seconds. Example: For a 5 minute mute length: `!mute_time 300`")
                        return True
                    mute_length = int(mute_length)
                    if mute_length < 1:
                        await Shared.safe_send(message, "A minimum of 1 second is required for mute length.")
                    elif mute_length > 604800:
                        await Shared.safe_send(message, "A maximum of 604800 seconds is allowed for mute length. (This is one week.)")
                    else:
                        self.mute_times[0] = timedelta(seconds=mute_length)
                        await Shared.safe_send(message, "Set mute time to: " + str(mute_length) + " seconds\nNote: *Mute times are not guaranteed to be exact. The member is guaranteed to be muted for at least the length set, but may be muted for up to 60 seconds after their mute should end. For example, if the set mute time is 5 minutes, the member will be unmuted somewhere between 5 minutes and 6 minutes after they were muted.*")
                        
                elif command == "mute_time_slot":
                    mute_length = ending
                    if not mute_length.isnumeric():
                        await Shared.safe_send(message, "Specify the mute length in number of seconds. Example: For a 5 minute mute length for this slot: `!mute_time_slot " + str(slotNum) + "300`")
                        return True
                    mute_length = int(mute_length)
                    if mute_length < 1:
                        await Shared.safe_send(message, "A minimum of 1 second is required for mute length.")
                    elif mute_length > 604800:
                        await Shared.safe_send(message, "A maximum of 604800 seconds is allowed for mute length. (This is one week.)")
                    else:
                        self.mute_times[slotNum] = timedelta(seconds=mute_length)
                        await Shared.safe_send(message, "Set mute time to: " + str(mute_length) + " seconds for slot #" + str(slotNum) + "\nNote: *Mute times are not guaranteed to be exact. The member is guaranteed to be muted for at least the length set, but may be muted for up to 60 seconds after their mute should end. For example, if the set mute time is 5 minutes, the member will be unmuted somewhere between 5 minutes and 6 minutes after they were muted.*")
                      
                
                elif command == "set_channel_id_slot":
                    id_to_set = ending
                    if not id_to_set.isnumeric():
                        await Shared.safe_send(message, "ID must be a number.")
                    else:
                        self.channel_ids[slotNum] = int(id_to_set)
                        await Shared.safe_send(message, "Slot #" + str(slotNum) + " channel id for restriction monitoring set to: " + id_to_set)
                
                elif command == "set_muted_role_id":
                    id_to_set = ending
                    if not id_to_set.isnumeric():
                        if id_to_set == "None" or id_to_set == "-1":
                            self.mute_role_ids[0] = -1
                            await Shared.safe_send(message, "No longer assigning a role for violations server wide")
                        else:
                            await Shared.safe_send(message, "ID must be a number.")
                    else:
                        self.mute_role_ids[0] = int(id_to_set)
                        await Shared.safe_send(message, "Set muted role id to: " + id_to_set)
                
                elif command == "set_muted_role_id_slot":
                    id_to_set = ending
                    if not id_to_set.isnumeric():
                        if id_to_set == "None" or id_to_set == "-1":
                            self.mute_role_ids[slotNum] = -1
                            await Shared.safe_send(message, "No longer assigning a role for violations in the channel for slot #" + str(slotNum))
                        else:
                            await Shared.safe_send(message, "ID must be a number.")
                    else:
                        self.mute_role_ids[slotNum] = int(id_to_set)
                        await Shared.safe_send(message, "Set muted role id for slot #" + str(slotNum) + " to: " + id_to_set)
                
                
                elif command == "set_restricted_role_id":
                    id_to_set = ending
                    if not id_to_set.isnumeric():
                        await Shared.safe_send(message, "ID must be a number.")
                    else:
                        self.restricted_role_ids[0] = int(id_to_set)
                        await Shared.safe_send(message, "Set server wide restricted role id to: " + id_to_set)
                
                elif command == "set_restricted_role_id_slot":
                    id_to_set = ending
                    if not id_to_set.isnumeric():
                        await Shared.safe_send(message, "ID must be a number.")
                    else:
                        self.restricted_role_ids[slotNum] = int(id_to_set)
                        await Shared.safe_send(message, "Set slot #" + str(slotNum) + " restricted role id to: " + id_to_set)
                
                elif command == "violations":
                    await Shared.safe_send(message, self.get_violations_str())
                    
                return True
            
        return False
    
    
    def unmute_all(self):
        pass
    
    
    def guild_test(self):
        print("Guild name:", self.guild.name)
        print("Member count:", self.guild.member_count)
        print("Member length:", len(self.guild.members))
        print("Role count:", len(self.guild.roles))
        print("Channel count:", len(self.guild.channels))
        print("\n")
    
    async def get_enabled_restriction_slot(self, message:discord.Member):
        author_id = message.author.id
        author = message.author
        if not isinstance(author, discord.Member):
            author = self.guild.get_member(author_id)
        
        if author == None:
            author = await self.guild.fetch_member(author_id)
        
        if author == None:
            Shared.log_event("Couldn't find member for this message: " + repr(message))
            return None, None
            
        
        all_roles = {role.id for role in author.roles}
        for i in reversed(range(6)):
            if self.on[i]:
                if self.channel_ids[i] == message.channel.id or i == 0:
                    if self.restricted_role_ids[i] in all_roles:
                        return i, author
        return None, None
    
    def clear_spam(self):
        self.message_time_counter = defaultdict(list)
        
    def over_spam_limit(self, message:discord.Message, slot_triggered:int):
        if self.spam_limit[slot_triggered] == 0:
            return False
        
        max_messages = self.spam_limit[slot_triggered]
        message_history = self.message_time_counter[message.author.id]
        cur_time = datetime.now()
        recent_messages_count = 0
        try:
            for message_time_ind in range(len(message_history)-1, -1, -1):
                if message_history[message_time_ind] >= (cur_time - self.spam_time):
                    recent_messages_count += 1
                else:
                    break
        except: #List changed during iteration, ignore and move on - very rare, could happen in nanoseconds once every 12 hours
            pass
        return recent_messages_count > max_messages
        
        
        
    def message_allowed(self, message:discord.Message, slot_triggered:int):

            
        #TODO: Allow admin setting to turn on/off stickers
        #if not self.allowed_stickers[slot_triggered]:
        #if len(message.stickers) > 0:
        #    return False
        
        if self.over_spam_limit(message, slot_triggered):
            return True, False
        
        if len(message.raw_mentions) > self.allowed_mentions[slot_triggered]:
            return False, False
        
        message_content = message.content
        for raw_mention in message.raw_mentions:
            mention_type_1 = "<@!" + str(raw_mention) + ">"
            mention_type_2 = "<@" + str(raw_mention) + ">"
            if mention_type_1 in message_content:
                message_content = message_content.replace(mention_type_1, "", 1)
            else:
                message_content = message_content.replace(mention_type_2, "", 1)
        
        
        message_content = message_content.strip().lower()
        
        if self.allowed_files[slot_triggered]:
            if len(message.attachments) > 0:
                if len(message_content) == 0:
                    return False, True #If the message content was no longer 0 (after removing mentions), regardless of there being files, we need to check if it hits restriction filter
        else: #Attachments not allowed
            if len(message.attachments) > 0:
                return False, False
                
        if len(message_content) == 0:
            return False, False #TODO, this means all empty messages are not okay, see line #405

        
        if message_content in self.whitelists[slot_triggered]:
            return False, True
        else:
            #TODO: Add number support
            #There are two possible ways to do this. The following way may seem easiest, but it has a bug:
            #message_content = replace_continuous_numbers(message_content, replacement_text="%%number")
            #if message_content in self.whitelists[slot_triggered]:
            #   return False, True
            
            #The bug is a scenario where the term in the allowed list is: ?quickedit 1 %%number %%number and the message is "?quickedit 1 2 3"
            #Line 539 doesn't succeed because the term contains %%number, and that's okay. But line 544 also fails because we get back "?quickedit %%number %%number %%number"
            #which fails to match.
            
            #What is the solution? Perhaps we do not allow wild card numbers in to be in the same term as normal numbers. But this limits the user's possibilities for matching, which isn't ideal.
            
            #We also want to avoid putting user input directly into a regex pattern. The reasons for this are beyond the scope of these comments.
            
            #It appears, then, we'll have to iterate through the whitelist terms, add all that have wild cards to a list, then for each of those terms,
            #carefully iterate over the user input and check if it matches. This is unfortunately the only solution that comes to mind,
            #which is less than ideal since every check thus-far is O(1) lookup (hashing). We open ourselves up to very large lookup times if there are many terms with wild cards
            #with this solution, and/or if this user's message is very long.
            
            #Brainstorm for alternative solutions...?
  
            pass
        return False, False
            
    
    async def restriction_filter_check(self, message:discord.Message):
        if message.author.bot:
            return
        if self.is_pickled:
            return

            
        
        slot_triggered, member_object = await self.get_enabled_restriction_slot(message)
        if slot_triggered == None:
            return
        
        self.message_time_counter[message.author.id].append(datetime.now())
        
        spam_filter_triggered, allowed = self.message_allowed(message, slot_triggered)
        if not allowed:
            try:
                await message.delete() #for speed
            except discord.errors.Forbidden:
                await Shared.safe_send_missing_permissions(message, delete_after=default_missing_perms_time)
            except discord.errors.NotFound:
                pass
            except Exception as ex:
                Shared.log_event("UNKNOWN EXCEPTION OCCURRED")
                Shared.log_traceback(ex)

            reason_specified = ""
            if not spam_filter_triggered:
                reason_specified = "non-whitelisted term used in #" + str(message.channel) + " - violated " + ("server wide" if slot_triggered == 0 else ("slot #" + str(slot_triggered))) + " settings"
            else:
                reason_specified = "spamming in #" + str(message.channel) + " - violated " + ("server wide" if slot_triggered == 0 else ("slot #" + str(slot_triggered))) + " spam settings"
            
            muted_role = -1
            mute_success = False
            if self.mute_role_ids[slot_triggered] != -1:  
                muted_role = Shared.get_role(self.guild, self.mute_role_ids[slot_triggered])
                if muted_role != None:
                    mute_str = " - " + str(round((self.mute_times[slot_triggered].total_seconds()/60), 1)) + " minute mute"
                    try:
                        await member_object.add_roles(muted_role,\
                                reason=reason_specified+mute_str,\
                                           atomic=True)
                    except discord.errors.Forbidden:
                        await Shared.safe_send_missing_permissions(message, delete_after=default_missing_perms_time)
                    except Exception as ex:
                        Shared.log_event("UNKNOWN EXCEPTION OCCURRED")
                        Shared.log_traceback(ex)
                    else:
                        mute_success = True
                        reason_specified += mute_str
            
            if not mute_success:
                muted_role = -1
            else:
                muted_role = muted_role.id
                        
            curTime = datetime.now()
            unmute_time = curTime + self.mute_times[slot_triggered]
            self.muted_members[message.author.id] = (member_object, curTime, (muted_role, reason_specified, unmute_time))
                        
        
    async def unmute_check(self):
        if self.is_pickled:
            return
        try:
        
            if len(self.muted_members) == 0:
                return
        
            removed = set()
            curTime = datetime.now()
            error_occurred = False
            for member_id, (discord_member, _, (muted_role_id, reason, end_mute_time)) in self.muted_members.items():
                if end_mute_time < curTime:
                    if muted_role_id != -1:
                        if isinstance(discord_member, discord.Member):
                            muted_role = Shared.get_role(self.guild, muted_role_id)
                            try:
                                await discord_member.remove_roles(muted_role, reason=reason + " - muted ended", atomic=True)
                            except discord.errors.Forbidden:
                                error_occurred = True
                                pass #Nowhere to send messages to
                            except discord.errors.NotFound:
                                pass
                            except Exception as ex:
                                error_occurred = True
                                Shared.log_event("UNKNOWN EXCEPTION OCCURRED")
                                Shared.log_traceback(ex)
                    if not error_occurred: #Note that if they have no muted role specified, we'll remove them automatically
                        removed.add(member_id)
                
            for member_id in removed:
                del self.muted_members[member_id]   
        except Exception as ex:
            error_occurred = True
            Shared.log_event("UNKNOWN EXCEPTION OCCURRED")
            Shared.log_traceback(ex)
 

    
    async def unpickle_self(self, curGuild):
        self.guild = curGuild
        members = self.guild.members
        
        if 'allowed_mentions' not in self.__dict__:
            self.allowed_mentions = [1, 1, 1, 1, 1, 1]
        if 'allowed_files' not in self.__dict__:
            self.allowed_files = [False, False, False, False, False, False]
        
        if 'muted_members' in self.__dict__:
            to_find = set()
            for member_id in self.muted_members:
                if isinstance(self.muted_members[member_id][0], int):
                    to_find.add(member_id)
            
            for member in members:
                if member.id in to_find:
                    self.muted_members[member.id] = (member, self.muted_members[member.id][1], self.muted_members[member.id][2])
                    to_find.remove(member.id)
            self.is_pickled = False
            
        if 'spam_limit' not in self.__dict__:
            self.spam_limit = [0, 0, 0, 0, 0, 0]
        
    
    def get_pickle_ready(self):
        temp_instance = GuildRestriction(self.guild)
        for key in self.__dict__:
            temp_instance.__dict__[key] = self.__dict__[key]
        for_pickle = {}
        for member_id, (member, mutetime, information) in temp_instance.muted_members.items():
            if isinstance(member, int):
                for_pickle[member_id] = (member, mutetime, information)
            else:
                for_pickle[member_id] = (member.id, mutetime, information)
        temp_instance.muted_members = for_pickle
        
        if not isinstance(temp_instance.guild, int):
            temp_instance.guild = temp_instance.guild.id
        
        temp_instance.is_pickled = True
        return temp_instance
    
    def __str__(self):
        to_build = str(self.guild) + "\n"
        to_build += str("Is pickled: ") + str(self.is_pickled) + "\n"
        to_build += self.get_server_wide_settings() + "\n"
        to_build += self.get_whitelisted_terms(0) + "\n"
        for i in range(1, 6):
            to_build += self.get_slot_settings(i) + "\n"
            to_build += self.get_whitelisted_terms(i) + "\n"
        to_build += self.get_violations_str()
        return to_build
    
    def __repr__(self):
        return str(self)
        
        
            
