from variables import PREFIX as P
from discord import Embed


main_help_menu = Embed(
    title="Pinocchio Bot Usage",
    description=f"""
**NOTE:** Arguments inside <> are necessary, and inside [] are optional.
**Support Server: https://support.pinocchiobot.xyz**
**For additional help, do `{P}help <command name>`.**
To get the old help message with description, do `{P}fullhelp`.
    """,
)
main_help_menu.add_field(
    name=":robot: General",
    inline=False,
    value=f"`{P}help`, `{P}support`, `{P}donate`, `{P}creator`, `{P}vote`, `{P}claimreward`, `{P}invite`, `{P}botstats/{P}botinfo/{P}info`, `{P}ping`,`{P}poll`, `{P}whois`, `{P}worldleaderboard/{P}wlb/{P}worldlb`, `{P}guildleaderboard/{P}glb/{P}guildlb/{P}leaderboard`, `{P}say/{P}pinosay`",
)
main_help_menu.add_field(
    name=":moneybag: Financial",
    inline=False,
    value=f"`{P}wallet`, `{P}transfer`, `{P}dailies`, `{P}paidroles`, `{P}customrole`, `{P}discoin`, `{P}exchange`",
)
main_help_menu.add_field(
    name="<a:RainbowWeeb:564012559590752256> Waifu",
    inline=False,
    value=f"`{P}waifu`, `{P}search`, `{P}buy`, `{P}sell`, `{P}details`, `{P}trade`, `{P}moneytrade`, `{P}favorite`, `{P}unfavorite`, `{P}harem`, `{P}randomroll/{P}rr`, `{P}rolls`",
)
main_help_menu.add_field(
    name="<:UmaruCool:575381825296400384> Anime",
    inline=False,
    value=f"`{P}anime`, `{P}manga`, `{P}animelist`, `{P}mangalist`, `{P}profile`, `{P}nyaa`, `{P}whichanime`",
)
main_help_menu.add_field(
    name="<:SmartHuh:575382892520275980> Quiz **NEW**",
    inline=False,
    value=f"`{P}quiz`, `{P}tquiz/{P}textquiz`, `{P}wquiz/{P}waifuquiz`",
)
main_help_menu.add_field(
    name="<a:MikuKurukurupa:564012084631699456> Fun",
    inline=False,
    value=f"`{P}chucknorris`, `{P}dadjoke`, `{P}xkcd`, `{P}catfact`, `{P}8ball`, `{P}cook`, `{P}lmgtfy`, `{P}urbandictionary`, `{P}cowsay`, `{P}avatar`",
)
main_help_menu.add_field(
    name="<a:PKomiEars:575382520179326979> Reactions",
    inline=False,
    value=f"`{P}hug`, `{P}kiss`, `{P}pat`, `{P}tickle`, `{P}bite`, `{P}kick`, `{P}slap`, `{P}punch`, `{P}poke`, `{P}laugh`, `{P}cry`, `{P}blush`, `{P}confused`, `{P}pout`, `{P}dance`, `{P}jojo`, `{P}megumin`, `{P}satania`, `{P}lick`, `{P}think`, `{P}shrug`, `{P}owo`, `{P}nom`, `{P}eyeroll`, `{P}lewd`, `{P}stare`, `{P}triggered`,`{P}facepalm`, `{P}gif`",
)
main_help_menu.add_field(
    name=":musical_note: Music (Donator-only Feature)",
    inline=False,
    value=f"`{P}play/{P}p`, `{P}pause`, `{P}resume`, `{P}leave`, `{P}skip`, `{P}queue`, `{P}volume`, `{P}status`",
)
main_help_menu.add_field(
    name=":tools: Administration",
    inline=False,
    value=f"`{P}setpaidroles`, `{P}setcustomroles`, `{P}setwlchannel`, `{P}setwelcome`, `{P}setleave`, `{P}coindrops`, `{P}rescuewaifus`, `{P}forcedivorceallwaifus`, `{P}forcedivorcewaifus`, `{P}purge`",
)
main_help_menu.set_footer(text=f"For additional help, do {P}help <command name>.")


full_help_text = """
__**Pinocchio Bot Usage:**__
**NOTE:** Arguments inside <> are necessary, and inside [] are optional.
**Bot**
`{0}help`: Get the commands and a brief description.
`{0}help <command name>`: A little more detailed description (if available).
`{0}donate`: Donate to this bot UwU.
`{0}creator`: Get to know the creator of this bot, so you can annoy him to fix the damned bugs.
`{0}vote`: Vote for this bot! Isn't Pinocchio kawaii? Vote for her and make her happy. _(sorry)_
`{0}claimreward`: Pinocchio is happy now! Thanks for voting. Here, collect your reward.
`{0}invite`: Get the invite link for this server.
`{0}botstats`/`{0}botinfo`/`{0}info`: General stats about the bot.
`{0}worldleaderboard/{0}wlb/{0}worldlb`: Get the world leaderboard.
`{0}guildleaderboard/{0}glb/{0}guildlb`: Get the guild leaderboard.
`{0}say [channel, default: current] <text>`: Speak as Pinocchio!
**Financial**
`{0}wallet [optional: @user mention]`: Check your own wallet or others' wallet.
`{0}transfer-money <@user mention> <amount>`: Transfer some money.
`{0}dailies`: Get your daily money and become riiiich.
`{0}paidroles`: Get a preset role with $$$.
`{0}customrole`: Get your custom colored role with $$$$$$.
`{0}discoin`: Get information about how to exchange currency with other bots using <:Discoin:357656754642747403> Discoin. **NEW**
`{0}exchange <Pinocchio Coins> <Currency>`: Exchange currency with other bots with <:Discoin:357656754642747403> Discoin. **NEW**
**Waifu**
`{0}waifu`: Buy/Sell/View/Search/Trade/Money-Trade/Favorite/Unfavorite Waifus. Will make your loneliness disappear.
`{0}harem [@user mention] [sort option] [gender option] [series name]`: Get the list of your bought waifus. Valid sort options: `name-desc`, `series-desc`, `name-asc`, `series-asc`, `id-asc`, `id-desc`, `price-asc`, `price-desc`. Valid gender options: `waifu`, `husbando`.
`{0}randomroll`/`{0}rr`: Get a random waifu/husbando for a very cheap price. Normal users can do it 10 times per 3 hours, tier 1 donators 30 times, and tier 2 donators 90 times.
`{0}rolls`: Check how many rolls you have left for getting a random waifu. Resets every 3 hours.
**Anime**
`{0}anime <anime name>`: Get details about an anime.
`{0}manga <manga name>`: Get details about a manga.
`{0}animelist <MAL Username>`: Get someone's MAL animelist.
`{0}mangalist <MAL Username>`: Get someone's MAL mangalist.
`{0}profile <MAL Username>`: Get someone's MAL profile.
`{0}nyaa <search string>`: Get anime torrents from nyaa.si.
`{0}whichanime`: Get an anime from a scene picture. Using trace.moe.
**Fun**
*Usage* `{0}<command name>`: `{0}chucknorris`, `{0}dadjoke`, `{0}xkcd`, `{0}catfact`, `{0}8ball`.
*Usage* `{0}<command name> <@user mention>`: `{0}cook`.
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
*NOTE: To use these commands, you have to donate to the bot. After donating, please contact RandomGhost#0666 to enable this.*
*NOTE#2: HQ means highest available music quality in YouTube. To save their server bandwidth, most bots take the lowest available music quality in YouTube. Not this bot.*
`{0}play`/`{0}p`: Play some musix.
`{0}leave`: Make the bot leave the music channel **Requires administrator permission**
`{0}skip`: Skip the current song.
`{0}queue`: Get current playlist.
`{0}volume`: Set the volume. Default: 100.
`{0}pause`/`{0}resume`: Pause/Resume music.
`{0}status`: Get status about current playing music.
**Administration (Below commands require Admininstrator Permission)**
`{0}setpaidroles`: Set up paid roles.
`{0}setcustomroles`: Set price or disable custom roles.
`{0}purge <number of messages between 1 to 100>`: Purge messages from the channel.
`{0}setwlchannel`: Set up welcome/leave message channel, or disable it. Default: disabled.
`{0}setwelcome <new string>`: Change the default welcome string, or disable it by `{0}setwelcome None`.
`{0}setleave <new string>`: Change the default leave string, or disable it by `{0}setleave None`.
`{0}coindrops <disable/enable>`: Enable/Disable coin drops for a server. Default: disabled.
`{0}rescuewaifus`: Removes waifus/husbandos from people who left the server. **NEW**
**Support Server: https://support.pinocchiobot.xyz**
""".format(
    P
)
