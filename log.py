import asyncio
import variables
from datetime import datetime
import time

queue = None

def log_to_file(items):
    with open(variables.LOG_FILE, "a") as f:
        f.write("\n".join(items) + "\n")


async def start_logging():
    global queue
    buffer = []
    queue = asyncio.Queue()
    last = time.time()
    while True:
        item = await queue.get()
        buffer.append(item)
        if len(buffer) >= variables.LOG_BUFFER or time.time() - last > variables.LOG_WAIT_MAX_SEC:
            log_to_file(buffer)
            last = time.time()
            buffer.clear()


async def log(user, guild, item):
    guildtxt = f"[{str(guild) }]({ guild.id })" if guild else "DM"
    content = str(item).replace("\n", "\n\t")
    await queue.put(
        f"$ {str(datetime.now())} - [{ str(user) }]({ user.id }) - {guildtxt} - {content}"
    )

