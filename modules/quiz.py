from variables import PREFIX

async def quiz(client, message, *args):
    await message.channel.send(
        f"""
Hey! Glad to see you interested in the quiz! Unfortunately, it's still a WIP, but don't worry, it will be done soon!
Join the support server or just wait and check {PREFIX}quiz regularly!
        """)


quiz_functions = {
    "quiz": (
        quiz, "`{P}quiz`: Time to battle with your friends or yourself and test your anime knowledge!"
    )
}