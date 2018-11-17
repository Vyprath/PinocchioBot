from variables import PREFIX


HELP_MESSAGE = """
__**Pinocchio Bot Usage:**__

**Bot**
`{0}help`: Get the commands and a brief description.
`{0}help <command name>`: A little more detailed description (if available).
`{0}donate`: Donate to this bot UwU.
`{0}creator`: Get to know the creator of this bot, so you can annoy him to fix the damned bugs.
`{0}vote`: Vote for this bot! Isn't Pinocchio kawaii? Vote for her and make her happy. _(sorry)_
`{0}claimreward`: Pinocchio is happy now! Thanks for voting. Here, collect your reward.
`{0}invite`: Get the invite link for this server.

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

**Fun**
`{0}avatar [optional: @user mention]`: View yours or someone's avatar.
`{0}poll \"Title of Poll\" \"Option 1\" \"Option 2\" [\"Option 3\"...]`: Create a reaction poll.

**Reactions**
__*Usage* `{0}<command name> <@user mention>`:__ `{0}hug`,`{0}kiss`,`{0}pat`,`{0}tickle`,`{0}bite`,
`{0}kick`,`{0}slap`,`{0}punch`,`{0}poke`.
__*Usage* `{0}<command name>`:__ `{0}laugh`,`{0}cry`,`{0}blush`,`{0}confused`,`{0}pout`,`{0}dance`,
`{0}jojo`,`{0}megumin`,`{0}satania`,`{0}lick`,`{0}think`,`{0}shrug`,`{0}owo`,`{0}nom`,
`{0}eyeroll`,`{0}lewd`,`{0}stare`,`{0}triggered`,`{0}facepalm`.
`{0}gif <search string>`: Search for a GIF.

**Lag Free HQ Music** __(Donator-exclusive feature)__
*NOTE: To use these commands, you have to donate to the bot. After donating, please contact RandomGhost#5990 to enable this.*
*NOTE#2: HQ means highest available music quality in YouTube. To save their server bandwidth, most bots take the lowest available music quality in YouTube. Not this bot.*
`{0}play`/`{0}p`: Play some musix.
`{0}leave`: Make the bot leave the music channel **Requires administrator permission**
`{0}skip`: Skip the current song.
`{0}queue`: Get current playlist.
`{0}volume`: Set the volume. Default: 100.
`{0}pause`/`{0}resume`: Pause/Resume music.
`{0}status`: Get status about current playing music.

**Administration (Below commands require Admininstrator Permission)**
`{0}get-money <amount>`: Get some money.
`{0}setpaidroles`: Set up paid roles.
`{0}purge <number of messages between 1 to 100>`: Purge messages from the channel.

**NOTE: Bot is still in pre-alpha. Be prepared for bugs. Report bugs at https://discord.gg/HkN7ReX**
""".format(PREFIX)
