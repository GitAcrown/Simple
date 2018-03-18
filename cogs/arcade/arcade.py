import asyncio
import os
import random

import discord
from discord.ext import commands

from .utils.dataIO import fileIO, dataIO


class Arcade:
    """Jeux divers d'Entre Kheys"""

    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/arcade/sys.json") # Fichier paramètres
        self.data = dataIO.load_json("data/arcade/data.json") # Fichier de joueurs
        self.cycle_task = bot.loop.create_task(self.loop())
        self.instances = {}
        self.q_mstr = {}
        self.q_eqip = {}

    async def loop(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(5)  # Temps de mise en route
            while True:
                for i in self.instances:
                    if self.instances[i]["DESPAWN"] == 1:
                        await self.despawn(i)
                    else:
                        self.instances[i]["DESPAWN"] = 1
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    def open(self, user: discord.Member):
        if user.id not in self.data:
            self.data[user.id] = {"EQUIP": None,
                                  "INV": [],
                                  "ATK": 2,
                                  "DEF": 1,
                                  "VIE": 20,
                                  "PSEUDO": user.name}
        self.data[user.id]["PSEUDO"] = user.name
        return self.data[user.id]

    async def despawn(self, mid):
        if mid in self.instances:
            message = self.instances[mid]["MSG"]
            entity = self.instances[mid]["ENNEMI"]
            em = discord.Embed(title="Q_α | {}".format(entity["NOM"]), color=entity["COLOR"],
                               description="**A FUI**")
            await self.bot.edit_message(embed=em)
            await self.bot.clear_reactions(message)
            del self.instances[mid]
        else:
            return False

    @commands.command(pass_context=True)
    async def spawn(self, ctx, model: int, channel: discord.Channel = None):
        """Permet de faire spawn une entité sur le salon désiré. Par défaut le salon de la commande."""
        if not channel:
            channel = ctx.message.channel
        if model == 0:
            entity = {"NOM": "Boudin",
                      "DESC": "C'est une blague ?!?",
                      "ATK": 3,
                      "DEF": 1,
                      "VIE": 30,
                      "EQUIP": None,
                      "IMG": "https://cdn.discordapp.com/emojis/300398776252628996.png",
                      "COLOR": 0xe0bb28}
        elif model == 1:
            entity = {"NOM": "Gollum",
                      "DESC": "*sort de la cage*",
                      "ATK": 2,
                      "DEF": 2,
                      "VIE": 12,
                      "EQUIP": None,
                      "IMG": "https://cdn.discordapp.com/emojis/334144438647652352.png",
                      "COLOR": 0x82503b}
        elif model == 2:
            entity = {"NOM": "Larry",
                      "DESC": "Un coup de CHANCE.",
                      "ATK": 1,
                      "DEF": 5,
                      "VIE": 20,
                      "EQUIP": None,
                      "IMG": "https://cdn.discordapp.com/emojis/391241567794626560.png",
                      "COLOR": 0xdda78b}
        else:
            await self.bot.say("Modèle #{} non disponible.".format(model))
            return
        eqip = [{"NOM": "Claquette de Chatoune",
                 "BONUS_ATK": 2,
                 "BONUS_DEF": 0,
                 "BONUS_VIE": 0},
                {"NOM": "Chaise d'Evos",
                 "BONUS_ATK": 0,
                 "BONUS_DEF": 1,
                 "BONUS_VIE": 5},
                {"NOM": "Bouclier LGBT",
                 "BONUS_ATK": 0,
                 "BONUS_DEF": 3,
                 "BONUS_VIE": 0}]
        arme = random.choice(eqip)
        entity["EQUIP"] = arme
        entity["ATK"] += arme["BONUS_ATK"]
        entity["DEF"] += arme["BONUS_DEF"]
        entity["VIE"] += arme["BONUS_VIE"]

        em = discord.Embed(title="Q_α | {}".format(entity["NOM"]), color=entity["COLOR"],
                           description=entity["DESC"])
        txt = "`{}` **PV**\n" \
              "**ATK** `{}`\n" \
              "**DEF** `{}`\n" \
              "**EQUIP** `{} ({}, {}, {})`".format(entity["VIE"],
                                                  entity["ATK"],
                                                  entity["DEF"],
                                                  entity["EQUIP"]["NOM"],
                                                  entity["EQUIP"]["BONUS_VIE"],
                                                  entity["EQUIP"]["BONUS_ATK"],
                                                  entity["EQUIP"]["BONUS_DEF"])
        em.set_thumbnail(url= entity["IMG"])
        em.add_field(name="STATS", value=txt)
        em.set_footer(text="💢 Attaquer")
        msg = await self.bot.send_message(channel, embed=em)
        await self.bot.add_reaction(msg, "💢")
        if msg.id not in self.instances:
            self.instances[msg.id] = {"ENNEMI": entity,
                                      "COMBATTANTS": {},
                                      "DESPAWN": 0,
                                      "MSG": msg}

    async def react_add(self, reaction, user):
        message = reaction.message
        channel = message.channel
        server = message.server
        if user.bot:
            return
        if message.id in self.instances:
            acc = self.open(user)
            entity = self.instances[message.id]["ENNEMI"]
            if user.id not in self.instances[message.id]["COMBATTANTS"]:
                self.instances[message.id]["COMBATTANTS"][user.id] = acc
            critique = True if random.randint(0, 10) == 0 else False
            hit = acc["ATK"] * 2 if critique else acc["ATK"]
            entity["VIE"] -= hit
            if entity["VIE"] > 0:

                em = discord.Embed(title="Q_α | {}".format(entity["NOM"]), color=entity["COLOR"],
                                   description=entity["DESC"])
                txt = "`{}` **PV**\n" \
                      "**ATK** `{}`\n" \
                      "**DEF** `{}`\n" \
                      "**EQUIP** `{} ({}, {}, {})`".format(entity["VIE"],
                                                          entity["ATK"],
                                                          entity["DEF"],
                                                          entity["EQUIP"]["NOM"],
                                                          entity["EQUIP"]["BONUS_VIE"],
                                                          entity["EQUIP"]["BONUS_ATK"],
                                                          entity["EQUIP"]["BONUS_DEF"])
                em.add_field(name="STATS", value=txt)
                em.set_thumbnail(url=entity["IMG"])
                dlg = random.choice(["Aïe ! Vous avez fait {} dgts !", "Bien joué ! {} dgts.", "{} dgts ! Bien fait !"])
                self.instances[message.id]["DESPAWN"] = 0
                em.set_footer(text=dlg.format(hit))
                await self.bot.edit_message(message, embed=em)
                await self.bot.remove_reaction(message, reaction.emoji, user)
            else:
                em = discord.Embed(title="Q_α | {}".format(entity["NOM"]), color=0xededed,  # he's ded
                                   description="***MORT***")
                em.set_thumbnail(url=entity["IMG"])
                liste = ""
                for p in self.instances[message.id]["COMBATTANTS"]:
                    liste += "- *{}*\n".format(self.instances[message.id]["COMBATTANTS"][p]["PSEUDO"])
                em.add_field(name="GAGNANTS", value=liste)
                em.set_footer(text="Vous avez vaincu {} avec succès ! GG !".format(entity["NOM"]))
                await self.bot.edit_message(message, embed=em)
                await self.bot.clear_reactions(message)

def check_folders():
    if not os.path.exists("data/arcade"):
        print("Création du dossier arcade...")
        os.makedirs("data/arcade")


def check_files():
    if not os.path.isfile("data/arcade/sys.json"):
        print("Création du fichier arcade/sys.json...")
        fileIO("data/arcade/sys.json", "save", {})
    if not os.path.isfile("data/arcade/data.json"):
        print("Création du fichier arcade/data.json...")
        fileIO("data/arcade/data.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Arcade(bot)
    bot.add_cog(n)
    bot.add_listener(n.react_add, "on_reaction_add")