from variables import PREFIX


HELP_MESSAGE = """
__**Pinocchio Bot Usage:**__

*NOTE: Bot is still in pre-alpha. Be prepared for bugs. Report bugs at https://discord.gg/F6REE6P*

**General**
`{0}help`: Get the commands and a brief description.
`{0}help <command name>`: A little more detailed description (if available).

**Financial**
`{0}wallet [optional: @user mention]`: Check your own wallet or others' wallet.
`{0}transfer-money <@user mention> <amount>`: Transfer some money.
`{0}dailies`: Get your daily money and become riiiich.

**Shop**
`{0}paidroles`: Get a preset role with $$$.
`{0}customrole`: Get your custom colored role with $$$$$$.

**Waifu**
`{0}waifu`: Buy/Sell/View/Search/Trade Waifus. Will make your loneliness disappear.
`{0}harem`: Get the list of your bought waifus.

**Reactions**
__*Usage* `{0}<command name> <@user mention>`:__ `{0}hug`,`{0}kiss`,`{0}pat`,`{0}tickle`,`{0}bite`,
`{0}kick`,`{0}slap`,`{0}punch`,`{0}poke`.
__*Usage* `{0}<command name>`:__ `{0}laugh`,`{0}cry`,`{0}blush`,`{0}confused`,`{0}pout`,`{0}dance`,
`{0}jojo`,`{0}megumin`,`{0}satania`,`{0}lick`,`{0}think`,`{0}shrug`,`{0}owo`,`{0}nom`,
`{0}eyeroll`,`{0}lewd`,`{0}stare`,`{0}triggered`,`{0}facepalm`.
`{0}gif <search string>`: Search for a GIF.

**Lag Free Music** __(Donator-exclusive feature)__
*NOTE: To use these commands, you have to donate to the bot.*
*After donating, please contact <@252297314394308608> to enable this.*
`{0}play`: Play some musix.
`{0}leave`: Make the bot leave the music channel **Requires administrator permission**
`{0}skip`: Skip the current song.

**Administration (Below commands require Admininstrator Permission)**
`{0}get-money <amount>`: Get some money.
`{0}@paidroles`: Set up paid roles.
`{0}@purge <number of messages>`: Purge messages from the channel.
""".format(PREFIX)
