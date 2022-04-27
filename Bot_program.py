import os
import json
import requests
import discord
import asyncio
from better_profanity import profanity
import emoji


intents = discord.Intents.all()
client = discord.Client(intents=intents)

# URL = Your model's url
API_URL = os.getenv('URL')
# HFT = Your read hugginface access token
headers = {"Authorization": f"Bearer {os.getenv('HFT')}"}


def query(payload):

    data = json.dumps(payload)
    response = requests.request("POST", API_URL, headers=headers, data=data)
    return json.loads(response.content.decode("utf-8"))


@client.event
async def on_ready():

    print(f'Logged in')

    # load the model on inference API
    query({'inputs': {'text': 'Wake up.'}})


@client.event
async def on_message(msg):

    mess = msg.content

    # ignore attachments, non bot messages and own message
    if msg.author.id == client.user.id or mess == '' or mess.startswith('!!not') or msg.embeds or msg.is_system():
        return

    # censor and delete messages containing profanities
    if profanity.contains_profanity(mess):
        async with msg.channel.typing():
            await asyncio.sleep(1)
        altered_msg = profanity.censor(mess, '-')
        await msg.reply(f"`Language`\n {altered_msg}")
        await msg.delete()
        return

    # clear chat history (only accessed by Moderator role)
    if mess.startswith('!!del'):
        if "Moderator" in [role.name for role in msg.author.roles]:
            try:
                int(mess[5:])
                assert int(mess[5:])>0
            except (TypeError, ValueError, AssertionError):
                await msg.reply("```Only positive integers < 1000 accepted.```")
            else:
                try:
                    await msg.channel.purge(limit=int(mess[5:])+1 if int(mess[5:]) < 1000 else 1000)
                except(discord.Forbidden, discord.HTTPException):
                    await msg.reply("```Error occurred. Maybe messages are older than 2 weeks.```")
                
        else:
            await msg.reply("```You need a Moderator role to use that command.```")

    # process user input
    else:
        clean_text = emoji.replace_emoji(mess, replace='')
        # if full of emojis don't waste API calls
        if not clean_text:
            await asyncio.sleep(1)
            await msg.reply("I didn't get that.")
            return
        payload = {'inputs': {'text': clean_text}}
        async with msg.channel.typing():
            response = query(payload)
        answer = response.get('generated_text', None)
        # log errors and handle empty string
        if not answer:
            if 'error' in response:
                answer = '```Notice: {}```'.format(response['error'])
            else:
                answer = "I didn't get that."
        try:
            await msg.reply(answer)
        except(discord.HTTPException):
            await msg.reply("`Let me think again.`")
# DT = Your discord bot application token
client.run(os.getenv('DT'))

