import os
import re
from copy import deepcopy

import discord
from sympy import sympify

from .utils.dataIO import fileIO, dataIO


class Awsom:
    """Expérimentations d'un module intelligent, basé sur de l'intelligence artificielle"""
    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/awsom/sys.json")

    async def do(self, message: discord.Message, txt: str):
        new_message = deepcopy(message)
        new_message.content = "&" + txt
        await self.bot.process_commands(new_message)

    async def detect(self, message):  # Regex c'est la VIE
        server = message.channel.server
        if message.content.startswith("<@{}>".format(self.bot.user.id)):
            msg = " ".join(message.content.split()[1:])
            msg = msg.replace("`", "")
            output = re.compile(r"(?:emprisonnes*|lib[èe]res*|met en prison) <@(.\d+)>(?:\s?\w*?\s)?([0-9]*[jhms])?",
                                re.IGNORECASE | re.DOTALL).findall(msg)
            if output:
                u = output[0]
                plus = " {}".format(u[1]) if u[1] else ""
                await self.do(message, "p <@{}>{}".format(u[0], plus))
                return

            output = re.compile(r"ban <@(.\d+)>", re.IGNORECASE | re.DOTALL).findall(msg)
            if output:
                u = output[0]
                await self.do(message, "ban <@{}>".format(u))
                return

            output = re.compile(r"kick <@(.\d+)>", re.IGNORECASE | re.DOTALL).findall(msg)
            if output:
                u = output[0]
                await self.do(message, "kick <@{}>".format(u))
                return

            output = re.compile(r"envoie à <@(.\d+)> (.*\w+)", re.IGNORECASE | re.DOTALL).findall(msg)
            output2 = re.compile(r"envoie (.*\w+) à <@(.\d+)>", re.IGNORECASE | re.DOTALL).findall(msg)
            if output:
                u = output[0]
                m = server.get_member(u[0])
                em = discord.Embed(title=message.author.name, description=u[1])
                await self.bot.send_message(m, embed=em)
                await self.bot.send_message(message.author, "**Message envoyé**")
                return
            elif output2:
                u = output2[0]
                m = server.get_member(u[1])
                em = discord.Embed(title=message.author.name, description=u[0])
                await self.bot.send_message(m, embed=em)
                await self.bot.send_message(message.author, "**Message envoyé**")
                return

            output = re.compile(r"combien (?:fait|font) (.*)", re.IGNORECASE | re.DOTALL).findall(msg)
            output2 = re.compile(r"calcule (.*)", re.IGNORECASE | re.DOTALL).findall(msg)
            if output:
                u = output[0]
                await self.bot.send_message(message.channel, "Ça fait `{}`".format(str(sympify(u))))
                return
            elif output2:
                u = output2[0]
                await self.bot.send_message(message.channel, "Ça fait `{}`".format(str(sympify(u))))
                return

def check_folders():
    if not os.path.exists("data/awsom"):
        print("Création du dossier Awsom...")
        os.makedirs("data/awsom")


def check_files():
    if not os.path.isfile("data/awsom/sys.json"):
        print("Création du fichier Awsom/sys.json...")
        fileIO("data/awsom/sys.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Awsom(bot)
    bot.add_cog(n)
    bot.add_listener(n.detect, "on_message")
