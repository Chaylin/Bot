import discord
import pymongo
import asyncio
import pathlib
import json
from table2ascii import table2ascii as t2a
import requests
from Game.config import ConfigStuff

should_run = ConfigStuff().read_config_bool('game', 'account', 'discord_bot')
TOKEN = ''
client = discord.Client()
m_client = pymongo.MongoClient(
    "mongodb+srv://admin:admin@cluster0.kxi86.mongodb.net/Database?retryWrites=true&w=majority")
db = m_client.tribalwars

path_notify = pathlib.Path(__file__).parent.absolute().joinpath("ConfigFiles\data.txt")
channel_id = 1002863359571537950


@client.event
async def on_ready():
    print('logged in as {0.user}'.format(client))
    client.loop.create_task(update_notifications())


async def update_notifications():
    while True:
        with open(path_notify, 'r') as file:
            content = json.load(file)
        while len(content['notifications']) > 0:
            await send_notification(content['notifications'][0])
            content['notifications'].pop(0)
        with open(path_notify, 'w') as file:
            json.dump(content, file)
        await asyncio.sleep(20)


async def send_notification(notification):
    channel = client.get_channel(channel_id)
    await channel.send(notification)
    return


@client.event
async def on_message(message):
    user_msg = str(message.content)
    channel = str(message.channel.name)
    if message.author == client.user:
        return

    if channel == 'chat-bot':

        if '!help' in user_msg.lower():
            output = t2a(
                header=["Command", "database", "key", "value", "query"],
                body=[
                    ["!set", "player202", "build", "true/false", "player-name"],
                    ["!set", "player202", "gather", "true/false", "player-name"],
                    ["!set", "player202", "farm", "true/false", "player-name"],
                    ["!set", "player202", "recruit", "true/false", "player-name"],
                    ["!set", "player202", "apm_cap", "0-150", "player-name"],
                    ["!set", "player202", "sleep", "0-150", "player-name"],
                    ["!set", "player202", "timeout-farm", "0-60", "player-name"],
                    ["!set", "villages202", "build", "true/false", "village-id"],
                    ["!set", "villages202", "gather", "true/false", "village-id"],
                    ["!set", "villages202", "farm", "true/false", "village-id"],
                    ["!set", "villages202", "recruit", "true/false", "village-id"],
                ],
                first_col_heading=True
            )
            await message.channel.send(f"```\n{output}\n```")
            output = t2a(
                header=["Command", "database", "query"],
                body=[
                    ["!get", "player202", "player-name"],
                    ["!get", "village202", "village-id"],

                ],
                first_col_heading=True
            )
            await message.channel.send(f"```\n{output}\n```")
            output = t2a(
                header=["Special commands", "function"],
                body=[
                    ["!who is not farming?", "all vils with farm disabled"],
                    ["!who is not gathering?", "all vils with gather disabled"],
                ],
                first_col_heading=True
            )
            await message.channel.send(f"```\n{output}\n```")

        # !get player202 stoffl2108
        if '!get player' in user_msg.lower() or '!get village' in user_msg.lower():
            if '!get player' in user_msg.lower():
                try:
                    player_name = str(user_msg.lower()).split(' ')[2]
                    if len(str(user_msg.lower()).split(' ')) > 2:
                        player_name = f"{str(user_msg.lower()).split(' ')[2]} {str(user_msg.lower()).split(' ')[3]}"
                    data = get_player(str(user_msg.lower()).split(' ')[1], player_name)
                except IndexError:
                    await message.channel.send('No data found!')
                    return
                if data:
                    output = t2a(
                        header=["Setting", "Value"],
                        body=[
                            ['build', data['build']],
                            ['gather', data['gather']],
                            ['farm', data['farm']],
                            ['recruit', data['recruit']],
                            ['apm_cap', data['apm_cap']],
                            ['sleep', data['sleep']],
                            ['timeout_farm', data['timeout_farm']],
                            ['farmassist_axe', data['farmassist_axe']],
                            ['farmassist_light', data['farmassist_light']],
                            ['farmassist_marcher', data['farmassist_marcher']],
                            ['farmassist_heavy', data['farmassist_heavy']],
                        ],
                        first_col_heading=True
                    )
                    await message.channel.send(f"```\n{output}\n```")

                else:
                    await message.channel.send('No data found!')
                return
            if '!get village' in user_msg.lower():
                try:
                    data = get_village(str(user_msg.lower()).split(' ')[1], str(user_msg.lower()).split(' ')[2])
                except IndexError:
                    await message.channel.send('No data found! Maybe miss some space?')
                    return
                if data:
                    output = t2a(
                        header=["Setting", "Value"],
                        body=[
                            ['build', data['build']],
                            ['gather', data['gather']],
                            ['farm', data['farm']],
                            ['recruit', data['recruit']],
                        ],
                        first_col_heading=True
                    )
                    await message.channel.send(f"```\n{output}\n```")

                else:
                    await message.channel.send('No data found! Maybe miss some space?')
                return

        if '!who is not farming?' in user_msg.lower():
            vils = get_all_farm_disabled('own_villages202')
            output = t2a(
                header=["Name", "ID"],
                body=vils,
                first_col_heading=True
            )
            await message.channel.send(f"```\n{output}\n```")

        if '!who is not gathering?' in user_msg.lower():
            vils = get_all_gather_disabled('own_villages202')
            output = t2a(
                header=["Name", "ID"],
                body=vils,
                first_col_heading=True
            )
            await message.channel.send(f"```\n{output}\n```")

        if '!ultimate' in user_msg.lower():
            try:
                url = str(user_msg).split(' ')[1]
                r = requests.get(url)
                if r.ok:
                    pass

            except IndexError:
                await message.channel.send("Can't read DS Ultimate Import, something went wrong!")
                return

        # !set village202 gather_units spear true 9999 (all)
        if 'gather_units' in user_msg.lower():
            if '!set' in user_msg.lower():
                try:
                    set_gather_units(
                        str(user_msg.lower()).split(' ')[1],
                        str(user_msg.lower()).split(' ')[3],
                        str(user_msg.lower()).split(' ')[4],
                        str(user_msg.lower()).split(' ')[5],
                    )
                    if 'all' in user_msg.lower():
                        await message.channel.send('Apply these settings to every village!')
                        return

                    data = get_village(str(user_msg.lower()).split(' ')[1],
                                       str(user_msg.lower()).split(' ')[5])
                    if data:
                        output = t2a(
                            header=["Units", "Value"],
                            body=[
                                ['spear', data['gather_units']['spear']],
                                ['sword', data['gather_units']['sword']],
                                ['axe', data['gather_units']['axe']],
                                ['archer', data['gather_units']['archer']],
                                ['light', data['gather_units']['light']],
                                ['marcher', data['gather_units']['marcher']],
                                ['heavy', data['gather_units']['heavy']],
                            ],
                            first_col_heading=True
                        )
                        await message.channel.send(f"```\n{output}\n```")

                    else:
                        await message.channel.send('No data found!')
                    return

                except IndexError:
                    await message.channel.send('No data found! Maybe miss some keys or space?')
                    return

        # !set player farm true stoffl2108
        if '!set' in user_msg.lower() and 'gather_units' not in user_msg.lower():
            try:
                if '!set player' in user_msg.lower():
                    set_player(str(user_msg.lower()).split(' ')[1],
                               str(user_msg.lower()).split(' ')[4],
                               str(user_msg.lower()).split(' ')[2],
                               user_msg.lower().split(' ')[3],
                               )
                    data = get_player(str(user_msg.lower()).split(' ')[1],
                                      str(user_msg.lower()).split(' ')[4])
                    if data:
                        output = t2a(
                            header=["Setting", "Value"],
                            body=[
                                ['build', data['build']],
                                ['gather', data['gather']],
                                ['farm', data['farm']],
                                ['recruit', data['recruit']],
                                ['apm_cap', data['apm_cap']],
                                ['sleep', data['sleep']],
                                ['timeout_farm', data['timeout_farm']],
                                ['farmassist_axe', data['farmassist_axe']],
                                ['farmassist_light', data['farmassist_light']],
                                ['farmassist_marcher', data['farmassist_marcher']],
                                ['farmassist_heavy', data['farmassist_heavy']],
                            ],
                            first_col_heading=True
                        )
                        await message.channel.send(f"```\n{output}\n```")

                    else:
                        await message.channel.send('No data found!')
                    return

                elif '!set village' in user_msg.lower():
                    set_village(str(user_msg.lower()).split(' ')[1],
                                str(user_msg.lower()).split(' ')[4],
                                str(user_msg.lower()).split(' ')[2],
                                user_msg.lower().split(' ')[3],
                                )
                    data = get_village(str(user_msg.lower()).split(' ')[1],
                                       str(user_msg.lower()).split(' ')[4])
                    if data:
                        output = t2a(
                            header=["Setting", "Value"],
                            body=[
                                ['build', data['build']],
                                ['gather', data['gather']],
                                ['farm', data['farm']],
                                ['recruit', data['recruit']],
                            ],
                            first_col_heading=True
                        )
                        await message.channel.send(f"```\n{output}\n```")

                    else:
                        await message.channel.send('No data found!')
                    return
                else:
                    await message.channel.send('Did u mean "!set player..." or "!set village..." ?')
                    return
            except IndexError:
                await message.channel.send('No data found! Maybe miss some keys or space?')
                return


def get_player(database, player_name):
    find = {"player": player_name}
    result = db[database].find_one(find)
    return result


def get_village(database, village_id):
    find = {"id": str(village_id)}
    result = db[f'own_{database}'].find_one(find)
    return result


def get_all_farm_disabled(database):
    find = {'farm': False}
    result = db[database].find(find)
    vils = []
    for x in result:
        vils.append([x['game_data']['village']['name'], x['game_data']['village']['id']])
    return vils


def get_all_gather_disabled(database):
    find = {'gather': False}
    result = db[database].find(find)
    vils = []
    for x in result:
        vils.append([x['game_data']['village']['name'], x['game_data']['village']['id']])
    return vils


def set_gather_units(database, key, value, query):
    if 'all' in query:
        update = {{}, {"$set": {key: bool(value)}}}
        db[database].update(update)
    else:
        update = {"$set": {key: bool(value)}}
        query = {'id': query}
        db[database].update_one(query, update)


def set_player(database, player_name, key, value):
    if value.isnumeric():
        value = int(value)
    if type(value) == str:
        if 'false' in value:
            value = False
    if type(value) == str:
        if 'true' in value:
            value = True
    find = {"player": player_name}
    if '[' in key:
        f_key = str(key.split('[')[0])
        n_key = str(key.split('[')[1])
        nested_key = str(n_key.replace("]", ""))
        data = {f"{f_key}": {f"{nested_key}": value}}
    else:
        data = {f"{key}": value}

    result = db[database].find_one(find)
    if result:
        update = {"$set": data}
        db[database].update_one(find, update)


def set_village(database, village_id, key, value):
    if value.isnumeric():
        value = int(value)
    if type(value) == str:
        if 'false' in value:
            value = False
    if type(value) == str:
        if 'true' in value:
            value = True
    find = {"id": village_id}
    data = {f"{key}": value}
    result = db[f'own_{database}'].find_one(find)
    if result:
        update = {"$set": data}
        db[f'own_{database}'].update_one(find, update)


def run():
    if should_run:
        client.run(TOKEN)
    else:
        print('DiscordBot is set to false')


# DS ULTIMATE IMPORT #
""" 19500&10923&ram&1661531441000&8&false&true&spear=/sword=/axe=/archer=/spy=/light=/marcher=/heavy=/ram=/catapult=/knight=/snob=/militia=MA==
            startID & targetID & slowestUnit & timestamp impact & type & ....
            type:
                8 Off
                11 Eroberung
                45 Wallbrecher
                14 Fake
                0 Unterstützung
                30 main
                31 barracks
                32 stable
                33 garage
                34 church
                35 snob
                36 smith
                37 place
                38 statue
                39 market
                40 wood
                41 stone
                42 iron
                43 farm
                44 storage"""
