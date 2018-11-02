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
from .admin import admin_functions
from .devtest import devtest_functions
from .general import general_functions
from .currency import currency_functions, currency_handlers
from .shop import shop_functions
from .waifu import waifu_functions


async def message_resolve(client, message, cmd_prefix):
    if message.content.startswith(cmd_prefix):
        args = message.content[1:].split(" ")
        if args[0] == 'help':
            await print_help(client, message, *args)
        elif args[0] in functions.keys():
            await functions[args[0]][0](client, message, *args[1:])
    for handler in handlers:
        await handler(client, message)


async def print_help(client, message, *args):
    if len(args) == 0:
        await message.channel.send("I think I am supposed to add a help message here...")
    elif args[0] in functions.keys():
        help_string = functions[args[0]][1]
        if help_string is not None:
            help_string = "The developer says: fcuk off."
        await message.channel.send("{0}: {1}".format(args[0], help_string))

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

handlers += currency_handlers
