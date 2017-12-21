import datetime
import operator
import os
import random
import re
import string
import time
from collections import namedtuple

import discord
from discord.ext import commands

from .utils.dataIO import fileIO, dataIO


class PrismAPI:
    """API PRISM | Pont système du module PRISM"""
    def __init__(self, bot, path):
        self.bot = bot
        self.data = dataIO.load_json(path)
        self.old = dataIO.load_json("data/squid/data.json")

# ESSENTIEL ------------------------

    def save(self) -> bool:
        fileIO("data/prism/data.json", "save", self.data)
        return True

    def open(self, user: discord.Member, cat: str = None) -> dict:
        """Renvoie les données PRISM d'un membre, à travers une catégorie optionnelle"""
        if user.id not in self.data:
            c = "//" + str(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in
                                   range(4)))
            self.data[user.id] = {"SID": c,
                                  "ORIGINE": time.time(),
                                  "ECO": {},
                                  "DATA": {"PSEUDOS": [],
                                           "SURNOMS": [],
                                           "MSG_REEL": 0,
                                           "MSG_PART": 0},
                                  "SYS": {},
                                  "PAST": [],
                                  "JEUX": {}}
            if user.id in self.old:
                self.update(user)
                self.data[user.id]["SID"] = self.old[user.id]["SID"]
                self.data[user.id]["SYS"]["BIO"] = self.old[user.id]["BIO"]
                self.data[user.id]["DATA"]["PSEUDOS"] = self.old[user.id]["PSEUDOS"]
                self.data[user.id]["DATA"]["SURNOMS"] = self.old[user.id]["SURNOMS"]
                self.data[user.id]["DATA"]["MSG_REEL"] = self.old[user.id]["DATA"]["MSG_REEL"]
                self.data[user.id]["DATA"]["MSG_PART"] = self.old[user.id]["DATA"]["MSG_PART"]
                # On extrait les données importantes de SQUID qui a servit de pont entre EGO et PRISM et on les reclasse

        self.update(user)
        if cat:
            return self.data[user.id][cat]
        return self.data[user.id]

    def update(self, user: discord.Member) -> bool:
        app = self.data[user.id]
        maj_eco = [["SOLDE", 0],
                   ["TRS", []]]  # >>ECO
        for m in maj_eco:
            if m[0] not in app["ECO"]:
                app["ECO"][m[0]] = m[1]

        maj_data = [["PSEUDOS", [user.name]],
                    ["SURNOMS", [user.display_name]],
                    ["MSG_PART", 0],
                    ["MSG_REEL", 0],
                    ["JOIN", 0],
                    ["QUIT", 0],
                    ["BAN", 0],
                    ["EMOJIS", {}]]  # >>DATA
        for m in maj_data:
            if m[0] not in app["DATA"]:
                app["DATA"][m[0]] = m[1]

        maj_sys = [["BIO", None],
                   ["QUIT_SAVE", []]]  # >>SYS
        for m in maj_sys:
            if m[0] not in app["SYS"]:
                app["SYS"][m[0]] = m[1]
        self.save()
        return True

    def get_infos(self, membre: discord.Member, himself: bool = False):
        p = self.open(membre)
        timestamp = datetime.datetime.now()
        formatname = membre.name if membre.display_name == membre.name else "{} «{}»".format(membre.name,
                                                                                          membre.display_name)
        if not himself:
            bio = p["SYS"]["BIO"] if p["SYS"]["BIO"] else ""
        else:
            bio = "*Ajoutez une description avec* **&c bio**" if not p["SYS"]["BIO"] else p["SYS"]["BIO"]
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
        pseudoslist = p["DATA"]["PSEUDOS"] if p["DATA"]["PSEUDOS"] else "?"
        surnomslist = p["DATA"]["SURNOMS"] if p["DATA"]["SURNOMS"] else "?"
        past = p["PAST"] if p["PAST"] else None
        origine = p["ORIGINE"]
        # By compiling...
        Infos = namedtuple('Infos', ["sid", "bio", "formatname", "rang", "rangimg", "qualif", "statuscolor", "creation",
                                     "date_creation", "depuis", "date_depuis", "roles", "liste_pseudos",
                                     "liste_surnoms", "past", "origine"])
        return Infos(sid, bio, formatname, rang, rangimg, actif, statuscolor, creation, datecreation, arrive,
                     datearrive, roles, pseudoslist, surnomslist, past, origine)

# OUTILS ------------------------

    def grade(self, user: discord.Member):
        roles = [r.name for r in user.roles]
        p = self.open(user, "DATA")
        timestamp = (datetime.datetime.now() - user.joined_at).days
        jours = self.since(user, "jour") if self.since(user, "jour") > timestamp else timestamp
        ratio = int(p["MSG_REEL"] / jours)
        return None  # Todo: Faire le système de grades (rank)

    def jeux_verif(self) -> list:
        verif = []
        dispo = []
        for p in self.data:  # On sort une liste des jeux vérifiés
            for g in self.data[p]["JEUX"]:
                if g not in verif:
                    verif.append(g)
                else:
                    if g not in dispo:
                        dispo.append(g)
        return dispo

    def library(self, user: discord.Member) -> list or bool:
        p = self.open(user)
        dispo = self.jeux_verif()
        if p["JEUX"]:
            liste = [[r, p["JEUX"][r]] for r in p["JEUX"] if r in dispo]
            liste = sorted(liste, key=operator.itemgetter(1), reverse=True)
            return liste if liste else False
        return False

    def since(self, user: discord.Member, format=None) -> float:
        origine = self.open(user)["ORIGINE"]
        s = time.time() - origine
        if s < 86401:
            s = 86401
        sm = s / 60  # en minutes
        if format == "minute": return sm
        sh = sm / 60  # en heures
        if format == "heure": return sh
        sj = sh / 24  # en jours
        if format == "jour": return sj
        sa = sj / 364.25  # en années
        if format == "annee": return sa
        return s

    def u_bar(self, prc) -> str:
        ch1 = "░"
        ch2 = "▒"
        ch3 = "█"
        nb = int(prc / 10)
        bar = ""
        if prc > 100:
            return self.u_bar(100)
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
        roles = [r.name for r in member.roles]
        if "Habitué" and "Oldfag" in roles:
            return ""
        elif "Habitué" in roles and "Oldfag" not in roles:
            n = (days / old) * 100
            if n > 100: n = 100
            barre = "`{} {}%`".format(self.u_bar(n), int(n))
            return "-> **Oldfag**\n" + barre
        elif "Oldfag" in roles and "Habitué" not in roles:
            n = (days / hab) * 100
            if n > 100: n = 100
            barre = "`{} {}%`".format(self.u_bar(n), int(n))
            return "-> **re-Habitué**\n" + barre
        elif "Oldfag" not in roles and "Habitué" not in roles:
            n = (days / hab) * 100
            if n > 100: n = 100
            barre = "`{} {}%`".format(self.u_bar(n), int(n))
            return "-> **Habitué**\n" + barre
        else:
            return ""

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
        if ratio < 50:
            return "I"
        elif 50 <= ratio < 100:
            return "II"
        elif 100 <= ratio < 175:
            return "III"
        elif 175 <= ratio < 300:
            return "IV"
        elif 300 <= ratio:
            return "V"
        else:
            return "?"

    def top_emote_perso(self, user:discord.Member, top: int = 3) -> list or bool:
        p = self.open(user, "DATA")
        if p["EMOJIS"]:
            liste = [[r, p["EMOJIS"][r]] for r in p["EMOJIS"]]
            liste = sorted(liste, key=operator.itemgetter(1), reverse=True)
            nl = liste[:top]
            return nl
        return False

    def prism_avatar(self):
        l = ["https://i.imgur.com/oy3rtxW.png", "https://i.imgur.com/1HBokTM.png", "https://i.imgur.com/oFux3JS.png",
             "https://i.imgur.com/yltqljv.png", "https://i.imgur.com/SN2E0Kc.png"]
        return random.choice(l)

# MODIFIERS ----------------------------

    def add_past(self, user: discord.Member, event:str) -> bool:
        p = self.open(user)
        jour = time.strftime("%d/%m/%Y", time.localtime())
        heure = time.strftime("%H:%M", time.localtime())
        p["PAST"].append([heure, jour, event])
        return True


class Prism:  # MODULE CONCRET =========================================
    """PRISM | Système aggréateur de données et services spécialisés & personnalisés"""
    def __init__(self, bot):
        self.bot = bot
        self.app = PrismAPI(bot, "data/prism/data.json")  # API\\PRISM
        self.glb = dataIO.load_json("data/prism/global.json")
        self.sys = dataIO.load_json("data/prism/sys.json")
        self.quit_msg = ["Au revoir, ***{}*** petit ange.", "***{}*** a quitté notre monde.",
                         "***{}*** a quitté la partie.", "***{}*** s'est déconnecté un peu trop violemment",
                         "RIP ***{}*** :cry:", "Bye bye *{}*", "***{}*** a appuyé sur le mauvais bouton...",
                         "***{}*** a quitté la secte.", "***{}*** est mort ! Il va respawn non ?",
                         "***{}*** est sorti de la Matrice !", "***{}*** est tombé du bord de la Terre !",
                         "***{}*** a été banni... Non je déconne, il est parti tout seul.",
                         "Je crois que ***{}*** est parti...", "***{}*** a raccroché.",
                         "***{}*** est en fuite...", "***{}*** s'est libéré de ses chaines !",
                         "***{}*** s'est suicidé de deux balles dans le dos."]
        self.quit_msg_event = ["***{}*** s'est électrocuté avec une guirlande...",
                               "***{}*** s'est suicidé avec une guirlande...", "***{}*** a quitté la fête.",
                               "***{}*** a fait une overdose de sucre d'orge.",
                               "***{}*** est parti voir au Pôle nord le père Noël.",
                               "***{}*** n'avait de toute évidence pas l'esprit de Noël...",
                               "***{}*** n'a pas cru au père Noël et s'en est allé.",
                               "Le cadeau de ***{}*** ne lui allait pas, il est parti le vendre.",
                               "***{}*** fêtera Noël tout seul cette année...",
                               "***{}*** est parti chercher son costume de père Noël... non ?",
                               "***{}*** a fait une gastro suite à l'overdose de chocolat causé par son "
                               "calendrier de l'Avent."]

# FONCTIONS GLOBALES --------------------------------

    def save(self, spe: bool = False) -> bool:
        self.app.save()
        if spe: return True
        fileIO("data/prism/global.json", "save", self.glb)
        fileIO("data/prism/sys.json", "save", self.sys)
        return True

    def get_glb(self) -> dict:
        today = time.strftime("%d/%m/%Y", time.localtime())
        heure = time.strftime("%H", time.localtime())
        if today not in self.glb:
            self.glb[today] = {"MSG_PART": 0,
                               "MSG_REEL": 0,
                               "JOIN": 0,
                               "RETURN": 0,
                               "QUIT": 0,
                               "BAN": 0,
                               "EMOJIS": {},
                               "REACTIONS": {},
                               "SUIVI_CHANNELS": {},
                               "HORAIRE_ECRIT": {}}
        if heure not in self.glb[today]["HORAIRE_ECRIT"]:
            self.glb[today]["HORAIRE_ECRIT"][heure] = 0
        self.save()
        return self.glb[today]

# PERSONNEL -----------------------------------------

    @commands.group(name="card", aliases=["c"], pass_context=True, invoke_without_command=True)
    async def prism_card(self, ctx, user: discord.Member = None):
        """Ensemble de commandes relatives à la Carte de Membre fournie par le système PRISM

        Par défaut, renvoie la carte de membre de l'utilisateur visé (ou soi-même)"""
        if ctx.invoked_subcommand is None:
            if not user:
                user = ctx.message.author
            await ctx.invoke(self.show, user=user)

    @prism_card.command(pass_context=True)
    async def show(self, ctx, user: discord.Member = None):
        """Affiche la carte de membre d'un utilisateur ou de soi-même le cas écheant"""
        if not user: user = ctx.message.author
        today = time.strftime("%d/%m/%Y", time.localtime())
        data = self.app.get_infos(user, himself=True if user == ctx.message.author else False)
        p = self.app.open(user)
        em = discord.Embed(title=data.formatname, description=data.bio, color=data.statuscolor)
        em.set_thumbnail(url=user.avatar_url if user.avatar_url else self.app.prism_avatar())
        em.add_field(name="Identifiants", value="**ID:** {}\n**SID:** {}".format(user.id, data.sid))
        em.add_field(name="Dates", value="**Création:** {} (**{}** jours)\n"
                                         "**Arrivée:** {} (**{}** jours)".format(data.date_creation,
                                                                                 data.creation,
                                                                                 data.date_depuis, data.depuis))
        em.add_field(name="Rôles", value="***{}***\n\n{}".format(data.roles if data.roles else "***Aucun***",
                                                                 self.app.rolebarre(user)))
        psd = data.liste_pseudos[-3:] if data.liste_pseudos != "?" else []
        psd.reverse()
        srn = data.liste_surnoms[-3:] if data.liste_surnoms != "?" else []
        srn.reverse()
        top = self.app.top_emote_perso(user, 3)
        if top:
            clt = []
            for t in top:
                clt.append("{} ({})".format(t[0], t[1]))
            emo = "\n**Emojis fav.** *{}*".format("; ".join(clt))
        else:
            emo = ""
        timestamp = (datetime.datetime.now() - user.joined_at).days
        jours = self.app.since(user, "jour") if self.app.since(user, "jour") > timestamp else timestamp
        ecr = round(p["DATA"]["MSG_PART"] / jours, 2)
        em.add_field(name="Stats", value="**{}** msg/jour{}".format(ecr, emo))
        em.add_field(name="Anciennement",
                     value="**Pseudos:** {}\n**Surnoms:** {}".format(", ".join(psd) if psd else "Aucun",
                                                                     ", ".join(srn) if srn else "Aucun"))
        txt = ""
        if data.past:
            b = data.past[-3:]
            b.reverse()
            for e in b:
                if e[1] == today:
                    txt += "**{}** - *{}*\n".format(e[0], e[2])
                else:
                    txt += "**{}** - *{}*\n".format(e[1], e[2])
        else:
            txt = "Aucune action"
        em.add_field(name="Historique", value=txt)
        em.set_footer(text="Rang {} {}{}".format(data.rang, data.qualif,
                                                 " | Joue à {}".format(user.game) if user.game else ""),
                      icon_url=data.rangimg)
        await self.bot.say(embed=em)

    @prism_card.command(pass_context=True)
    async def bio(self, ctx, *texte):
        """Modifier sa bio sur sa carte (En-tête)

        Laisser le texte vide enlevera le message par défaut"""
        u = self.app.open(ctx.message.author, "SYS")
        u["BIO"] = " ".join(texte)
        await self.bot.say("**Succès** | Votre bio s'affichera en haut de votre carte de membre")
        self.app.add_past(ctx.message.author, "Changement de bio")
        self.save(True)

    @prism_card.command(pass_context=True)
    async def jeux(self, ctx, user: discord.Member = None):
        """Affiche les jeux possédés par le membre"""
        if not user: user = ctx.message.author
        txt = add = ""
        lib = self.app.library(user)
        if not lib:
            await self.bot.say("**Bibliothèque vide** | Aucun jeu vérifié n'est possédé par l'utilisateur")
            return
        for e in lib:
            if len(txt) < 1960:
                txt += "`{}`\n".format(e[0])
            else:
                txt += "**...**"
        em = discord.Embed(title="Bibliothèque de {}".format(
            user.name) if user == ctx.message.author else "Votre bibliothèque", description=txt)
        em.set_footer(text="Du plus au moins joué | Certains jeux peuvent ne pas avoir été détectés")
        await self.bot.say(embed=em)

# TRIGGERS ----------------------------------------------

    async def prism_msg(self, message):
        if not message.server:
            return
        glb = self.get_glb()
        heure = time.strftime("%H", time.localtime())
        author = message.author
        channel = message.channel
        server = message.server
        p = self.app.open(author)
        p["DATA"]["MSG_REEL"] += 1
        p["DATA"]["MSG_PART"] += 1
        glb["MSG_PART"] += 1
        glb["MSG_REEL"] += 1
        glb["SUIVI_CHANNELS"][channel.id] = glb["SUIVI_CHANNELS"][channel.id] + 1 if channel.id in glb[
            "SUIVI_CHANNELS"] else 1
        glb["HORAIRE_ECRIT"][heure] += 1
        if ":" in message.content:
            output = re.compile(':(.*?):', re.DOTALL | re.IGNORECASE).findall(message.content)
            if output:
                for i in output:
                    if i in [e.name for e in server.emojis]:
                        glb["EMOJIS"][i] = glb["EMOJIS"][i] + 1 if i in glb["EMOJIS"] else 1
                        p["DATA"]["EMOJIS"][i] = p["DATA"]["EMOJIS"][i] + 1 if i in p["DATA"]["EMOJIS"] else 1
        self.save()

    async def prism_msgdel(self, message):
        if not message.server:
            return
        glb = self.get_glb()
        author = message.author
        channel = message.channel
        p = self.app.open(author)
        p["DATA"]["MSG_REEL"] -= 1
        glb["MSG_REEL"] -= 1
        self.save()

    async def prism_react(self, reaction, author):
        message = reaction.message
        if not message.server:
            return
        server = message.server
        glb = self.get_glb()
        p = self.app.open(author)
        if type(reaction.emoji) is str:
            name = reaction.emoji
        else:
            name = reaction.emoji.name
        if name in [e.name for e in server.emojis]:
            glb["REACTIONS"][name] = glb["REACTIONS"][name] + 1 if name in glb["REACTIONS"] else 1
            p["DATA"]["EMOJIS"][name] = p["DATA"]["EMOJIS"][name] + 1 if name in p["DATA"]["EMOJIS"] else 1
        self.save()

    async def prism_join(self, user: discord.Member):
        glb = self.get_glb()
        p = self.app.open(user, "DATA")
        p["JOIN"] += 1
        glb["JOIN"] += 1
        if p["QUIT"] > 0:
            self.app.add_past(user, "Retour sur le serveur")
            glb["RETURN"] += 1
        else:
            self.app.add_past(user, "Arrivée sur le serveur")
        self.save()

    async def prism_quit(self, user: discord.Member):
        glb = self.get_glb()
        p = self.app.open(user)
        p["DATA"]["QUIT"] += 1
        p["SYS"]["QUIT_SAVE"] = [r.name for r in user.roles]
        glb["QUIT"] += 1
        self.app.add_past(user, "Quitte le serveur")
        self.save()
        msgchannel = self.bot.get_channel("204585334925819904")  # HALL
        quitmsg = self.quit_msg if not self.quit_msg_event else self.quit_msg_event
        await self.bot.send_message(msgchannel, "**>** " + random.choice(quitmsg).format(user.name))

    async def prism_perso(self, before, after):
        p = self.app.open(after, "DATA")
        if after.name != before.name:
            p["PSEUDOS"].append(after.name)
            self.app.add_past(after, "Changement de pseudo pour *{}*".format(after.name))
        if after.display_name != before.display_name:
            if after.display_name == after.name:
                self.app.add_past(after, "Surnom retiré")
            else:
                p["SURNOMS"].append(after.display_name)
                self.app.add_past(after, "Changement du surnom pour *{}*".format(after.display_name))
        if after.avatar_url != before.avatar_url:
            url = before.avatar_url
            url = url.split("?")[0] # On retire le reformatage serveur Discord
            self.app.add_past(after, "Changement d'avatar ([Ancien]({}))".format(url))
        if after.top_role != before.top_role:
            if after.top_role.name is "Prison" and before.top_role.name != "Prison":
                self.app.add_past(after, "Entrée en prison")
            elif before.top_role.name is "Prison" and after.top_role.name != "Prison":
                self.app.add_past(after, "Sortie de prison")
            elif before.top_role.name != "Prison" and after.top_role.name != "Prison":
                if after.top_role > before.top_role:
                    self.app.add_past(after, "A reçu le rôle {}".format(after.top_role.name))
                else:
                    self.app.add_past(after, "A été rétrogradé {}".format(after.top_role.name))
            else:
                pass
        p = self.app.open(after, "JEUX")
        if after.game:
            if after.game.name:
                if after.game.name.lower() not in p:
                    p[after.game.name.lower()] = 0
                p[after.game.name.lower()] += 1
        self.save()

    async def prism_ban(self, user):
        p = self.app.open(user)
        glb = self.get_glb()
        p["DATA"]["QUIT"] += 1
        p["DATA"]["BAN"] += 1
        p["SYS"]["QUIT_SAVE"] = [r.name for r in user.roles]
        glb["BAN"] += 1
        self.app.add_past(user, "Banni du serveur")
        self.save()

def check_folders():
    if not os.path.exists("data/prism"):
        print("Creation du dossier PRISM...")
        os.makedirs("data/prism")


def check_files():
    if not os.path.isfile("data/prism/data.json"):
        print("Création et import de PRISM/data")
        fileIO("data/prism/data.json", "save", {})
    if not os.path.isfile("data/prism/global.json"):
        print("Création et import de PRISM/global")
        fileIO("data/prism/global.json", "save", {})
    if not os.path.isfile("data/prism/sys.json"):
        print("Création et import de PRISM/sys")
        fileIO("data/prism/sys.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Prism(bot)
    bot.add_listener(n.prism_msg, "on_message")
    bot.add_listener(n.prism_msgdel, "on_message_delete")
    bot.add_listener(n.prism_react, "on_reaction_add")
    bot.add_listener(n.prism_join, "on_member_join")
    bot.add_listener(n.prism_quit, "on_member_remove")
    bot.add_listener(n.prism_perso, "on_member_update")
    bot.add_listener(n.prism_ban, "on_member_ban")
    # TODO: bot.add_listener(n.prism_voice, "on_voice_state_update") -- DIFFICILE
    bot.add_cog(n)