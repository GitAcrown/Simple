import asyncio
import os
from .utils import checks
import discord
from collections import namedtuple
from __main__ import send_cmd_help
from discord.ext import commands
import time
import operator
import random
from .utils.dataIO import fileIO, dataIO
import re
import datetime
import string


class SquidApp:
    """API SQUID | Système aggrégateur de données et services spécialisés"""
    def __init__(self, bot, path):
        self.bot = bot
        self.data = dataIO.load_json(path)

    def saveapp(self) -> bool:
        fileIO("data/squid/data.json", "save", self.data)
        return True

    def open(self, user: discord.Member) -> dict:
        if user.id not in self.data:
            c = "//" + str(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in
                                   range(4)))
            self.data[user.id] = {"SID": c,
                                  "SOLDE": 0,
                                  "PSEUDOS": [user.name],
                                  "SURNOMS": [user.display_name],
                                  "BIO": None,
                                  "PAST": [],
                                  "JEUX": [],
                                  "DATA": {}}
        self.update(user)
        return self.data[user.id]

    def force_open(self, id) -> dict:
        if id not in self.data:
            c = "//" + str(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in
                                   range(4)))
            self.data[id] = {"SID": c,
                             "SOLDE": 0,
                             "PSEUDOS": [],
                             "SURNOMS": [],
                             "BIO": None,
                             "JEUX": [],
                             "PAST": [],
                             "DATA": {}}
            self.saveapp()
        return self.data[id]

    def update(self, user: discord.Member) -> bool:
        majdata = [["MSG_PART", 0],
                   ["MSG_REEL", 0],
                   ["JOIN", 0],
                   ["QUIT", 0],
                   ["BAN", 0]]
        majsimple = [["AUTOPSEUDO", False]]
        p = self.data[user.id]
        for u in majdata:
            if u[0] not in p["DATA"]:
                p["DATA"][u[0]] = u[1]
        for u in majsimple:
            if u[0] not in p:
                p[u[0]] = u[1]
        self.saveapp()
        return True

    def u_bar(self, prc) -> str:
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

    def rolebarre(self, member) -> str or bool:
        """Génère un STR de la barre de progression jusqu'au prochain rôle (Hab. ou Old.)"""
        hab = 14
        old = 120
        days = (datetime.datetime.now() - member.joined_at).days
        if "Habitué" not in [r.name for r in member.roles]:
            if "Oldfag" not in [r.name for r in member.roles]:
                if days <= hab:
                    n = days / hab * 100
                    return "**Progression:** *Habitué*\n" + self.u_bar(n) + " *{}%*".format(int(n))
                else:
                    return "**Progression:** *Habitué*\n" + self.u_bar(100) + " *100%*"
            else:
                return "**Progression:** *Maximum*"
        else:
            if "Oldfag" not in [r.name for r in member.roles]:
                if days <= old:
                    n = days / old * 100
                    return "**Progression:** *Oldfag*\n" + self.u_bar(n) + " *{}%*".format(int(n))
                else:
                    return "**Progression:** *Oldfag*\n" + self.u_bar(100) + " *100%*"
            else:
                return "**Progression:** *Maximum*"

    def color_status(self, user) -> hex:
        s = user.status
        if not user.bot:
            if s == discord.Status.online:
                return 0x43B581  # Vert
            elif s == discord.Status.idle:
                return 0xFAA61A  # Jaune
            elif s == discord.Status.dnd:
                return 0xF04747  # Rouge
            else:
                return 0x9ea0a3  # Gris
        else:
            return 0x2e6cc9      # Bleu

    def rang(self, val: int) -> list:
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

    def qualif(self, jours: int, msg: int) -> str:
        if jours == 0: jours = 1
        ratio = int(msg / jours)
        if ratio < 25:
            return "I"
        elif 25 <= ratio < 75:
            return "II"
        elif 75 <= ratio < 200:
            return "III"
        elif 200 <= ratio < 400:
            return "IV"
        elif 400 <= ratio:
            return "V"
        else:
            return "?"

    def add_past(self, user: discord.Member, category: str, event:str) -> bool:
        types = ["punition", "identite", "role", "presence"]
        if category in types:
            p = self.open(user)
            jour = time.strftime("%d/%m/%Y", time.localtime())
            heure = time.strftime("%H:%M", time.localtime())
            p["PAST"].append([heure, jour, category, event])
            return True
        else:
            print("Impossible de créer un nouvel évenement pour {} (EventNotInList)".format(str(user)))
            return False

    def infos(self, membre: discord.Member, timestamp):
        p = self.open(membre)
        formatname = membre.name if membre.display_name == membre.name else "{} «{}»".format(membre.name,
                                                                                          membre.display_name)
        bio = p["BIO"] if p["BIO"] else "*Ajoutez une description avec* **&m bio**"
        rang = self.rang(p["DATA"]["MSG_REEL"])[0]
        rangimg = self.rang(p["DATA"]["MSG_REEL"])[1]
        actif = self.qualif((timestamp - membre.joined_at).days, p["DATA"]["MSG_REEL"])
        statuscolor = self.color_status(membre)
        sid = p["SID"]
        creation = (timestamp - membre.created_at).days
        datecreation = membre.created_at.strftime("%d/%m/%Y")
        arrive = (timestamp - membre.joined_at).days
        datearrive = membre.joined_at.strftime("%d/%m/%Y")
        roles = ", ".join([r.name for r in membre.roles if r.name != "@everyone"])
        if not roles: roles = None
        pseudoslist = p["PSEUDOS"] if p["PSEUDOS"] else "?"
        surnomslist = p["SURNOMS"] if p["SURNOMS"] else "?"
        past = p["PAST"] if p["PAST"] else None
        # By compiling...
        Infos = namedtuple('Infos', ["sid", "bio", "formatname", "rang", "rangimg", "qualif", "statuscolor", "creation",
                                     "date_creation", "depuis", "date_depuis", "roles", "liste_pseudos",
                                     "liste_surnoms", "past"])
        return Infos(sid, bio, formatname, rang, rangimg, actif, statuscolor, creation, datecreation, arrive, datearrive, roles,
                     pseudoslist, surnomslist, past)


class Squid:
    """SQUID | Fonctionnalités statistiques et avancées"""
    def __init__(self, bot):
        self.bot = bot
        self.app = SquidApp(bot, "data/squid/data.json")  # API\\SQUID
        self.glb = dataIO.load_json("data/squid/global.json")
        self.sys = dataIO.load_json("data/squid/sys.json")

    def save(self) -> bool:
        self.app.saveapp()
        fileIO("data/squid/global.json", "save", self.glb)
        fileIO("data/squid/sys.json", "save", self.sys)
        return True

    def getglb(self) -> dict:
        today = time.strftime("%d/%m/%Y", time.localtime())
        if today not in self.glb:
            self.glb[today] = {"MSG_PART": 0,
                               "MSG_REEL": 0,
                               "JOIN": 0,
                               "QUIT": 0,
                               "BAN": 0}
        self.save()
        return self.glb[today]

    @commands.command(pass_context=True)
    async def random(self, ctx):
        """Génère un pseudo aléatoire (Système syllabique)"""
        await self.bot.say("**{}**".format(self.gen_pseudo()))

    @commands.group(aliases=["m"], pass_context=True)
    async def modif(self, ctx):
        """Paramètres Squid personnels"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @modif.command(pass_context=True, hidden=True)
    async def autopseudo(self, ctx):
        """Permet d'activer/désactiver le changement automatique de pseudos à chaque message"""
        u = self.app.open(ctx.message.author)
        if u["AUTOPSEUDO"] is False:
            u["AUTOPSEUDO"] = True
            await self.bot.say("Votre pseudo changera automatiquement à chaque nouveau message. N'en abusez pas...")
        else:
            u["AUTOPSEUDO"] = False
            await self.bot.say("Votre pseudo ne changera plus à chaque nouveau message.")
        self.save()

    @modif.command(pass_context=True, hidden=True)
    @checks.admin_or_permissions(manage_nicknames=True)
    async def modautopseudo(self, ctx, user: discord.Member):
        """Permet d'activer/Désactiver le changement automatique de pseudo pour un autre membre
        (Modération seulement)"""
        u = self.app.open(user)
        if u["AUTOPSEUDO"] is False:
            u["AUTOPSEUDO"] = True
            await self.bot.say("Son pseudo changera désormais à chaque nouveau message.")
        else:
            u["AUTOPSEUDO"] = False
            await self.bot.say("Son pseudo ne changera plus à chaque nouveau message.")
        self.save()

    @modif.command(pass_context=True)
    async def bio(self, ctx, *texte: str):
        """Permet de modifier la bio de sa carte de membre (L'en-tête)"""
        u = self.app.open(ctx.message.author)
        u["BIO"] = " ".join(texte)
        await self.bot.say("**Succès** | Votre bio s'affichera en haut de votre carte de membre")
        self.app.saveapp()

    @modif.command(pass_context=True, hidden=True)
    async def majrang(self, ctx, max: int):
        """Permet de mettre manuellement à jour les rangs de membre en consultant les X derniers messages.

        ATTENTION : Processus très long ! (+30m)"""
        id = "204585334925819904"
        channel = self.bot.get_channel(id)
        await self.bot.say("**Mise à jour en cours** | Ce processus peut prendre plusieures minutes...")
        data = {}
        n = 0
        async for msg in self.bot.logs_from(channel, limit=max):
            n += 1
            if n == (0.25 * max):
                await self.bot.say("**MAJ** | Env. 25%")
            if n == (0.50 * max):
                await self.bot.say("**MAJ** | Env. 50%")
            if n == (0.75 * max):
                await self.bot.say("**MAJ** | Env. 75%")
            if n == (0.90 * max):
                await self.bot.say("**MAJ** | Env. 90%")
            user = msg.author
            if user.id not in data:
                data[user.id] = 0
                self.app.open(user)
            data[user.id] += 1
        for u in data:
            g = self.app.force_open(u)
            g["DATA"]["MSG_REEL"] = data[u]
            g["DATA"]["MSG_PART"] = data[u]
        self.app.saveapp()
        await self.bot.say("**Mise à jour terminée** | Vous pouvez consulter vos rangs sur vos cartes (*&c*)")
        await self.bot.send_message(channel, "**Processus terminé** | "
                                             "Retour à la normale (Cartes mises à jour)")

    @commands.command(aliases=["carte", "c"], pass_context=True, no_pm=True)
    async def card(self, ctx, membre: discord.Member = None):
        """Affiche la carte de membre d'un utilisateur

        Si <membre> n'est pas spécifié, renverra votre propre carte"""
        if membre is None: membre = ctx.message.author
        today = time.strftime("%d/%m/%Y", time.localtime())
        data = self.app.infos(membre, ctx.message.timestamp)
        em = discord.Embed(title=data.formatname, description=data.bio, color=data.statuscolor)
        em.set_thumbnail(url=membre.avatar_url)
        em.add_field(name="Identifiants", value="**ID:** {}\n**SID:** {}".format(membre.id, data.sid))
        em.add_field(name="Dates", value="**Création:** {} (**{}** jours)\n"
                                         "**Arrivée:** {} (**{}** jours)".format(data.date_creation,
                                                                                 data.creation,
                                                                                 data.date_depuis, data.depuis))
        em.add_field(name="Rôles", value="***{}***\n\n{}".format(data.roles if data.roles else "***Aucun***",
                                                               self.app.rolebarre(membre)))
        em.add_field(name="Anciennement", value="**Pseudos:** {}\n**Surnoms:** {}".format(", ".join(data.liste_pseudos[-3:]),
                                                                                          ", ".join(data.liste_surnoms[-3:])))
        txt = ""
        if data.past:
            b = data.past[-3:]
            b.reverse()
            for e in b:
                if e[1] == today:
                    txt += "**{}** - *{}*\n".format(e[0], e[3])
                else:
                    txt += "**{}** - *{}*\n".format(e[1], e[3])
        else:
            txt = "Aucune action"
        em.add_field(name="Historique", value=txt)
        em.set_footer(text="Rang {} {}{}".format(data.rang, data.qualif,
                                                 " | Joue à {}".format(membre.game) if membre.game else ""),
                      icon_url=data.rangimg)
        await self.bot.say(embed=em)

    async def l_msg(self, message):
        author = message.author
        glb = self.getglb()
        p = self.app.open(author)
        p["DATA"]["MSG_PART"] += 1
        p["DATA"]["MSG_REEL"] += 1
        glb["MSG_PART"] += 1
        glb["MSG_REEL"] += 1
        self.save()
        if p["AUTOPSEUDO"] is True:
            try:
                await self.bot.change_nickname(author, self.gen_pseudo())
            except:
                pass

    def gen_pseudo(self):
        l = ["la", "li", "le", "lu", "le", "lo", "lou", "loi",
             "ra", "ri", "re", "ru", "re", "ro", "rou", "roi",
             "ma", "mi", "me", "mu", "me", "mo", "mou", "moi",
             "pa", "pi", "pe", "pu", "pe", "po", "pou", "poi",
             "ta", "ti", "te", "tu", "te", "to", "tou", "toi",
             "na", "ni", "ne", "nu", "ne", "no", "nou", "noi",
             "da", "di", "de", "du", "de", "do", "dou", "doi",
             "ba", "bi", "be", "bu", "be", "bo", "bou", "boi",
             "cha", "chi", "che", "chu", "che", "cho", "chou", "choi",
             "sha", "shi", "she", "shu", "she", "sho", "shou", "shoi",
             "ka", "ki", "ke", "ku", "ke", "ko", "kou", "koi",
             "ja", "ji", "je", "ju", "je", "jo", "jou", "joi",
             "ya", "yi", "ye", "yu", "ye", "yo", "you", "yoi",
             "xa", "xi", "xe", "xu", "xe", "xo", "xou", "xoi"]
        nb = random.randint(2, 5)
        nom = ""
        for b in range(0, nb):
            nom += random.choice(l)
        return nom.capitalize()

    async def l_msgdel(self, message):
        author = message.author
        glb = self.getglb()
        p = self.app.open(author)
        p["DATA"]["MSG_REEL"] -= 1
        glb["MSG_REEL"] -= 1
        self.save()

    async def l_join(self, user):
        p = self.app.open(user)
        glb = self.getglb()
        if p["DATA"]["JOIN"] == 0:
            self.app.add_past(user, "presence", "A rejoint le serveur")
        else:
            self.app.add_past(user, "presence", "Est de retour sur le serveur")
        glb["JOIN"] += 1
        p["DATA"]["JOIN"] += 1
        self.save()

    async def l_quit(self, user):
        p = self.app.open(user)
        glb = self.getglb()
        self.app.add_past(user, "presence", "A quitté le serveur")
        glb["QUIT"] += 1
        p["DATA"]["QUIT"] += 1
        id = "204585334925819904"  # Hall
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
        self.save()

    async def l_ban(self, user):
        p = self.app.open(user)
        glb = self.getglb()
        self.app.add_past(user, "presence", "A été banni")
        glb["BAN"] += 1
        p["DATA"]["BAN"] += 1
        self.save()

    async def l_profil(self, before, after):
        p = self.app.open(after)
        user = after
        if after.name != before.name:
            p["PSEUDOS"].append(after.name)
            self.app.add_past(user, "identite", "Est devenu **{}**".format(after.name))
        if after.display_name != before.display_name:
            if after.display_name != after.name:
                p["SURNOMS"].append(after.display_name)
                self.app.add_past(user, "identite", "Est désormais surnommé **{}**".format(after.display_name))
        if after.avatar_url != before.avatar_url:
            heure = time.strftime("%H:%M", time.localtime())
            if p["PAST"]:
                if p["PAST"][-1][0] == heure:
                    return
            self.app.add_past(user, "identite", "A changé son avatar: [Avant]({}) > [Après]({})".format(
                before.avatar_url, after.avatar_url))
            return
        if after.game:
            if after.game.name:
                if after.game.name.lower() not in p["JEUX"]:
                    p["JEUX"].append(after.game.name.lower())
        self.app.saveapp()


def check_folders():
    if not os.path.exists("data/squid"):
        print("Creation du dossier SQUID...")
        os.makedirs("data/squid")


def check_files():
    if not os.path.isfile("data/squid/data.json"):
        print("Création et import de Squid/data")
        fileIO("data/squid/data.json", "save", {})
    if not os.path.isfile("data/squid/global.json"):
        print("Création et import de Squid/global")
        fileIO("data/squid/global.json", "save", {})
    if not os.path.isfile("data/squid/sys.json"):
        print("Création et import de Squid/sys")
        fileIO("data/squid/sys.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Squid(bot)
    bot.add_listener(n.l_msg, "on_message")
    bot.add_listener(n.l_msgdel, "on_message_delete")
    # bot.add_listener(n.l_react, "on_reaction_add")
    bot.add_listener(n.l_join, "on_member_join")
    bot.add_listener(n.l_quit, "on_member_remove")
    bot.add_listener(n.l_profil, "on_member_update")
    bot.add_listener(n.l_ban, "on_member_ban")
    # bot.add_listener(n.l_voice, "on_voice_state_update")
    bot.add_cog(n)