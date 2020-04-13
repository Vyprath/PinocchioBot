import asyncio


async def paginate_embed(client, channel, embed, total_pages, modifier_func):
    """
    async def modifier_func(type, curr_page) type: 1 for forward, -1 for backward.
    """
    og_msg = await channel.send(embed=embed)
    if total_pages <= 1:
        return

    curr_page = 0

    await og_msg.add_reaction("⬅")
    await og_msg.add_reaction("➡")

    def check(reaction, user):
        return (
            not user.bot
            and reaction.message.channel == channel
            and reaction.message.id == og_msg.id
        )

    seen = False
    try:
        while not seen:
            reaction, purchaser = await client.wait_for(
                "reaction_add", timeout=120.0, check=check
            )
            if str(reaction.emoji) == "➡":
                if curr_page < total_pages - 1:
                    curr_page += 1
                    await modifier_func(1, curr_page)
                    await og_msg.edit(embed=embed)
                await og_msg.remove_reaction("➡", purchaser)
            elif str(reaction.emoji) == "⬅":
                if curr_page > 0:
                    curr_page -= 1
                    await modifier_func(-1, curr_page)
                    await og_msg.edit(embed=embed)
                await og_msg.remove_reaction("⬅", purchaser)
            else:
                continue
    except asyncio.TimeoutError:
        await og_msg.remove_reaction("⬅", client.user)
        await og_msg.remove_reaction("➡", client.user)
        return


def chunks(listt, division):
    for i in range(0, len(listt), division):
        yield listt[i : i + division]
