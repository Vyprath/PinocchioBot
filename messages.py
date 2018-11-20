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

**Anime** **NEW**
`{0}anime <anime name>`: Get details about an anime.
`{0}manga <manga name>`: Get details about a manga.
`{0}animelist <MAL Username>`: Get someone's MAL animelist.
`{0}mangalist <MAL Username>`: Get someone's MAL mangalist.
`{0}profile <MAL Username>`: Get someone's MAL profile.

**Fun** **NEW**
*Usage* `{0}<command name>`: `{0}chucknorris`, `{0}dadjoke`, `{0}xkcd`, `{0}catfact`, `{0}8ball`.
`{0}lmgtfy <query>`: Let me google that for you.
`{0}urbandictionary <query>`: Let me Urban Dict-- I mean, let me search Urban Dictionary for you.
`{0}cowsay <text>`: Cow says moo. And you can order the cow to speak for you.

**Misc**
`{0}avatar [optional: @user mention]`: View yours or someone's avatar.
`{0}poll \"Title of Poll\" \"Option 1\" \"Option 2\" [\"Option 3\"...]`: Create a reaction poll.
`{0}whois <@user mention>`: Get information about a user.

**Reactions**
*Usage* `{0}<command name> <@user mention>`: `{0}hug`,`{0}kiss`,`{0}pat`,`{0}tickle`,`{0}bite`,
`{0}kick`,`{0}slap`,`{0}punch`,`{0}poke`.
*Usage* `{0}<command name>`: `{0}laugh`,`{0}cry`,`{0}blush`,`{0}confused`,`{0}pout`,`{0}dance`,
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
`{0}setwlchannel`: Set up welcome/leave message channel.
`{0}setwelcome <new string>`: Change the default welcome string, or disable it by `{0}setwelcome None`.
`{0}setleave <new string>`: Change the default leave string, or disable it by `{0}setleave None`.

**NOTE: Bot is still in pre-alpha. Be prepared for bugs. Report bugs at https://discord.gg/HkN7ReX**
""".format(PREFIX)
