import logging

import sqlalchemy as sa
from databases import Database
from sqlalchemy.schema import CreateTable

from variables import DATABASE_URL

logging.basicConfig(level=logging.INFO)


meta = sa.MetaData()

Member = sa.Table(
    "members",
    meta,
    sa.Column("id", sa.BigInteger, primary_key=True, nullable=False),
    sa.Column("member", sa.BigInteger, nullable=False, unique=True),
    sa.Column("wallet", sa.BigInteger, default=0, nullable=False),
    sa.Column("last_dailies", sa.DateTime),
    sa.Column("last_reward", sa.DateTime),
    sa.Column("tier", sa.SmallInteger, server_default="0"),
    sa.Column("level", sa.BigInteger, nullable=False, server_default="0"),
)

Guild = sa.Table(
    "guild",
    meta,
    sa.Column("id", sa.BigInteger, primary_key=True, nullable=False),
    sa.Column("guild", sa.BigInteger, nullable=False, unique=True),
    sa.Column("shop_roles", sa.JSON),
    sa.Column("music_enabled", sa.Boolean),
    sa.Column("coin_drops", sa.Boolean, server_default="f", nullable=False),
    sa.Column("join_leave_channel", sa.BigInteger),
    sa.Column(
        "welcome_str",
        sa.String(length=60),
        server_default="Let the madness begin. Hold tight.",
    ),
    sa.Column(
        "leave_str",
        sa.String(length=60),
        server_default="See you again, in another life.",
    ),
    sa.Column("custom_role", sa.BigInteger, server_default="40000"),
)

Waifu = sa.Table(
    "waifu",
    meta,
    sa.Column("id", sa.BigInteger, primary_key=True, nullable=False),
    sa.Column("name", sa.String(length=200), nullable=False),
    sa.Column("from_anime", sa.String(length=200), nullable=False),
    sa.Column("gender", sa.String(length=1)),
    sa.Column("price", sa.BigInteger, nullable=False),
    sa.Column("description", sa.Text),
    sa.Column("image_url", sa.Text),
)

PurchasedWaifu = sa.Table(
    "purchased_waifu",
    meta,
    sa.Column("id", sa.BigInteger, primary_key=True, nullable=False, unique=True),
    sa.Column(
        "member_id", sa.BigInteger, sa.ForeignKey("members.id", ondelete="CASCADE")
    ),
    sa.Column("waifu_id", sa.BigInteger, sa.ForeignKey("waifu.id", ondelete="CASCADE")),
    sa.Column("guild", sa.BigInteger, nullable=False),
    sa.Column("member", sa.BigInteger, nullable=False),
    sa.Column("purchased_for", sa.BigInteger, nullable=False),
    sa.Column("favorite", sa.Boolean, nullable=False, server_default="f"),
)

tables = [Member, Guild, Waifu, PurchasedWaifu]

engine = None


async def prepare_engine():
    global engine
    if engine is None:
        engine = Database(DATABASE_URL)
        await engine.connect()
    return engine


async def prepare_tables():
    engine = await prepare_engine()
    for table in tables:
        create_expr = str(CreateTable(table))
        # Hacky solution to create table only if doesn't exist. FIXME.
        create_expr = create_expr.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
        await engine.execute(query=create_expr)


async def make_member_profile(members_list, self_id):
    engine = await prepare_engine()
    create_query_values = []
    for member in members_list:
        if member.id == self_id:
            continue
        exists_query = Member.select().where(Member.c.member == member.id)
        res = await engine.fetch_all(query=exists_query)
        if len(res) == 0:
            create_query_values.append({"member": member.id, "wallet": 0})
            logging.debug(f"Creating profile for member {member.name}.")
    if len(create_query_values) > 0:
        create_query = Member.insert(None)
        await engine.execute_many(query=create_query, values=create_query_values)


async def make_guild_entry(guilds_list):
    engine = await prepare_engine()
    create_query_values = []
    for guild in guilds_list:
        exists_query = Guild.select().where(Guild.c.guild == guild.id)
        res = await engine.fetch_all(query=exists_query)
        if len(res) == 0:
            create_query_values.append(
                {"guild": guild.id,}
            )
        logging.debug(f"Creating entry for guild {guild.name}.")
    if len(create_query_values) > 0:
        create_query = Guild.insert(None)
        await engine.execute_many(query=create_query, values=create_query_values)
