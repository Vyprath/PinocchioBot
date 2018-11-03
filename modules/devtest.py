async def hello_world(client, message, *args):
    await message.channel.send("Heya, {0}. N(args) = {2}. Your args: \"{1}\"".format(
        message.author, args, len(args),
    ))
    perms = message.author.guild_permissions
    admin = perms.administrator
    await message.channel.send(
        "Your guild permissions: \n```{0}```. Admin: {1}".format(perms, admin)
    )


devtest_functions = {
    'hello': (hello_world, None)
}
