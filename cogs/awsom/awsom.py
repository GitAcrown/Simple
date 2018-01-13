import asyncio
import os
import re
import time
from copy import deepcopy

import discord
from sympy import sympify
import wikipedia

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

    def redux(self, string: str, separateur: str = ".", limite: int = 2000):
        n = -1
        while len(separateur.join(string.split(separateur)[:n])) >= limite:
            n -= 1
        return separateur.join(string.split(separateur)[:n]) + separateur

    def wiki(self, recherche: str, langue: str = 'fr', souple: bool = True):
        wikipedia.set_lang(langue)
        s = wikipedia.search(recherche, 8, True)
        try:
            if s[1]:
                r = s[1]
            else:
                r = s[0][0] if s[0] else None
            if r:
                page = wikipedia.page(r, auto_suggest=souple)
                images = page.images
                image = images[0]
                for i in images:
                    if i.endswith(".png") or i.endswith(".gif") or i.endswith(".jpg") or i.endswith(".jpeg"):
                        image = i
                resum = page.summary
                if not resum:
                    resum = "Contenu indisponible"
                if len(resum) + len(r) > 1995:
                    resum = self.redux(resum, limite=1950)
                em = discord.Embed(title=r, description=resum)
                em.set_thumbnail(url=image)
                em.set_footer(text="Similaire: {}".format(", ".join(s[0])))
                return em
            else:
                if langue == "en":
                    return "Impossible de trouver {}".format(recherche)
                else:
                    return self.wiki(recherche, "en")
        except:
            if langue == "en":
                if souple:
                    if s[0]:
                        if len(s[0]) >= 2:
                            wikipedia.set_lang("fr")
                            s = wikipedia.search(recherche, 3, True)
                            return "**Introuvable** | Vouliez-vous dire *{}* ?".format(s[0][1])
                        else:
                            return "**Introuvable** | Aucun résultat pour *{}*".format(recherche)
                    else:
                        return "**Introuvable** | Aucun résultat pour *{}*".format(recherche)
                else:
                    return self.wiki(recherche, "en", False)
            else:
                if souple:
                    return self.wiki(recherche, "en")
                else:
                    return self.wiki(recherche, "fr", False)

    async def detect(self, message):  # Regex c'est la VIE
        channel = message.channel
        if message.mention_everyone:
            return
        if not hasattr(channel, 'server'):
            return
        server = channel.server
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

            output = re.compile(r"(?:re)?cherche (.*)", re.IGNORECASE | re.DOTALL).findall(msg)
            if output:
                u = output[0]
                r = self.wiki(u)
                if type(r) is str:
                    await self.bot.send_message(message.channel, r)
                else:
                    try:
                        await self.bot.send_message(message.channel, embed=r)
                    except:
                        await self.bot.send_message(message.channel, "**Erreur** | La ressource demandée est indisponible")
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
