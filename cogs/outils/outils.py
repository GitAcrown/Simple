import asyncio
import datetime
import operator
import os
import random
import re
import time
import zipfile
from urllib import request

import discord
from __main__ import send_cmd_help
from discord.ext import commands

from .utils import checks
from .utils.dataIO import fileIO, dataIO


class Outils:
    """Module d'outils utiles à la modération ou aux statistiques"""
    def __init__(self, bot):
        self.bot = bot
        self.results = dataIO.load_json("data/outils/results.json")

    @commands.command(pass_context=True)
    async def udbg(self, ctx, chemin):
        """Permet d'obtenir les fichiers d'un module."""
        try:
            await self.bot.say("Upload en cours...")
            await self.bot.send_file(ctx.message.channel, chemin)
        except:
            await self.bot.say("Impossible d'upload ce fichier")

    def make_zipfile(self, output_filename, source_dir):
        relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
        with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
            for root, dirs, files in os.walk(source_dir):
                # add directory (needed for empty dirs)
                zip.write(root, os.path.relpath(root, relroot))
                for file in files:
                    filename = os.path.join(root, file)
                    if os.path.isfile(filename):  # regular files only
                        arcname = os.path.join(os.path.relpath(root, relroot), file)
                        zip.write(filename, arcname)

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def zip(self, ctx, chemin):
        """Permet de zipper un fichier et de l'Upload"""
        al = random.randint(0, 999)
        output = "data/outils/zipped_{}.zip".format(al)
        self.make_zipfile(output, chemin)
        await self.bot.say("Upload en cours... **Patientez**")
        try:
            await self.bot.send_file(ctx.message.channel, output)
            os.remove(output)
        except:
            await self.bot.say("Impossible d'upload le fichier...")

    @commands.command(pass_context=True)
    async def ureset(self, ctx, chemin):
        """Permet de reset un fichier JSON (Attention: Efface toutes les données)"""
        try:
            await self.bot.say("Reset du fichier en cours...")
            os.remove(chemin)
            await asyncio.sleep(1)
            if not os.path.isfile(chemin):
                print("Recréation de {} ...".format(chemin))
                fileIO(chemin, "save", {})
                await self.bot.say("Reset effectué avec succès !")
            else:
                await self.bot.say("Echec du reset...")
        except:
            await self.bot.say("Echec du reset... :(")

    @commands.command(aliases=["ss"], pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def superstats(self, ctx, max:int, channelid, nom:str):
        """Récolte des statistiques sur tous les messages d'un channel
        Prend en compte les messages, mots et lettres + premier message de chaque membre
        Un nom doit être donné afin d'enregistrer les données en JSON"""
        await self.bot.say("Début de l'analyse...")
        channel = self.bot.get_channel(channelid)
        nom = nom.lower()
        if nom in self.results:
            await self.bot.say("Nom déjà existant pour enregistrement")
            return
        data = {}
        n = 0
        async for msg in self.bot.logs_from(channel, limit=max):
            if n == (0.25 * max):
                await self.bot.say("**Analyse** | Env. 25%")
            if n == (0.50 * max):
                await self.bot.say("**Analyse** | Env. 50%")
            if n == (0.75 * max):
                await self.bot.say("**Analyse** | Env. 75%")
            if n == (0.90 * max):
                await self.bot.say("**Analyse** | Env. 90%")
            n += 1
            ts = msg.timestamp
            mots = len(msg.content.split(" "))
            lettres = len(msg.content)
            user = msg.author
            if user.id not in data:
                data[user.id] = {"OLDEST_MSG": ts,
                                 "PSEUDO": user.name,
                                 "T_MSG": 0,
                                 "T_MOTS": 0,
                                 "T_LETTRES": 0}
            if data[user.id]["OLDEST_MSG"] > ts: data[user.id]["OLDEST_MSG"] = ts
            data[user.id]["T_MSG"] += 1
            data[user.id]["T_MOTS"] += mots
            data[user.id]["T_LETTRES"] += lettres
        txt = ""
        for e in data:
            txt += "{}\t{}\t{}\t{}\n".format(data[e]["PSEUDO"],
                                             data[e]["T_MSG"],
                                             data[e]["T_MOTS"],
                                             data[e]["T_LETTRES"])
            ts = data[e]["OLDEST_MSG"]
            date = "{}/{}/{} {}:{}".format(ts.day, ts.month, ts.year, ts.hour, ts.minute)
            data[e]["OLDEST_MSG"] = date
        filename = "StatsSS_{}".format(str(random.randint(1, 999)))
        file = open("data/outils/{}.txt".format(filename), "w", encoding="utf-8")
        file.write(txt)
        file.close()
        self.results[nom] = data
        fileIO("data/outils/results.json".format(filename), "save", self.results)
        try:
            await self.bot.send_file(ctx.message.channel, "data/outils/{}.txt".format(filename))
            os.remove("data/outils/{}.txt".format(filename))
        except:
            await self.bot.say("Impossible d'upload le fichier...")

    @commands.command(aliases=["com"], pass_context=True)
    async def commandsearch(self, ctx, search_string: str):
        """Cherche une commande"""
        # Build commands list
        commands_flat = {}
        for k, v in self.bot.commands.items():
            self._add_command(k, v, commands_flat)

        # Get matches
        matches = [c for c in commands_flat if search_string in c]

        # Display embed if possible
        cmds = "\n".join(matches)
        cogs = "\n".join([str(commands_flat[m].cog_name) for m in matches])
        if not matches:
            embed = discord.Embed(colour=0xcc0000, description="**Aucun résultat pour** ***{}***".format(search_string))
            await self.bot.say(embed=embed)
        elif len(cmds) < 900 and len(cogs) < 900:
            embed = discord.Embed(colour=0x00cc00)
            embed.add_field(name="Commande", value=cmds)
            embed.add_field(name="Extension", value=cogs)
            embed.set_footer(text="{} résultat{} pour {}".format(
                len(matches), "" if len(matches) == 1 else "s", search_string))
            await self.bot.say(embed=embed)
        else:
            maxlen = len(max(matches, key=len))
            msg = "\n".join(["{0:{1}}  {2}".format(m, maxlen, str(commands_flat[m].cog_name)) for m in matches])
            for page in pagify(msg):
                await self.bot.whisper(box(page))

    def _add_command(self, name, command, commands_flat, prefix=""):
        if isinstance(command, commands.core.Group):
            prefix += " {}".format(name)
            for k, v in command.commands.items():
                self._add_command(k, v, commands_flat, prefix)
        else:
            name = "{} {}".format(prefix, name).strip()
            commands_flat[name] = command

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def activs(self, ctx, max: int, channelid):
        """Récolte des statistiques à propos de l'activité sur le serveur"""
        await self.bot.say("Début de l'analyse de l'activité du serveur...")
        channel = self.bot.get_channel(channelid)
        data = {}
        n = 0
        async for msg in self.bot.logs_from(channel, limit=max):
            if n == (0.25 * max):
                await self.bot.say("**Analyse** | Env. 25%")
            if n == (0.50 * max):
                await self.bot.say("**Analyse** | Env. 50%")
            if n == (0.75 * max):
                await self.bot.say("**Analyse** | Env. 75%")
            if n == (0.90 * max):
                await self.bot.say("**Analyse** | Env. 90%")
            n += 1
            ts = msg.timestamp
            date = "{}/{}/{}".format(ts.day, ts.month, ts.year)
            user = msg.author.id
            if date not in data:
                data[date] = {"NB_MSG": 0,
                              "POSTERS": []}
            else:
                data[date]["NB_MSG"] += 1
                if user not in data[date]["POSTERS"]:
                    data[date]["POSTERS"].append(user)
        txt = ""
        for e in data:
            txt += "{}\t{}\t{}\n".format(e, data[e]["NB_MSG"], len(data[e]["POSTERS"]))
        filename = "StatsActivite_{}".format(str(random.randint(1, 999)))
        file = open("data/outils/{}.txt".format(filename), "w", encoding="utf-8")
        file.write(txt)
        file.close()
        try:
            await self.bot.send_file(ctx.message.channel, "data/outils/{}.txt".format(filename))
            os.remove("data/outils/{}.txt".format(filename))
        except:
            await self.bot.say("Impossible d'upload le fichier...")

def check_folders():
    if not os.path.exists("data/outils"):
        print("Creation du fichier Outils ...")
        os.makedirs("data/outils")

def check_files():
    if not os.path.isfile("data/outils/results.json"):
        print("Création de Outils/Results.json ...")
        fileIO("data/outils/results.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Outils(bot)
    bot.add_cog(n)