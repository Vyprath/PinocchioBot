"""
Note: In this init file, you have to specifically import the individual module's functions
as a dictionary. Then append that dictionary to the master dictionary in this init module.
The master dictionary here is called "functions".

Prototype of 'functions':
{
    'command_name': (command, help_string,),
}

help_string can be None, in which case 'help_string' = 'The developer says: fcuk off'.

Handlers are called when each message is recieved.

Prototype of 'handlers':
[handler_1,]
...
async def handler_1(client, message):
...
"""
import shlex

import jellyfish
from discord.errors import Forbidden

import messages
import variables
from log import log
from music import music_functions

from .admin import admin_functions
from .anime import anime_functions
from .currency import currency_functions, currency_handlers
from .devtest import devtest_functions
from .fun import fun_functions
from .general import general_functions
from .quiz import quiz_functions
from .reactions import reactions_functions
from .shop import shop_functions
from .waifu import waifu_functions


def split_args(value):
    lex = shlex.shlex(value)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


async def message_resolve(client, message, cmd_prefix):
    if message.author.bot:
        return
    if message.author.id in variables.noflylist:
        return
    if message.content.startswith(cmd_prefix):
        await log(message.author, message.guild, message.content)
        args = split_args(message.content[len(cmd_prefix) :])
        command = args[0].lower()
        if command == "help":
            await print_help(client, message, *args[len(cmd_prefix) :], full=False)
        elif command == "fullhelp":
            await print_help(client, message, *args[len(cmd_prefix) :], full=True)
        elif command in functions.keys():
            await functions[command][0](client, message, *args[len(cmd_prefix) :])
        else:
            jaro_dists = [
                (i, jellyfish.jaro_distance(command, i)) for i in functions.keys()
            ]
            jaro_dists = [i for i in jaro_dists if i[1] > 0.8]
            if len(jaro_dists) == 0:
                return
            jaro_dists.sort(key=lambda i: i[1], reverse=True)
            txt = ",".join([f"`{i[0]}`" for i in jaro_dists])
            await message.channel.send(
                f"`{variables.PREFIX}{command}` not found. Did you mean: {txt}"
            )
    for handler in handlers:
        await handler(client, message)


async def print_help(client, message, *args, full=False):
    if len(args) == 0 or args[0] == "inchannel":
        if full:
            for text in [
                messages.FULL_HELP_TEXT[i : i + 1990]
                for i in range(0, len(messages.FULL_HELP_TEXT), 1990)
            ]:
                await message.author.send(text)
        else:
            if len(args) == 1 and args[0] == "inchannel":
                await message.channel.send(embed=messages.main_help_menu)
            else:
                try:
                    await message.author.send(embed=messages.main_help_menu)
                    await message.channel.send("DM-ed the help message!")
                except Forbidden:
                    await message.channel.send(
                        "Could not DM help message! Is inbox disabled?",
                        embed=messages.main_help_menu,
                    )
    elif args[0] in functions.keys():
        help_string = functions[args[0]][1]
        if help_string is None:
            help_string = "No help message for this command."
        await message.channel.send(help_string.replace("{P}", variables.PREFIX))


"""
This is how 'functions' is implemented in a module file:

async def example(client, message, *args):
    return await message.channel.send("Hello, user. Your args: \"{}\"".format(" ".join(args)))

functions = {
    "hello": (argu, 'help message')
}
"""

functions = {}
handlers = []

functions.update(admin_functions)
functions.update(general_functions)
functions.update(devtest_functions)
functions.update(currency_functions)
functions.update(shop_functions)
functions.update(waifu_functions)
functions.update(fun_functions)
functions.update(reactions_functions)
functions.update(anime_functions)
functions.update(quiz_functions)
functions.update(music_functions)

handlers += currency_handlers
