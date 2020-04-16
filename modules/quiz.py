import database
import discord
import asyncio
import aiohttp
import random
from base64 import b64decode
from .utils import num_to_emote, num_to_uni_emote, uni_emote_to_num
from variables import PREFIX
from sqlalchemy.sql.expression import func
from .currency import _fetch_wallet, _remove_money, _add_money

quizes = {}


async def quiz_create(client, message, qtype, bonus_amt):
    quiz_id = qtype + hex(message.author.id)[2:] + ":" + hex(message.guild.id)[2:]
    if quiz_id in quizes:
        return await message.channel.send(
            f"You have already started a {qtype} quiz! Please end it with `{PREFIX}{qtype}quiz end` first."
        )
    engine = await database.prepare_engine()
    success = await _remove_money(engine, message.author, bonus_amt)
    if bonus_amt and not success:
        return await message.channel.send(
            f"You don't have enough coins to start a quiz with that bonus!"
        )
    quizes.update(
        {
            quiz_id: {
                "started": False,
                "win_bonus": bonus_amt,
                "members": {message.author: 0},  # {uid: points}
            }
        }
    )
    await message.channel.send(
        f"**{qtype.capitalize()} Quiz Created!**\nOthers join with `{PREFIX}{qtype}quiz join @{message.author.name}#{message.author.discriminator}`."
    )


async def quiz_join(client, message, qtype, maker):
    quiz_id = qtype + hex(maker.id)[2:] + ":" + hex(message.guild.id)[2:]
    if quiz_id not in quizes:
        return await message.channel.send(
            f"The quiz does not exist! Please create it with `{PREFIX}{qtype}quiz create` first."
        )
    quiz = quizes[quiz_id]
    if quiz["started"]:
        return await message.channel.send(
            f"This quiz has started! You can no longer join this quiz."
        )
    if message.author in quiz["members"]:
        return await message.channel.send(f"You have already joined the quiz!")
    quiz["members"].update({message.author: 0})
    await message.channel.send(f"**{qtype.capitalize()} Quiz Joined!**")


async def quiz_end(client, message, qtype):
    quiz_id = qtype + hex(message.author.id)[2:] + ":" + hex(message.guild.id)[2:]
    if quiz_id not in quizes:
        return await message.channel.send(
            f"You have not created a {qtype} quiz! Please create it with `{PREFIX}{qtype}quiz create` first."
        )
    quiz = quizes[quiz_id]
    res = []
    members = list(quiz["members"].items())
    members.sort(reverse=True, key=lambda x: x[1])
    allpts = list(set([i[1] for i in members]))
    allpts.sort()
    awarded = {}
    awardable = quiz["win_bonus"]
    if allpts[-1] > 0 and len(members) >= 3:
        awardable += 1000
    firstplace = [m[0] for m in members if m[1] == allpts[-1]]
    secondplace = (
        [m[0] for m in members if m[1] == allpts[-2]]
        if len(allpts) >= 2 and allpts[-2] > 0
        else []
    )
    thirdplace = (
        [m[0] for m in members if m[1] == allpts[-3]]
        if len(allpts) >= 3 and allpts[-3] > 0
        else []
    )
    ptsum = (
        allpts[-1]
        + (allpts[-2] if len(secondplace) > 0 else 0)
        + (allpts[-3] if len(thirdplace) > 0 else 0)
    )
    if awardable > 0 and ptsum > 0:
        engine = await database.prepare_engine()

        thirdaward = (
            0
            if len(thirdplace) == 0
            else round(awardable * allpts[-3] / ptsum / len(thirdplace))
        )
        secondaward = (
            0
            if len(secondplace) == 0
            else round(awardable * allpts[-2] / ptsum / len(secondplace))
        )
        firstaward = (
            0
            if len(firstplace) == 0
            else round(awardable * allpts[-1] / ptsum / len(firstplace))
        )
        for m in firstplace:
            await _add_money(engine, m, firstaward)
            awarded.update({m: firstaward})
        for m in secondplace:
            await _add_money(engine, m, secondaward)
            awarded.update({m: secondaward})
        for m in thirdplace:
            await _add_money(engine, m, thirdaward)
            awarded.update({m: thirdaward})

    for i, v in enumerate(members):
        medal = ""
        if i == 0:
            medal = ":first_place:"
        elif i == 1:
            medal = ":second_place:"
        elif i == 2:
            medal = ":third_place:"
        res.append(
            f"""
**[{str(i+1).zfill(2)}] __{v[0].name}#{v[0].discriminator}__ {medal}**
Points: {v[1]}{' | **Awarded ' + str(awarded[v[0]]) + ' <:PIC:668725298388271105>**' if v[0] in awarded else ''}"""
        )
    restxt = "\n".join(res)
    embed = discord.Embed(
        title=f"Results of {qtype.capitalize()} Quiz",
        description=restxt,
        color=message.author.color,
    )
    embed.set_footer(
        text=f"Quiz hosted by {message.author.name}#{message.author.discriminator}",
        icon_url=message.author.avatar_url_as(size=64),
    )
    quizes.pop(quiz_id)
    await message.channel.send(f"**{qtype.capitalize()} Quiz Over!**", embed=embed)


async def fetch_text_questions(num_q, diff):
    url = f"https://opentdb.com/api.php?amount={num_q}{'&difficulty=' + diff if diff else ''}&category=31&encode=base64"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    questions = []
    for q in data["results"]:
        cans = b64decode(q["correct_answer"]).decode("utf-8", "ignore")
        anss = [b64decode(i).decode("utf-8", "ignore") for i in q["incorrect_answers"]]
        anss.append(cans)
        random.shuffle(anss)
        questions.append(
            {
                "question": b64decode(q["question"]).decode("utf-8", "ignore"),
                "difficulty": b64decode(q["difficulty"]).decode("utf-8", "ignore"),
                "correct_answer": cans,
                "answers": anss,
            }
        )
    random.shuffle(questions)
    return questions


async def text_quiz_start(client, message, difficulty):
    quiz_id = "text" + hex(message.author.id)[2:] + ":" + hex(message.guild.id)[2:]
    if quiz_id not in quizes:
        return await message.channel.send(
            f"You have not created a text quiz! Please create it with `{PREFIX}textquiz create` first."
        )
    if difficulty.lower() not in ["easy", "medium", "hard", ""]:
        return await message.channel.send(
            f"Difficulty is optional, but has to be easy/medium/hard."
        )
    quiz = quizes[quiz_id]
    if quiz["started"]:
        return await message.channel.send(f"This quiz has started!")
    quiz["started"] = True
    members = quiz["members"]
    numrounds = min(5, 50 // len(members))
    tmpmsg = await message.channel.send(f"Preparing {difficulty} quiz... Please wait!")
    questions = await fetch_text_questions(numrounds * len(members), difficulty.lower())
    await tmpmsg.delete()

    for round in range(1, numrounds + 1):
        for member in members.keys():
            if quiz_id not in quizes:
                return
            question = questions.pop()
            embed = discord.Embed(
                title=f"Round {round}/{numrounds} - Question For {member.name}#{member.discriminator}",
                color=member.color,
                description=f"""
+5 points for correct answer.
-1 points for incorrect answer.
0 points for not attempting/skipping.
Currently, you have **{members[member]} points**.
__You have 15 seconds, good luck!__
                """,
            )
            embed.add_field(
                name="Difficulty",
                inline=False,
                value=question["difficulty"].capitalize(),
            )
            embed.add_field(name="Question", inline=False, value=question["question"])
            anstxt = "\n".join(
                [
                    f":{num_to_emote[i+1]}: : {j}"
                    for i, j in enumerate(question["answers"] + ["Skip"])
                ]
            )
            embed.add_field(name="Options", inline=False, value=anstxt)
            embed.set_footer(
                text=f"Text Quiz hosted by {message.author.name}#{message.author.discriminator}",
                icon_url=message.author.avatar_url_as(size=64),
            )
            msg = await message.channel.send(embed=embed)
            for i in range(len(question["answers"]) + 1):
                await msg.add_reaction(num_to_uni_emote[i + 1])
            atype = 0  # 1: Correct, 2: Incorrect, 3: Pass

            def check(reaction, user):
                return (
                    user == member
                    and reaction.message.channel == msg.channel
                    and reaction.message.id == msg.id
                    and str(reaction.emoji) in uni_emote_to_num.keys()
                )

            try:
                reaction, purchaser = await client.wait_for(
                    "reaction_add", timeout=15.0, check=check
                )
                ansid = uni_emote_to_num[str(reaction.emoji)] - 1
                if ansid == len(question["answers"]):
                    atype = 3
                else:
                    chosen_ans = question["answers"][ansid]
                    if chosen_ans == question["correct_answer"]:
                        atype = 1
                    else:
                        atype = 2
            except asyncio.TimeoutError:
                atype = 3
            if atype == 1:
                members[member] += 5
                embed.description = f"Correct! You have gained +5 points. You have {members[member]} points now."
            elif atype == 2:
                members[member] -= 1
                embed.description = f"Oh no! You have lost 1 point. You have {members[member]} points now."
            elif atype == 3:
                embed.description = (
                    f"Better luck next time! You have {members[member]} points now."
                )
            embed.set_field_at(
                index=1,
                name="Correct Answer",
                inline=False,
                value=question["correct_answer"],
            )
            await msg.edit(embed=embed)

    await quiz_end(client, message, "text")


async def text_quiz(client, message, *args):
    if len(args) < 1 or args[0].lower() not in ["create", "start", "join", "end"]:
        return await message.channel.send(f"Usage in {PREFIX}quiz. Please read that!")
    arg = args[0].lower()
    if arg == "create":
        return await quiz_create(
            client,
            message,
            "text",
            int(args[1]) if len(args) == 2 and args[1].isdigit() else 0,
        )
    elif arg == "join":
        if len(args) != 2 or len(message.mentions) != 1:
            return await message.channel.send(
                f"You have not specified the host! Usage is `{PREFIX}textquiz join <@host>`"
            )
        return await quiz_join(client, message, "text", message.mentions[0])
    elif arg == "end":
        return await quiz_end(client, message, "text")
    elif arg == "start":
        return await text_quiz_start(client, message, args[1] if len(args) == 2 else "")


async def fetch_waifu_questions(num_q, num_choices):
    questions = []
    question_query = (
        database.Waifu.select()
        .order_by(func.random())
        .where(database.Waifu.c.image_url.isnot(None))
        .limit(num_q)
    )
    engine = await database.prepare_engine()
    async with engine.acquire() as conn:
        cursor = await conn.execute(question_query)
        results = await cursor.fetchall()
        incorrect_answer_query = (
            database.Waifu.select()
            .order_by(func.random())
            .where(
                ~database.Waifu.c.name.in_([i[database.Waifu.c.name] for i in results])
            )
            .limit(num_q * (10+num_choices))
        )
        cursor = await conn.execute(incorrect_answer_query)
        random_answers = await cursor.fetchall()
    for q in results:
        img_url = random.choice(q[database.Waifu.c.image_url].split(","))
        cans = q[database.Waifu.c.name]
        random.shuffle(random_answers)
        anss = [i[database.Waifu.c.name] for i in random_answers[:num_choices]]
        if cans not in anss:
            anss[0] = cans
        random.shuffle(anss)
        questions.append(
            {"question": img_url, "correct_answer": cans, "answers": anss,}
        )
    random.shuffle(questions)
    return questions


async def waifu_quiz_start(client, message, difficulty):
    quiz_id = "waifu" + hex(message.author.id)[2:] + ":" + hex(message.guild.id)[2:]
    if quiz_id not in quizes:
        return await message.channel.send(
            f"You have not created a waifu quiz! Please create it with `{PREFIX}waifuquiz create` first."
        )
    quiz = quizes[quiz_id]
    if quiz["started"]:
        return await message.channel.send(f"This quiz has started!")
    quiz["started"] = True
    members = quiz["members"]
    numrounds = min(5, 50 // len(members))
    tmpmsg = await message.channel.send(f"Preparing quiz... Please wait!")
    num_choices = 4
    if difficulty == "easy":
        num_choices = 3
    elif difficulty == "medium":
        num_choices = 4
    elif difficulty == "hard":
        num_choices = 6
    questions = await fetch_waifu_questions(numrounds * len(members), num_choices)
    await tmpmsg.delete()

    for round in range(1, numrounds + 1):
        for member in members.keys():
            if quiz_id not in quizes:
                return
            question = questions.pop()
            embed = discord.Embed(
                title=f"Round {round}/{numrounds} - Question For {member.name}#{member.discriminator}",
                color=member.color,
                description=f"""
+5 points for correct answer.
-1 points for incorrect answer.
0 points for not attempting/skipping.
Currently, you have **{members[member]} points**.
__You have 15 seconds, good luck and guess the name of the waifu!__
                """,
            )
            # embed.add_field(name="Question", inline=False, value=question["question"])
            embed.set_image(url=question["question"])
            anstxt = "\n".join(
                [
                    f":{num_to_emote[i+1]}: : {j}"
                    for i, j in enumerate(question["answers"] + ["Skip"])
                ]
            )
            embed.add_field(name="Options", inline=False, value=anstxt)
            embed.set_footer(
                text=f"Waifu Quiz hosted by {message.author.name}#{message.author.discriminator}",
                icon_url=message.author.avatar_url_as(size=64),
            )
            msg = await message.channel.send(embed=embed)
            for i in range(len(question["answers"]) + 1):
                await msg.add_reaction(num_to_uni_emote[i + 1])
            atype = 0  # 1: Correct, 2: Incorrect, 3: Pass

            def check(reaction, user):
                return (
                    user == member
                    and reaction.message.channel == msg.channel
                    and reaction.message.id == msg.id
                    and str(reaction.emoji) in uni_emote_to_num.keys()
                )

            try:
                reaction, purchaser = await client.wait_for(
                    "reaction_add", timeout=15.0, check=check
                )
                ansid = uni_emote_to_num[str(reaction.emoji)] - 1
                if ansid == len(question["answers"]):
                    atype = 3
                else:
                    chosen_ans = question["answers"][ansid]
                    if chosen_ans == question["correct_answer"]:
                        atype = 1
                    else:
                        atype = 2
            except asyncio.TimeoutError:
                atype = 3
            if atype == 1:
                members[member] += 5
                embed.description = f"Correct! You have gained +5 points. You have {members[member]} points now."
            elif atype == 2:
                members[member] -= 1
                embed.description = f"Oh no! You have lost 1 point. You have {members[member]} points now."
            elif atype == 3:
                embed.description = (
                    f"Better luck next time! You have {members[member]} points now."
                )
            embed.set_field_at(
                index=0,
                name="Correct Answer",
                inline=False,
                value=question["correct_answer"],
            )
            await msg.edit(embed=embed)

    await quiz_end(client, message, "waifu")


async def waifu_quiz(client, message, *args):
    if len(args) < 1 or args[0].lower() not in ["create", "start", "join", "end"]:
        return await message.channel.send(f"Usage in {PREFIX}quiz. Please read that!")
    arg = args[0].lower()
    if arg == "create":
        return await quiz_create(
            client,
            message,
            "waifu",
            int(args[1]) if len(args) == 2 and args[1].isdigit() else 0,
        )
    elif arg == "join":
        if len(args) != 2 or len(message.mentions) != 1:
            return await message.channel.send(
                f"You have not specified the host! Usage is `{PREFIX}waifuquiz join <@host>`"
            )
        return await quiz_join(client, message, "waifu", message.mentions[0])
    elif arg == "end":
        return await quiz_end(client, message, "waifu")
    elif arg == "start":
        return await waifu_quiz_start(client, message, args[1].lower() if len(args) == 2 else "")


async def quiz(client, message, *args):
    argstxt = " ".join(args)
    if len(args) > 0:
        return await message.channel.send(
            f"`{PREFIX}quiz` is just for the rules and info. Maybe you meant `{PREFIX}textquiz {argstxt}` or `{PREFIX}waifuquiz {argstxt}`?"
        )
    await message.channel.send(
        f"""
For now, there is text quiz (`{PREFIX}textquiz/{PREFIX}tquiz`) and waifu recognising quiz (`{PREFIX}waifuquiz/{PREFIX}wquiz`)

**Rules of Quiz**

Test your knowledge on anime and/or compete with friends! You'll be asked either a multiple choice question or a true/false question.
Pick one that you think is correct, and get:
+5 points for choosing the right answer!
+0 points for skipping/not choosing.
-1 points for choosing the wrong answer.

In a multiplayer game with more than 2 players, the 1000 <:PIC:668725298388271105> is added to the money pool! (Provided winner scores >0 points).
Regardless of multi/single-player, you can provide a bonus amount yourself that will be taken from your balance. WARNING: Not scoring >0 points will result in loss of that money!

**Usage (Replace `{PREFIX}quiz` below with the type of quiz you want to play. For example, for text quiz use `{PREFIX}textquiz`, for waifu use `{PREFIX}waifuquiz` etc.):**
1. Create a quiz with `{PREFIX}quiz create [bonus]`. You will be added to the quiz by default as the host. Optionally, you can give your <:PIC:668725298388271105> that will be provided to the winners of the quiz!
2. Your friends will need to join with `{PREFIX}quiz join <@quiz host>`. If you're solo playing, ignore this step. Max 50 users at once.
3. Start the quiz with `{PREFIX}quiz start [easy|medium|hard]`!
4. The quiz will end after it has done enough rounds (max 5) or you can manually end it with `{PREFIX}quiz end` at the end of a round!
        """
    )


quiz_functions = {
    "quiz": (
        quiz,
        "`{P}quiz`: Time to battle with your friends or yourself and test your anime knowledge!",
    ),
    "textquiz": (text_quiz, "`{P}textquiz`: Text quiz based on anime!",),
    "tquiz": (text_quiz, "`{P}textquiz`: Text quiz based on anime!",),
    "waifuquiz": (waifu_quiz, "`{P}waifuquiz`: Text quiz based on anime!",),
    "wquiz": (waifu_quiz, "`{P}waifuquiz`: Text quiz based on anime!",),
}
