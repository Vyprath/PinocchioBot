import asyncio


num_to_emote = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "keycap_ten",
}
num_to_uni_emote = {
    0: "0⃣",
    1: "1⃣",
    2: "2⃣",
    3: "3⃣",
    4: "4⃣",
    5: "5⃣",
    6: "6⃣",
    7: "7⃣",
    8: "8⃣",
    9: "9⃣",
    10: "🔟",
}
uni_emote_to_num = {
    "0⃣": 0,
    "1⃣": 1,
    "2⃣": 2,
    "3⃣": 3,
    "4⃣": 4,
    "5⃣": 5,
    "6⃣": 6,
    "7⃣": 7,
    "8⃣": 8,
    "9⃣": 9,
    "🔟": 10,
}


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
