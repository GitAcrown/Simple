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
        dataIO.save_json("data/extra/sys.json", self.sys)
        return True

    def resetlogs(self):
        self.sys["SYSLOGS"] = []
        dataIO.save_json("data/extra/sys.json", self.sys)
        return True

    def getlogs(self):
        return self.sys["SYSLOGS"]

class Extra:
    """"Extra | Module d'aide à l'administration du système et outils divers"""
    def __init__(self, bot):
        self.bot = bot
        self.api = ExtraAPI(bot, "data/extra/sys.json")

    def tri_logs(self, parametres: str = None):
        base = self.api.getlogs()
        if not parametres:
            return base
        logs = []
        balises = re.compile(r"(jour|module|niveau|ignorer):(\w+)", re.IGNORECASE | re.DOTALL).findall(parametres)
        for b in balises:
            if b[0] == "module":
                for i in base:
                    if b[1].upper() in i:
                        if i not in logs:
                            logs.append(i)
            if b[0] == "niveau":
                for i in base:
                    if b[1] == i[2]:
                        if i not in logs:
                            logs.append(i)
            if b[0] == "ignorer":
                for i in base:
                    if b[1] != i[2]:
                        if i not in logs:
                            logs.append(i)
            if b[0] == "jour":
                for i in base:
                    if b[1] == i[1]:
                        if i not in logs:
                            logs.append(i)
        else:
            return logs

    @commands.command(pass_context=True, hidden=True)
    async def totalresetlogs(self, ctx):
        """Permet de reset les logs du bot TOTALEMENT"""
        if self.api.resetlogs():
            await self.bot.say("**Succès** | Les logs ont été supprimés entièrement.")
        else:
            await self.bot.say("**Erreur** | Impossible de supprimer les logs.")

    @commands.command(pass_context=True)
    async def logs(self, ctx, *parametres):
        """Affiche les logs détaillés du bot

        Paramètres:
        'module:<nom du module>' = voir les logs par module
        'niveau:<0, 1 ou 2>' = voir les logs par niveau
        'ignorer:<0, 1 ou 2>' = inverse de 'niveau'
        'jour:<jj/mm/aaaa>' = jour à rechercher

        Niveaux:
        0 = Notification (Tout s'est bien passé)
        1 = Erreur (Une petite erreur, parfois la solution automatisée apparait avec '>')
        2 = Erreur critique (Nécéssitant souvent un redémarrage, souvent automatique, du bot ou du module)"""
        logs = self.tri_logs(" ".join(parametres)) if parametres else self.tri_logs()
        jour = time.strftime("%d/%m/%Y", time.localtime())
        heure = time.strftime("%H:%M", time.localtime())
        if logs:
            txt = ""
            for l in logs[-15:]:
                if l[1] == jour:
                    if l[0] == heure:
                        txt += "*{}* | **A l'instant** - {}{} [{}]\n".format(l[2], l[4], " > {}".format(l[5]) if l[5] else "",
                                                                      l[3])
                    else:
                        txt += "*{}* | **{}** - {}{} [{}]\n".format(l[2], l[0], l[4], " > {}".format(l[5]) if l[5] else "",
                                                             l[3])
                else:
                    txt += "*{}* | **{}** - {}{} [{}]\n".format(l[2], l[1], l[4], " > {}".format(l[5]) if l[5] else "", l[3])
            em = discord.Embed(title="Logs Bot{}".format("| {}".format("/".join(parametres)) if parametres else ""),
                               description=txt)
            em.set_footer(text="Certains modules ne supportent pas ce système de logs | Du plus ancien au plus récent")
            await self.bot.say(embed=em)
        else:
            await self.bot.say("**Erreur** | Aucun log n'est disponible avec les options recherchées (Voir `&help logs`)")


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
