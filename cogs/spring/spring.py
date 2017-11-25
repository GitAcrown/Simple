import asyncio
import datetime
import os
import random
import string
import time

import discord
from __main__ import send_cmd_help
from discord.ext import commands

from .utils import checks
from .utils.dataIO import fileIO, dataIO

class Spring:
    """Module principal des fonctionnalités Entre Kheys (1ere Gen.)"""
    def __init__(self, bot):
        self.bot = bot
        self.data = dataIO.load_json("data/spring/data.json")
        self.version = "Spring 1.1 InProgess"

    def save(self):
        fileIO("data/spring/data.json", "save", self.data)
        return True

    def u_upi(self, id):
        """Utile > Utilisateur Par ID"""
        for s in self.bot.servers:
            for m in s.members:
                if m.id == id:
                    return m
        else:
            return False

    def u_cd(self, user):
        """Utile > Obtenir la couleur de disponibilité"""
        s = user.status
        if not user.bot:
            if s == discord.Status.online:
                return 0x43B581 #Vert
            elif s == discord.Status.idle:
                return 0xFAA61A #Jaune
            elif s == discord.Status.dnd:
                return 0xF04747 #Rouge
            else:
                return 0x9ea0a3 #Gris
        else:
            return 0x2e6cc9 #Bleu

    def u_sprid(self):
        """Utile > Générer un ID Spring"""
        clef = "//" + str(''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in
            range(4)))
        return clef

    def u_bar(self, prc):
        ch1 = "░"
        ch2 = "▒"
        ch3 = "█"
        nb = int(prc / 10)
        bar = ""
        while len(bar) < nb:
            bar += ch3
        if len(bar) < 10:
            bar += ch2
        while len(bar) < 10:
            bar += ch1
        return bar

    def u_rolebar(self, member):
        """Génère un STR de la barre de progression jusqu'au prochain rôle (Hab. ou Old.)"""
        hab = 14
        old = 120
        days = (datetime.datetime.now() - member.joined_at).days
        if "Habitué" not in [r.name for r in member.roles]:
            if "Oldfag" not in [r.name for r in member.roles]:
                if days <= hab:
                    n = days / hab * 100
                    return "**> Habitué**\n" + self.u_bar(n) + " *{}%*".format(int(n))
                else:
                    return "**> Habitué**\n" + self.u_bar(100) + " *100%*"
            else:
                return "**Rôle max. atteint**"
        else:
            if "Oldfag" not in [r.name for r in member.roles]:
                if days <= old:
                    n = days / old * 100
                    return "**> Oldfag**\n" + self.u_bar(n) + " *{}%*".format(int(n))
                else:
                    return "**> Oldfag**\n" + self.u_bar(100) + " *100%*"
            else:
                return "**Rôle max. atteint**"

    def rang(self, val: int):
        if val < 50:
            return ["Carton", "https://i.imgur.com/EOlpHHK.png"]
        elif 50 <= val < 200:
            return ["Bronze", "https://i.imgur.com/G1QTkM8.png"]
        elif 200 <= val < 1000:
            return ["Argent", "https://i.imgur.com/Z5RXSQC.png"]
        elif 1000 <= val < 10000:
            return ["Or", "https://i.imgur.com/UZvAWYX.png"]
        elif 10000 <= val < 30000:
            return ["Rubis", "https://i.imgur.com/28D3N8W.png"]
        elif 30000 <= val < 75000:
            return ["Saphir", "https://i.imgur.com/pH86yq2.png"]
        elif 75000 <= val < 150000:
            return ["Emeraude", "https://i.imgur.com/bWTO5jl.png"]
        elif 150000 <= val:
            return ["Diamant", "https://i.imgur.com/hYyZuZQ.png"]
        else:
            return ["Inconnu", "?"]

    def rang_actif(self, jours: int, msg: int):
        if jours == 0: jours = 1
        ratio = msg / jours
        if ratio < 25:
            return "I"
        elif 25 <= ratio < 75:
            return "II"
        elif 150 <= ratio < 275:
            return "III"
        elif 275 <= ratio < 450:
            return "IV"
        elif 450 <= ratio:
            return "V"
        else:
            return False

    def open(self, user: discord.Member):
        if user.id not in self.data:
            self.data[user.id] = {"SPRID": self.u_sprid(),
                                  "TS_ORIGIN": time.time(),
                                  "JEUX_NV": [],
                                  "XP": 0,
                                  "PSEUDOS": [user.name],
                                  "SURNOMS": [user.display_name],
                                  "OPTS": {"BIO": None, "URL": None}}
            self.save()
        return self.data[user.id]

    def open_id(self, id):
        if id not in self.data:
            self.data[id] = {"SPRID": self.u_sprid(),
                                  "TS_ORIGIN": time.time(),
                                  "JEUX_NV": [],
                                  "XP": 0,
                                  "PSEUDOS": [],
                                  "SURNOMS": [],
                                  "OPTS": {"BIO": None, "URL": None}}
            self.save()
        return self.data[id]

    @commands.group(aliases=["spr"], pass_context=True)
    async def spring(self, ctx):
        """Gestion des profils Spring Gen. I"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @spring.command(pass_context=True, hidden=True)
    async def majrang(self, ctx, max: int):
        """Permet de mettre manuellement à jour les rangs de membre en consultant les X derniers messages.

        ATTENTION : Processus très long ! (+30m)"""
        id = "204585334925819904"
        await self.bot.say("**Mise à jour en cours** | Ce processus peut prendre plusieures minutes...")
        channel = self.bot.get_channel(id)
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
            user = msg.author
            if user.id not in data:
                data[user.id] = 0
            data[user.id] += 1
        for u in data:
            g = self.open_id(u)
            g["XP"] = data[u]
        self.save()
        await self.bot.say("**Mise à jour terminée** | Vous pouvez consulter vos rangs sur vos cartes (*&c*)")

    @spring.command(pass_context=True)
    async def bio(self, ctx, *txt):
        """Changer sa bio sur sa carte de membre"""
        u = self.open(ctx.message.author)
        txt = " ".join(txt)
        u["OPTS"]["BIO"] = txt
        await self.bot.say("**Succès** | Votre bio s'affichera en haut de votre carte de membre")
        self.save()

    @commands.command(aliases=["carte", "c"], pass_context=True, no_pm=True)
    async def card(self, ctx, membre: discord.Member=None):
        """Affiche la carte de membre d'un utilisateur

        Si <membre> n'est pas spécifié, renverra votre propre carte"""
        if membre is None: membre = ctx.message.author
        self.open(membre)
        usertxt = membre.name if membre.display_name == membre.name else "{} «{}»".format(membre.name,
                                                                                          membre.display_name)
        desctxt = self.open(membre)["OPTS"]["BIO"]
        rang = self.rang(self.open(membre)["XP"])
        activ = self.rang_actif((ctx.message.timestamp - membre.joined_at).days, self.open(membre)["XP"])
        if membre == ctx.message.author and self.open(membre)["OPTS"]["BIO"] is None:
            desctxt = "Ajoutez une description avec &spr bio"
        em = discord.Embed(title=usertxt, description=desctxt, color=self.u_cd(membre),
                           url=self.open(membre)["OPTS"]["URL"])
        em.set_thumbnail(url=membre.avatar_url)
        em.add_field(name="IDs", value="{}\n**{}**".format(membre.id, self.open(membre)["SPRID"]))
        passed = (ctx.message.timestamp - membre.created_at).days
        em.add_field(name="Création", value="**{}** jours".format(passed))
        passed = (ctx.message.timestamp - membre.joined_at).days
        oldtxt = "**{}** jours\n".format(passed)
        oldtxt += self.u_rolebar(membre)
        em.add_field(name="Ancienneté", value=oldtxt)
        rolelist = "/".join([r.name for r in membre.roles if r.name != "@everyone"])
        em.add_field(name="Roles", value=rolelist if rolelist else "Aucun rôle")
        ancpsd = ", ".join(self.open(membre)["PSEUDOS"][3:])
        ancsur = ", ".join(self.open(membre)["SURNOMS"][3:])
        psdtxt = "**Pseudos**: {}\n**Surnoms**: {}".format(ancpsd if ancpsd else "*?*", ancsur if ancsur else "*?*")
        em.add_field(name="Précédemment", value=psdtxt)
        em.set_footer(text="Rang {} {}{}".format(rang[0], activ, " | Joue à {}".format(membre.game) if membre.game else ""),
                      icon_url=rang[1])
        await self.bot.say(embed=em)

    async def l_profil(self, avant, apres):
        spr = self.open(apres)
        if avant.name != apres.name:
            if apres.name not in spr["PSEUDOS"]:
                spr["PSEUDOS"].append(apres.name)
        if apres.display_name != avant.display_name:
            if apres.display_name not in spr["SURNOMS"]:
                spr["SURNOMS"].append(apres.display_name)
        self.save()

    async def l_leave(self, user):
        id = "204585334925819904" #Hall
        channel = self.bot.get_channel(id)
        r = ["Au revoir, ***{}*** petit ange.", "***{}*** a quitté notre monde.", "***{}*** a quitté la partie.",
             "***{}*** s'est déconnecté un peu trop violemment", "RIP ***{}*** :cry:", "Bye bye *{}*",
             "***{}*** a appuyé sur le mauvais bouton...", "***{}*** a quitté la secte.",
             "***{}*** est mort ! Il va respawn non ?", "***{}*** est sorti de la Matrice !",
             "***{}*** est tombé du bord de la Terre !",
             "***{}*** a été banni... Non je déconne, il est parti tout seul.",
             "***{}*** a ragequit le serveur.", "/suicide ***{}***",
             "Je crois que ***{}*** est parti...", "***{}*** a raccroché.",
             "***{}*** est en fuite...", "***{}*** s'est libéré de ses chaines !",
             "***{}*** s'est suicidé de deux balles dans le dos."]
        await self.bot.send_message(channel, "**>** " + random.choice(r).format(user.name))

    async def l_msg(self, message):
        author = message.author
        u = self.open(author)
        u["XP"] += 1
        self.save()

    async def l_msgdel(self, message):
        author = message.author
        u = self.open(author)
        u["XP"] -= 1
        self.save()

    async def l_leave(self, member):
        u = self.open(member)
        if u["XP"] > 100:
            u["XP"] -= 100
        else:
            u["XP"] = 0
        self.save()

    async def l_ban(self, member):
        u = self.open(member)
        u["XP"] = 0
        self.save()

    """@commands.command(aliases=["fp"], pass_context=True, no_pm=True, hidden=True)
    async def fastpoll(self, ctx, *arg):
        Permet de créer, modifier et paramétrer une interface de vote
        [arg] = Question ?;Réponse1;Réponse2;RéponseN...
        Exemple: Allez-vous bien ?;Oui;Non;Peut-être

        Il est possible de faire un poll avancé avec &sp | &smartpoll
        arg = " ".join(arg)
        q = arg.split(";")[0]
        r = arg.split(";")[1:]
        emojis = [s for s in "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"]
        r = lambda: random.randint(0, 255)
        rcolor = int('0x%02X%02X%02X' % (r(), r(), r()), 16)
        return

    async def l_reactadd(self, reaction, user):
        return

    async def l_reactrem(self, reaction, user):
        return"""

def check_folders():
    if not os.path.exists("data/spring"):
        print("Création du dossier Spring...")
        os.makedirs("data/spring")


def check_files():
    if not os.path.isfile("data/spring/data.json"):
        print("Ouverture de Spring > data.json")
        fileIO("data/spring/data.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Spring(bot)
    bot.add_listener(n.l_profil, "on_member_update")
    bot.add_listener(n.l_leave, "on_member_remove")
    bot.add_listener(n.l_msg, "on_message")
    bot.add_listener(n.l_msgdel, "on_message_delete")
    bot.add_listener(n.l_leave, "on_member_remove")
    bot.add_listener(n.l_ban, "on_member_ban")
    # bot.add_listener(n.l_reactadd, "on_reaction_add")
    # bot.add_listener(n.l_reactrem, "on_reaction_remove")
    bot.add_cog(n)