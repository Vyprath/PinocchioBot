import logging
from variables import DB_NAME, DB_USERNAME, DB_PASSWORD
from aiopg.sa import create_engine
from sqlalchemy.schema import CreateTable
import sqlalchemy as sa

logging.basicConfig(level=logging.INFO)


meta = sa.MetaData()

Member = sa.Table(
    'members', meta,
    sa.Column('id', sa.BigInteger, primary_key=True, nullable=False),
    sa.Column('guild', sa.BigInteger, nullable=False),
    sa.Column('member', sa.BigInteger, nullable=False),
    sa.Column('wallet', sa.BigInteger, default=0, nullable=False),
    sa.Column('last_dailies', sa.DateTime),
    sa.Column('last_reward', sa.DateTime),
    sa.Column('tier', sa.SmallInteger, server_default='0')
)

Guild = sa.Table(
    'guild', meta,
    sa.Column('id', sa.BigInteger, primary_key=True, nullable=False),
    sa.Column('guild', sa.BigInteger, nullable=False),
    sa.Column('shop_roles', sa.JSON),
    sa.Column('music_enabled', sa.Boolean),
    sa.Column('coin_drops', sa.Boolean, server_default='f', nullable=False),
    sa.Column('join_leave_channel', sa.BigInteger),
    sa.Column('welcome_str', sa.String(length=60), server_default="Let the madness begin. Hold tight."),
    sa.Column('leave_str', sa.String(length=60), server_default="See you again, in another life.")
)

Waifu = sa.Table(
    'waifu', meta,
    sa.Column('id', sa.BigInteger, primary_key=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('from_anime', sa.String(length=200), nullable=False),
    sa.Column('gender', sa.String(length=1)),
    sa.Column('price', sa.BigInteger, nullable=False),
    sa.Column('image_url', sa.String(length=400)),
)

PurchasedWaifu = sa.Table(
    'purchased_waifu', meta,
    sa.Column('id', sa.BigInteger, primary_key=True, nullable=False, unique=True),
    sa.Column('member_id', sa.BigInteger, sa.ForeignKey('members.id', ondelete='CASCADE')),
    sa.Column('waifu_id', sa.BigInteger, sa.ForeignKey('waifu.id', ondelete='CASCADE')),
    sa.Column('guild', sa.BigInteger, nullable=False),
    sa.Column('member', sa.BigInteger, nullable=False),
    sa.Column('purchased_for', sa.BigInteger, nullable=False),
)

RPGWeapon = sa.Table(
    'rpg_weapon', meta,
    sa.Column('id', sa.BigInteger, primary_key=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('effects', sa.JSON, nullable=False)
)

RPGCharacter = sa.Table(
    'rpg_character', meta,
    sa.Column('id', sa.BigInteger, primary_key=True, nullable=False),
    sa.Column('member', sa.BigInteger, nullable=False),
    sa.Column('guild', sa.BigInteger, nullable=False),
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('level', sa.Integer, nullable=False),
    sa.Column('game_wallet', sa.BigInteger, nullable=False),
    sa.Column('weapon_id', sa.BigInteger, sa.ForeignKey('rpg_weapon.id', ondelete='SET NULL')),
    sa.Column('waifu_id', sa.BigInteger, sa.ForeignKey('waifu.id', ondelete='CASCADE')),
    sa.Column('purchased_waifu_id',
              sa.BigInteger, sa.ForeignKey('purchased_waifu.id', ondelete='CASCADE')),
)

tables = [Member, Guild, Waifu, PurchasedWaifu, RPGWeapon, RPGCharacter]


async def prepare_engine():
    engine = await create_engine(
        database=DB_NAME,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        host='127.0.0.1',
    )
    return engine


async def prepare_tables():
    engine = await prepare_engine()
    async with engine.acquire() as conn:
        for table in tables:
            table_name = table.name
            query = """
            SELECT * FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = N'{}'""".format(table_name)
            cursor = await conn.execute(query)
            resp = await cursor.fetchone()
            if resp is None:
                logging.info("Table {} does not exist; creating.".format(table_name))
                create_expr = CreateTable(table)
                await conn.execute(create_expr)
            else:
                logging.info("Table {} already exists.".format(table_name))


async def make_member_profile(members_list, self_id):
        engine = await prepare_engine()
        async with engine.acquire() as conn:
            create_query_values = []
            for member in members_list:
                if member.id == self_id:
                    continue
                exists_query = Member.select().where(
                    Member.c.member == member.id).where(
                    Member.c.guild == member.guild.id)
                cursor = await conn.execute(exists_query)
                res = await cursor.fetchone()
                if res is None:
                    create_query_values.append({
                        'guild': member.guild.id,
                        'member': member.id,
                        'wallet': 0,
                    })
                    logging.info('Creating profile for member {}.'.format(member.name))
            if len(create_query_values) > 0:
                create_query = Member.insert().values(create_query_values)
                await conn.execute(create_query)


async def make_guild_entry(guilds_list):
        engine = await prepare_engine()
        async with engine.acquire() as conn:
            create_query_values = []
            for guild in guilds_list:
                exists_query = Guild.select().where(
                    Guild.c.guild == guild.id)
                cursor = await conn.execute(exists_query)
                res = await cursor.fetchone()
                if res is None:
                    create_query_values.append({
                        'guild': guild.id,
                    })
                    logging.info('Creating entry for guild {}.'.format(guild.name))
            if len(create_query_values) > 0:
                create_query = Guild.insert().values(create_query_values)
                await conn.execute(create_query)


"""
async def insert_data(engine, table, values):
    async with engine.acquire() as conn:
        query = table.insert().values(values).returning(table.c.id)
        cursor = await conn.execute(query)
        resp = await cursor.fetchall()
    return [r[0] for r in resp]
"""
