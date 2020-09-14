import asyncio
import time
from datetime import datetime

import aiofiles

import variables

QUEUE = None


async def log_to_file(items):
    async with aiofiles.open(variables.LOG_FILE, "a") as f:
        await f.write("\n".join(items) + "\n")


async def start_logging():
    global QUEUE
    buffer = []
    QUEUE = asyncio.Queue()
    last = time.time()
    while True:
        item = await QUEUE.get()
        buffer.append(item)
        if (
            len(buffer) >= variables.LOG_BUFFER
            or time.time() - last > variables.LOG_WAIT_MAX_SEC
        ):
            if variables.LOG_FILE is not None:
                await log_to_file(buffer)
            last = time.time()
            buffer.clear()


async def log(user, guild, item):
    if not QUEUE:
        return
    guildtxt = f"[{str(guild) }]({ guild.id })" if guild else "DM"
    content = str(item).replace("\n", "\n\t")
    await QUEUE.put(
        f"$ {str(datetime.now())} - [{ str(user) }]({ user.id }) - {guildtxt} - {content}"
    )
