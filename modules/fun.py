async def avatar_url(client, message, *args):
    if len(message.mentions) == 0:
        member = message.author
    else:
        member = message.mentions[0]
    await message.channel.send("Avatar URL: {0}".format(member.avatar_url))


fun_functions = {  # Kek, this feels like I am stuttering to say functions.
    'avatar': (avatar_url, "View yours or someone's avatar."),
}
