import os
import re
import time

import discord
from discord.ext import commands

from .utils.dataIO import dataIO


class ExtraAPI:
    """API du module Extra venant ajouter divers outils d'administration système"""
    def __init__(self, bot, path):
        self.bot = bot
        self.sys = dataIO.load_json(path)

    def logit(self, niveau, module: str, desc: str, solution: str=None):
        jour = time.strftime("%d/%m/%Y", time.localtime())
        heure = time.strftime("%H:%M", time.localtime())
        self.sys["SYSLOGS"].append([heure, jour, str(niveau), module.upper(), desc, solution])
        #niveau = 0, 1 ou 2

    def getlogs(self, *parametres):
        if not parametres:
            return self.sys["SYSLOGS"]
        logs = []
        parametres = " ".join(parametres)
        balises = re.compile(r"(jour|module|niveau|ignorer):(\w)", re.IGNORECASE | re.DOTALL).findall(" ".join(parametres))
        for b in balises:
            if b[0] is "module":
                logs = [l for l in self.sys["SYSLOGS"] if l[3] == b[1].upper()]
            elif b[0] is "niveau":
                logs = [l for l in self.sys["SYSLOGS"] if l[2] == b[1]]
            elif b[0] is "ignorer":
                logs = [l for l in self.sys["SYSLOGS"] if l[2] != b[1]]
            elif b[0] is "jour":
                logs = [l for l in self.sys["SYSLOGS"] if l[1] == b[1]]
        return logs

class Extra:
    """"Extra | Module d'aide à l'administration du système et outils divers"""
    def __init__(self, bot):
        self.bot = bot
        self.api = ExtraAPI(bot, "data/extra/sys.json")

    @commands.command(pass_context=True)
    async def logs(self, ctx, *parametres):
        """Affiche les logs détaillés du bot

        Paramètres:
        'module:<nom du module>' = voir les logs par module
        'niveau:<0, 1 ou 2>' = voir les logs par niveau
        'ignorer:<0, 1 ou 2>' = inverse de 'niveau'
        'jour:<jj/mm/aaaa>' = jour à rechercher"""
        logs = self.api.getlogs(parametres)
        jour = time.strftime("%d/%m/%Y", time.localtime())
        heure = time.strftime("%H:%M", time.localtime())
        if logs:
            logs.reverse()
            txt = ""
            for l in logs[:15]:
                if l[1] == jour:
                    if l[0] == heure:
                        "*{}* | **A l'instant** - {}{} [{}]\n".format(l[2], l[4], " > {}".format(l[5]) if l[5] else "",
                                                                      l[3])
                    else:
                        "*{}* | **{}** - {}{} [{}]\n".format(l[2], l[0], l[4], " > {}".format(l[5]) if l[5] else "",
                                                             l[3])
                else:
                    "*{}* | **{}** - {}{} [{}]\n".format(l[2], l[1], l[4], " > {}".format(l[5]) if l[5] else "", l[3])
            em = discord.Embed(title="Logs Bot{}".format("| {}".format("/".join(parametres))) if parametres else "",
                               description=txt)
            em.set_footer(text="Certains modules peuvent ne pas être compatible avec ce système de logs.")
            await self.bot.say(embed=em)
        else:
            await self.bot.say("**Erreur** | Aucun log n'est disponible avec les options recherchées.")


def check_folders():
    if not os.path.exists("data/extra"):
        print("Création du dossier EXTRA...")
        os.makedirs("data/extra")


def check_files():
    if not os.path.isfile("data/extra/sys.json"):
        print("Création de Extra/sys.json")
        dataIO.save_json("data/extra/sys.json", {"SYSLOGS": []})


def setup(bot):
    check_folders()
    check_files()
    n = Extra(bot)
    bot.add_cog(n)
