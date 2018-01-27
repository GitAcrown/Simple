# Version Light
import asyncio
import datetime
import operator
import os
import random
import re
import string
import time

import discord
from discord.ext import commands

from .utils import checks
from .utils.dataIO import dataIO, fileIO


class PRISMApp:
    """API PRISM | Version Light"""

    def __init__(self, bot, path):
        self.bot = bot
        self.data = dataIO.load_json(path)
        self.old = dataIO.load_json("data/squid/data.json")
        self.update()

    def save(self):
        fileIO("data/prism/data.json", "save", self.data)
        return True

    def open(self, user: discord.Member, category: str = None):
        """Retourne un dict contenant toutes les informations du membre"""
        if user.id not in self.data:
            c = "//" + str(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in
                                   range(4)))
            self.data[user.id] = {"SID": c, "ORIGINE": time.time(), "ECO": {},
                                  "DATA": {"PSEUDOS": [], "SURNOMS": [], "MSG_REEL": 0, "MSG_PART": 0},
                                  "SYS": {}, "PAST": [], "JEUX": {}}
            self.update(user)
            if user.id in self.old:
                self.data[user.id]["SID"] = self.old[user.id]["SID"]
                self.data[user.id]["SYS"]["BIO"] = self.old[user.id]["BIO"]
                self.data[user.id]["DATA"]["PSEUDOS"] = self.old[user.id]["PSEUDOS"]
                self.data[user.id]["DATA"]["SURNOMS"] = self.old[user.id]["SURNOMS"]
                self.data[user.id]["DATA"]["MSG_REEL"] = self.old[user.id]["DATA"]["MSG_REEL"]
                self.data[user.id]["DATA"]["MSG_PART"] = self.old[user.id]["DATA"]["MSG_PART"]
        return self.data[user.id][category] if category else self.data[user.id]

    def update(self, user: discord.Member = None):
        tree = {"DATA": {"PSEUDOS": [user.name] if user else [],
                         "SURNOMS": [user.display_name] if user else [],
                         "MSG_PART": 0,
                         "MSG_REEL": 0,
                         "JOIN": 0,
                         "QUIT": 0,
                         "BAN": 0,
                         "EMOJIS": {},
                         "MOTS_REEL": 0,
                         "MOTS_PART": 0,
                         "LETTRES_REEL": 0,
                         "LETTRES_PART": 0},
                "SYS": {"BIO": None,
                        "QUIT_SAVE": [],
                        "D_VU": None,
                        "SEXE": "neutre",
                        "LIMITE_GRADE": None,
                        "BADGES": {}},
                "ECO": {"SOLDE": 0}}
        for e in tree:
            for i in tree[e]:
                if user:
                    if i not in self.data[user.id][e]:
                        self.data[user.id][e][i] = tree[e][i]
                else:
                    for u in self.data:
                        if i not in self.data[u][e]:
                            self.data[u][e][i] = tree[e][i]
        return True

    def add_past(self, user: discord.Member, event: str):
        p = self.open(user)
        jour = time.strftime("%d/%m/%Y", time.localtime())
        heure = time.strftime("%H:%M", time.localtime())
        p["PAST"].append([heure, jour, event])
        return True

    def jeux_verif(self):
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

    def grade(self, user: discord.Member):
        data = self.open(user)
        roles = [r.name for r in user.roles]
        msg = data["DATA"]["MSG_REEL"]
        sexe = data["SYS"]["SEXE"]
        limite = data["SYS"]["LIMITE_GRADE"] if data["SYS"]["LIMITE_GRADE"] else 3
        cond = {"ROLES": 1,
                "RANG": 1}
        if "Oldfag" in roles:
            cond["ROLES"] = 2
        if "Malsain" in roles or "Modérateur" in roles or "Administrateur" in roles:
            cond["ROLES"] = 3
        if 10000 <= msg <= 30000:
            cond["RANG"] = 2
        elif 30000 < msg:
            cond["RANG"] = 3
        if cond["ROLES"] >= cond["RANG"]:
            nb = cond["ROLES"]
        else:
            nb = cond["RANG"]
        nom = ""
        if nb >= limite:
            nb = limite
        if nb == 2:
            if sexe == "masculin":
                nom = "Résident"
            elif sexe == "feminin":
                nom = "Résidente"
            else:
                nom = "Résident·e"
            return [nom, "https://i.imgur.com/0krtchP.png", 2]
        elif nb == 3:
            if sexe == "masculin":
                nom = "Citoyen"
            elif sexe == "feminin":
                nom = "Citoyenne"
            else:
                nom = "Citoyen·ne"
            return [nom, "https://i.imgur.com/O9slR25.png", 3]
        else:
            if sexe == "masculin":
                nom = "Migrant"
            elif sexe == "feminin":
                nom = "Migrante"
            else:
                nom = "Migrant·e"
            return [nom, "https://i.imgur.com/6NB1e33.png", 1]


class Prism:  # MODULE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """PRISM | Système aggréateur de données et services spécialisés & personnalisés (Version light)"""

    def __init__(self, bot):
        self.bot = bot
        self.app = PRISMApp(bot, "data/prism/data.json")  # API\\PRISM
        self.glb = dataIO.load_json("data/prism/global.json")
        self.cycle_task = bot.loop.create_task(self.loop())
        self.quit_msg = ["Au revoir {} !", "Bye bye {}.", "{} s'est trompé de bouton.",
                         "{} a été suicidé de deux bans dans le dos.", "{} a ragequit le serveur.",
                         "GAME OVER {}", "A jamais {} !", "Les meilleurs partent en premier, sauf {}...",
                         "{} est parti, un de moins !", "{} s'envole vers d'autres cieux !", "YOU DIED {}",
                         "De toute évidence {} ne faisait pas parti de l'élite.", "{} a sauté d'un trottoir.",
                         "{} a roulé jusqu'en bas de la falaise.", "{} est parti ouvrir son propre serveur...",
                         "{} n'était de toute évidence pas assez *chill* pour ce serveur.",
                         "{} a été supprimé par le lobby LGBTQ+.", "{} a été neutralisé par le lobby e-estonien.",
                         "{}... désolé c'est qui ce random ?", "On m'annonce à l'oreillette que {} est parti.",
                         "C'est la fin pour {}...", "{} est parti faire caca chez Paul.",
                         "{} a été jeté dans la fosse aux randoms.", "{} est parti rejoindre Johnny...",
                         "{} est parti suite à une rupture de stock de biscuits *Belvita*",
                         "{} ne supportait plus d'être l'*Omega* du serveur.", "{} a paniqué une fois de plus.",
                         "{}, itsbhuge mostaje", "{} s'est *enfin* barré !", "Plus besoin de le bloquer, {} est parti !",
                         "Boop bip boup {} bip", "{} a pris sa retraite.",
                         "{} a disparu dans des circonstances encore incertaines...", "Non pas toi {} ! 😢",
                         "{} a quitté. Un de plus ou un de moins hein...",
                         "{} était de toute évidence trop underground pour ce serveur de normies.",
                         "{} a refusé de *checker ses privilèges* et en a payé le prix.",
                         "{} est parti. C'est tellement triste j'en ai recraché mes céréales.",
                         "{} a quitté/20", "{} est parti voir le serveur adulte.", "Ce n'est qu'un *au revoir* {} !"]

    async def loop(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(6)  # Temps de mise en route
            n = 1
            while True:
                self.app.save()
                fileIO("data/prism/global.json", "save", self.glb)
                await asyncio.sleep(300)
                print("MAJ PRISM #{} réalisée avec succès".format(n))
                n += 1
        except asyncio.CancelledError:
            pass

    def get_glb(self, server: discord.Server):
        date = time.strftime("%d/%m/%Y", time.localtime())
        heure = time.strftime("%H", time.localtime())
        if server.id not in self.glb:
            self.glb[server.id] = {}
        if date not in self.glb[server.id]:
            self.glb[server.id][date] = {}
        if heure not in self.glb[server.id][date]:
            self.glb[server.id][date][heure] = {"CHANNELS": {},
                                                "JOIN": 0,
                                                "RETURN": 0,
                                                "QUIT": 0,
                                                "BAN": 0,
                                                "BOT_MSG": 0,
                                                "EMOJIS": {}}
        return self.glb[server.id][date][heure]

    def color_status(self, user: discord.Member):
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
            return 0x2e6cc9  # Bleu

    def fake_avatar(self):
        l = ["https://i.imgur.com/oy3rtxW.png", "https://i.imgur.com/1HBokTM.png", "https://i.imgur.com/oFux3JS.png",
             "https://i.imgur.com/yltqljv.png", "https://i.imgur.com/SN2E0Kc.png"]
        return random.choice(l)

    def since(self, user: discord.Member, format=None):
        origine = self.app.open(user)["ORIGINE"]
        origine = datetime.datetime.fromtimestamp(origine)
        s = (datetime.datetime.now() - origine).seconds
        if s < 86401: s = 86401
        sm = s / 60  # en minutes
        if format == "minute": return sm
        sh = sm / 60  # en heures
        if format == "heure": return sh
        sj = sh / 24  # en jours
        if format == "jour": return sj
        sa = sj / 364.25  # en années
        if format == "annee": return sa
        return s

    def top_emote_perso(self, user: discord.Member, top: int = 3):
        p = self.app.open(user, "DATA")
        if p["EMOJIS"]:
            liste = [[r, p["EMOJIS"][r]] for r in p["EMOJIS"]]
            liste = sorted(liste, key=operator.itemgetter(1), reverse=True)
            nl = liste[:top]
            return nl
        return []

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

    def qualif(self, jours: int, msg: int):
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

    def rolebarre(self, member) -> str or bool:
        """Génère un STR de la barre de progression jusqu'au prochain rôle (Hab. ou Old.)"""

        def u_bar(prc) -> str:
            ch1 = "░"
            ch2 = "▒"
            ch3 = "█"
            nb = int(prc / 10)
            bar = ""
            if prc > 100:
                return u_bar(100)
            while len(bar) < nb:
                bar += ch3
            if len(bar) < 10:
                bar += ch2
            while len(bar) < 10:
                bar += ch1
            return bar

        hab = 14
        old = 120
        days = (datetime.datetime.now() - member.joined_at).days
        roles = [r.name for r in member.roles]
        if "Habitué" and "Oldfag" in roles:
            return ""
        elif "Habitué" in roles and "Oldfag" not in roles:
            n = (days / old) * 100
            if n > 100:
                n = 100
            barre = "`{} {}%`".format(u_bar(n), int(n))
            return "-> **Oldfag**\n" + barre
        elif "Oldfag" in roles and "Habitué" not in roles:
            n = (days / hab) * 100
            if n > 100:
                n = 100
            barre = "`{} {}%`".format(u_bar(n), int(n))
            return "-> **re-Habitué**\n" + barre
        elif "Oldfag" not in roles and "Habitué" not in roles:
            n = (days / hab) * 100
            if n > 100:
                n = 100
            barre = "`{} {}%`".format(u_bar(n), int(n))
            return "-> **Habitué**\n" + barre
        else:
            return ""

    def day_stats_num(self, server: discord.Server, date: str, cat: str):
        val = 0
        cat = cat.upper()
        if server.id in self.glb:
            if date in self.glb[server.id]:
                for h in self.glb[server.id][date]:
                    if cat in self.glb[server.id][date][h]:
                        val += self.glb[server.id][date][h][cat]
                return val
            else:
                return 0
        else:
            return False

    def day_stats_dict(self, server: discord.Server, date: str, cat: str):
        data = {}
        cat = cat.upper()
        if server.id in self.glb:
            if date in self.glb[server.id]:
                for h in self.glb[server.id][date]:
                    for e in self.glb[server.id][date][h][cat]:
                        if e not in data:
                            data[e] = self.glb[server.id][date][h][cat][e]
                        else:
                            data[e] += self.glb[server.id][date][h][cat][e]
                return data
            else:
                return data
        else:
            return False

    def botmsg_count(self, server: discord.Server):
        count = 0
        for member in server.members:
            if member.bot:
                count += self.app.open(member, "DATA")["MSG_PART"]
        return count

    # COMMANDES +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    @commands.group(name="card", aliases=["c"], pass_context=True, invoke_without_command=True, no_pm=True)
    async def prism_card(self, ctx, user: discord.Member = None):
        """Ensemble de commandes relatives à la Carte de Membre fournie par le système PRISM

        Par défaut, renvoie la carte de membre de l'utilisateur visé (ou soi-même)"""
        if ctx.invoked_subcommand is None:
            if not user:
                user = ctx.message.author
            await ctx.invoke(self.show, user=user)

    @prism_card.command(pass_context=True)
    async def beta(self, ctx, user: discord.Member = None):
        """Affiche la carte de membre d'un utilisateur (Nouvelle version)"""
        if not user:
            user = ctx.message.author
        page = "home"
        menu = None
        while True:
            await asyncio.sleep(1)
            today = time.strftime("%d/%m/%Y", time.localtime())
            timestamp = datetime.datetime.now()
            data = self.app.open(user)
            roles = []
            formatname = user.name if user.display_name == user.name else "{} «{}»".format(user.name, user.display_name)
            for r in user.roles:
                if r.name != "@everyone":
                    if r.mentionable:
                        roles.append(r.mention)
                    else:
                        roles.append("*" + r.name + "*")
            if page == "home":
                em = discord.Embed(title=formatname, description=data["SYS"]["BIO"], color=self.color_status(user))
                em.set_thumbnail(url=user.avatar_url if user.avatar_url else self.fake_avatar())
                emolist = ["📊", "⏱", "🏅"]
                creation = (timestamp - user.created_at).days
                datecreation = user.created_at.strftime("%d/%m/%Y")
                arrive = (timestamp - user.joined_at).days
                datearrive = user.joined_at.strftime("%d/%m/%Y")
                origine = datetime.datetime.fromtimestamp(data["ORIGINE"])
                since_origine = (timestamp - origine).days
                strorigine = datetime.datetime.strftime(origine, "%d/%m/%Y %H:%M")
                dmsg = data["SYS"]["D_VU"]
                ptxt = "**ID** `{}`\n".format(user.id)
                ptxt += "**Rôles** {}\n".format(" ,".join(roles) if roles else "Aucun")
                ptxt += "**Création** `{}` (**{}**j)\n".format(datecreation, creation)
                ptxt += "**Arrivée** `{}` (**{}**j)\n".format(datearrive, arrive)
                ptxt += "**Apparition** `{}` (**{}**j)\n".format(strorigine, since_origine)
                ptxt += "**Dernier msg** `{}\n`".format(dmsg)
                ptxt += "\n"
                if user.voice_channel:
                    ptxt += "- **En vocal sur *{}***\n".format(user.voice_channel.name)
                if user.top_role.name == "Prison":
                    ptxt += "- **En prison**\n"
                if user.game:
                    if user.game.name:
                        ptxt += "- **Joue à *{}***\n".format(user.game.name)
                em.add_field(name="Données", value=ptxt)

                pseudoslist = data["DATA"]["PSEUDOS"] if data["DATA"]["PSEUDOS"] else "?"
                surnomslist = data["DATA"]["SURNOMS"] if data["DATA"]["SURNOMS"] else "?"
                psd = pseudoslist[-3:] if pseudoslist != "?" else []
                psd.reverse()
                srn = surnomslist[-3:] if surnomslist != "?" else []
                srn.reverse()
                em.add_field(name="Anciennement", value="**Pseudos** {}\n**Surnoms** {}".format(
                    ", ".join(psd) if psd else "Aucun", ", ".join(srn) if srn else "Aucun"))

            elif page == "stats":
                em = discord.Embed(title=formatname, description=data["SYS"]["BIO"], color=self.color_status(user))
                em.set_thumbnail(url=user.avatar_url if user.avatar_url else self.fake_avatar())
                origine = datetime.datetime.fromtimestamp(data["ORIGINE"])
                jours = (timestamp - origine).days
                statstxt = ""
                emolist = ["👤", "⏱", "🏅"]
                msgjour = round(data["DATA"]["MSG_PART"] / jours, 2)
                statstxt += "**{}** msg/jour\n".format(msgjour)
                motsmsg = round(data["DATA"]["MOTS_PART"] / data["DATA"]["MSG_PART"], 2)
                statstxt += "**{}** mots/msg\n".format(motsmsg)
                ltrmsg = round(data["DATA"]["LETTRES_PART"] / data["DATA"]["MSG_PART"], 2)
                statstxt += "**{}** lettres/msg\n".format(ltrmsg)
                top = self.top_emote_perso(user, 5)
                if top:
                    clt = []
                    for t in top:
                        clt.append("{} - *{}*".format(t[0], t[1]))
                    statstxt += "**Emojis favoris**\n{}\n".format("\n".join(clt))
                em.add_field(name="Stats", value=statstxt)

            elif page == "hist":
                em = discord.Embed(title=formatname, description=data["SYS"]["BIO"], color=self.color_status(user))
                em.set_thumbnail(url=user.avatar_url if user.avatar_url else self.fake_avatar())
                txt = ""
                emolist = ["👤", "📊", "🏅"]
                if data["PAST"]:
                    b = data["PAST"][-5:]
                    b.reverse()
                    for e in b:
                        if e[1] == today:
                            txt += "**{}** - {}\n".format(e[0], e[2])
                        else:
                            txt += "**{}** - {}\n".format(e[1], e[2])
                else:
                    txt = "Aucune action"
                em.add_field(name="Historique", value=txt)

            elif page == "badges":
                em = discord.Embed(title=formatname, description=data["SYS"]["BIO"], color=self.color_status(user))
                em.set_thumbnail(url=user.avatar_url if user.avatar_url else self.fake_avatar())
                txt = ""
                emolist = ["👤", "📊", "⏱"]
                if data["SYS"]["BADGES"]:
                    lb = [[b["DATE"], b["NOM"], b["DESC"]] for b in data["SYS"]["BADGES"]]
                    lb = sorted(lb, key=operator.itemgetter(0), reverse=True)
                    for e in lb[-5:]:
                        txt += "**{}** - *{}*\n".format(e[1], e[2])
                else:
                    txt = "**Aucun succès** (Non disponibles)"
                em.add_field(name="Succès", value=txt)

            em.set_footer(text="{} | Utilisez les réactions pour naviguer".format(self.app.grade(user)[0]),
                          icon_url=self.app.grade(user)[1])
            if menu is None:
                menu = await self.bot.say(embed=em)
            else:
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                menu = await self.bot.edit_message(menu, embed=em)

            for e in emolist:
                await self.bot.add_reaction(menu, e)
            act = await self.bot.wait_for_reaction(emolist, message=menu, timeout=60,
                                                   check=self.check)
            if act is None:
                em.set_footer(text="{} | Session expirée".format(self.app.grade(user)[0]),
                              icon_url=self.app.grade(user)[1])
                await self.bot.edit_message(menu, embed=em)
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                return
            elif act.reaction.emoji == "👤":
                page = "home"
            elif act.reaction.emoji == "📊":
                page = "stats"
            elif act.reaction.emoji == "⏱":
                page = "hist"
            elif act.reaction.emoji == "🏅":
                page = "badges"
            else:
                em.set_footer(text="{} | Page indisponible".format(self.app.grade(user)[0]),
                              icon_url=self.app.grade(user)[1])
                await self.bot.edit_message(menu, embed=em)
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                continue

    @prism_card.command(pass_context=True)
    async def show(self, ctx, user: discord.Member = None):
        """Affiche la carte de membre (Ancienne version) d'un utilisateur ou de soi-même le cas écheant"""
        if not user:
            user = ctx.message.author
        today = time.strftime("%d/%m/%Y", time.localtime())
        timestamp = datetime.datetime.now()
        data = self.app.open(user)
        formatname = user.name if user.display_name == user.name else "{} «{}»".format(user.name, user.display_name)
        em = discord.Embed(title=formatname, description=data["SYS"]["BIO"], color=self.color_status(user))
        em.set_thumbnail(url=user.avatar_url if user.avatar_url else self.fake_avatar())
        em.add_field(name="Données", value="**ID:** {}\n**SID:** {}\n**Solde:** {}*BK*".format(user.id, data["SID"],
                                                                                               data["ECO"]["SOLDE"]))
        creation = (timestamp - user.created_at).days
        datecreation = user.created_at.strftime("%d/%m/%Y")
        arrive = (timestamp - user.joined_at).days
        datearrive = user.joined_at.strftime("%d/%m/%Y")
        origine = datetime.datetime.fromtimestamp(data["ORIGINE"])
        since_origine = (timestamp - origine).days
        strorigine = datetime.datetime.strftime(origine, "%d/%m/%Y %H:%M")
        dmsg = data["SYS"]["D_VU"]
        em.add_field(name="Dates", value="**Création:** {} (**{}**j)\n"
                                         "**Arrivée:** {} (**{}**j)\n"
                                         "**Enregistrement:** {} (**{}**j)\n"
                                         "**Dernier msg:** {}".format(datecreation, creation, datearrive, arrive,
                                                                      strorigine, since_origine, dmsg))
        roles = []
        for r in user.roles:
            if r.name != "@everyone":
                if r.mentionable:
                    roles.append(r.mention)
                else:
                    roles.append("*" + r.name + "*")
        em.add_field(name="Rôles", value="{}\n\n{}".format(", ".join(roles) if roles else "**Aucun**", self.rolebarre(user)))
        pseudoslist = data["DATA"]["PSEUDOS"] if data["DATA"]["PSEUDOS"] else "?"
        surnomslist = data["DATA"]["SURNOMS"] if data["DATA"]["SURNOMS"] else "?"
        psd = pseudoslist[-3:] if pseudoslist != "?" else []
        psd.reverse()
        srn = surnomslist[-3:] if surnomslist != "?" else []
        srn.reverse()
        statstxt = ""
        jours = since_origine
        msgjour = round(data["DATA"]["MSG_PART"] / jours, 2)
        statstxt += "**{}** msg/jour\n".format(msgjour)
        motsmsg = round(data["DATA"]["MOTS_PART"] / data["DATA"]["MSG_PART"], 2)
        statstxt += "**{}** mots/msg\n".format(motsmsg)
        ltrmsg = round(data["DATA"]["LETTRES_PART"] / data["DATA"]["MSG_PART"], 2)
        statstxt += "**{}** lettres/msg\n".format(ltrmsg)
        top = self.top_emote_perso(user, 3)
        if top:
            clt = []
            for t in top:
                clt.append("**{}** (*{}*)".format(t[0], t[1]))
            statstxt += "**Emojis fav.:** {}\n".format("; ".join(clt))
        em.add_field(name="Stats", value=statstxt)
        em.add_field(name="Anciennement",
                     value="**Pseudos:** {}\n**Surnoms:** {}".format(", ".join(psd) if psd else "Aucun",
                                                                     ", ".join(srn) if srn else "Aucun"))
        txt = ""
        if data["PAST"]:
            b = data["PAST"][-3:]
            b.reverse()
            for e in b:
                if e[1] == today:
                    txt += "**{}** - {}\n".format(e[0], e[2])
                else:
                    txt += "**{}** - {}\n".format(e[1], e[2])
        else:
            txt = "Aucune action"
        em.add_field(name="Historique", value=txt)
        em.set_footer(text="{}{}".format(self.app.grade(user)[0],
                                         " | Joue à {}".format(user.game) if user.game else ""),
                      icon_url=self.app.grade(user)[1])
        await self.bot.say(embed=em)

    @prism_card.command(pass_context=True)
    async def bio(self, ctx, *texte):
        """Modifier sa bio sur sa carte (En-tête)

        Laisser le texte vide enlevera le message par défaut"""
        u = self.app.open(ctx.message.author, "SYS")
        if texte:
            await self.bot.say("**Succès** | Votre bio s'affichera en haut de votre carte de membre")
        else:
            await self.bot.say("**Succès** | Votre bio n'affichera aucun message")
        self.app.add_past(ctx.message.author, "Changement de bio")
        u["BIO"] = " ".join(texte)

    @prism_card.command(pass_context=True)
    async def sexe(self, ctx, sexe: str):
        """Permet d'indiquer au bot son sexe, permettant d'adapter un certain nombre de fonctionnalités
        Reconnus : neutre, feminin/femme, masculin/homme"""
        data = self.app.open(ctx.message.author, "SYS")
        if sexe.lower() in ["neutre", "n"]:
            data["SEXE"] = "neutre"
            await self.bot.say("**Succès** | Vous serez désigné de manière la plus neutre possible")
        elif sexe.lower() in ["femme", "feminin", "f"]:
            data["SEXE"] = "feminin"
            await self.bot.say("**Succès** | Vous serez désignée comme une personne de sexe féminin")
        elif sexe.lower() in ["homme", "masculin", "h"]:
            data["SEXE"] = "masculin"
            await self.bot.say("**Succès** | Vous serez désigné comme une personne de sexe masculin")
        else:
            await self.bot.say("**Inconnu** | Je ne reconnais que 3 sexes: **Neutre**, **Feminin** et **Masculin**.\n"
                               "*Veillez à ne pas mettre d'accents !*")

    @prism_card.command(pass_context=True)
    async def extract(self, ctx, user: discord.Member = None):
        """Permet d'extraire les données personnelles d'un membre en fichier texte (.txt)

        Le fichier est préformaté pour son utilisation sur des fichiers de traitement de données"""
        if not user: user = ctx.message.author
        p = self.app.open(user)
        await self.bot.say("**Organisation des données** | Veuillez patienter pendant que je rassemble les données...")
        origine = datetime.datetime.fromtimestamp(p["ORIGINE"])
        strorigine = datetime.datetime.strftime(origine, "%d/%m/%Y %H:%M")
        today = datetime.datetime.strftime(ctx.message.timestamp, "%d%m%Y_%H%M")
        txt = ">>> Données de {} ({}) <<<\n".format(user.name, user.id)
        txt += "System IDentificator (SID)\t{}\n".format(p["SID"])
        txt += "Origine estimee\t{}\n".format(strorigine)
        txt += "Solde BitKheys\t{}\n".format(p["ECO"]["SOLDE"])
        txt += "Bio\t{}\n".format(p["SYS"]["BIO"])
        txt += "Grade\t{}\n".format(self.app.grade(user)[0])
        txt += "\n--- Stats ---\n"
        txt += "Nb msg reel\t{}\n".format(p["DATA"]["MSG_REEL"])
        txt += "Nb msg total\t{}\n".format(p["DATA"]["MSG_PART"])
        txt += "Nb mots reel\t{}\n".format(p["DATA"]["MOTS_REEL"])
        txt += "Nb mots total\t{}\n".format(p["DATA"]["MOTS_PART"])
        txt += "Nb lettres reel\t{}\n".format(p["DATA"]["LETTRES_REEL"])
        txt += "Nb lettres total\t{}\n".format(p["DATA"]["LETTRES_PART"])
        txt += "Nb d'arrivees\t{}\n".format(p["DATA"]["JOIN"])
        txt += "Nb bans\t{}\n".format(p["DATA"]["BAN"])
        txt += "Nb de departs\t{}\n".format(p["DATA"]["QUIT"])
        txt += "Pseudos\t{}\n".format(", ".join(p["DATA"]["PSEUDOS"]) if p["DATA"]["PSEUDOS"] else "Aucun changement")
        txt += "Surnoms\t{}\n".format(", ".join(p["DATA"]["SURNOMS"]) if p["DATA"]["SURNOMS"] else "Aucun changement")
        dispo = self.app.jeux_verif()
        jeux = [p["JEUX"][r] for r in p["JEUX"] if r in dispo]
        txt += "Jeux\t{}\n".format(", ".join(jeux) if jeux else "Aucun detecte")
        txt += "\n--- Emojis / Nb d'utilisations ---\n"
        order = [[r, p["DATA"]["EMOJIS"][r]] for r in p["DATA"]["EMOJIS"]]
        order = sorted(order, key=operator.itemgetter(1), reverse=True)
        for i in order:
            txt += "{}\t{}\n".format(i[0], i[1])
        txt += "\n--- Historique ---\n"
        for e in p["PAST"]:
            txt += "{} {}\t{}\n".format(e[0], e[1], e[2])

        filename = "PStats-{}-{}.txt".format(today, user.name)
        file = open("data/outils/{}".format(filename), "w", encoding="UTF-8")
        file.write(txt)
        file.close()
        await asyncio.sleep(2)
        await self.bot.say("**Upload en cours** | Ce processus peut être assez long si le fichier est volumineux")
        try:
            await self.bot.send_file(ctx.message.channel, "data/outils/{}".format(filename))
            os.remove("data/outils/{}".format(filename))
        except Exception as e:
            await self.bot.say("**Erreur dans l'Upload** | `{}`".format(e))

    @commands.command(aliases=["jeux", "j"], pass_context=True)
    async def biblio(self, ctx, user: discord.Member = None):
        """Affiche les jeux possédés par le membre"""
        if not user:
            user = ctx.message.author
        txt = ""
        p = self.app.open(user)
        dispo = self.app.jeux_verif()
        lib = []
        if p["JEUX"]:
            lib = [[r, p["JEUX"][r]] for r in p["JEUX"] if r in dispo]
            lib = sorted(lib, key=operator.itemgetter(1), reverse=True)
        if not lib:
            await self.bot.say("**Bibliothèque vide** | Aucun jeu vérifié n'est possédé par l'utilisateur")
            return
        for e in lib:
            if len(txt) < 1960:
                txt += "`{}`\n".format(e[0].capitalize())
            else:
                txt += "**...**"
        em = discord.Embed(title="Bibliothèque de {}".format(
            user.name) if user != ctx.message.author else "Votre bibliothèque", description=txt)
        em.set_footer(text="Du plus au moins joué | Certains jeux peuvent ne pas avoir été détectés")
        await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    @checks.admin_or_permissions(kick_members=True)
    async def limite(self, ctx, user: discord.Member, lim: int = 3):
        """Permet de limiter le grade du membre visé
        1 - Migrant(e) maximum
        2 - Résident(e) maximum
        3 - Aucune limitation"""
        data = self.app.open(user, "SYS")
        if lim == 1:
            data["LIMITE_GRADE"] = lim
            await self.bot.say("**Succès** | Le membre sera limité au grade *Migrant*")
        elif lim == 2:
            data["LIMITE_GRADE"] = lim
            await self.bot.say("**Succès** | Le membre sera limité au grade *Résident*")
        elif lim == 3:
            data["LIMITE_GRADE"] = None
            await self.bot.say("**Succès** | Le membre ne sera pas limité dans son grade")
        else:
            await self.bot.say("**Impossible** | La valeur doit être entre 1 et 3 (Voir `&help limite`)")

    @commands.group(name="global", aliases=["g"], pass_context=True, invoke_without_command=True, no_pm=True)
    async def prism_global(self, ctx):
        """Ensemble de commandes relatives aux données globales récoltées par PRISM

        Par défaut, renvoie un résumé des statistiques dans le temps"""
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.stats)

    def check(self, reaction, user):
        return not user.bot

    @prism_global.command(pass_context=True)
    async def stats(self, ctx):
        """Affiche un résumé clair des statistiques récoltées par PRISM"""
        server = ctx.message.server
        rewind = 0
        menu = None
        while True:
            msgtxt = msgact = msgemo = ""
            glb = self.glb[
                server.id]  # On prend l'ENSEMBLE des données du serveur, pas les actuelles comme self.get_glb()
            today = time.strftime("%d/%m/%Y", time.localtime())
            if rewind > 0:
                date = time.strftime("%d/%m/%Y",
                                     time.localtime(time.mktime(time.strptime(today, "%d/%m/%Y")) - (86400 * rewind)))
            elif rewind == -1:
                date = "now"
            else:
                date = today

            if date != "now":
                if date in glb:
                    em = discord.Embed(title="Données | **{}**".format(date if date != today else "Aujourd'hui"))
                    em.set_thumbnail(url=server.icon_url)

                    msgtxt = msgact = msgemo = ""

                    stats = self.day_stats_dict(server, date, "CHANNELS")
                    if stats:
                        stats = [[self.bot.get_channel(e), stats[e]] for e in stats]
                        stats = sorted(stats, key=operator.itemgetter(1), reverse=True)
                        total = 0
                        for nom, num in stats:
                            msgtxt += "**{}** {}\n".format(nom, num)
                            total += num
                        botmsg = self.day_stats_num(server, date, "BOT_MSG")
                        msgtxt += "- **Total** {}\n" \
                                  "- **Bots exclus** {}".format(total, (total - botmsg))
                        em.add_field(name="Messages", value=msgtxt)

                    data = {}
                    for h in glb[date]:
                        if h not in data:
                            data[h] = 0
                        for chan in glb[date][h]["CHANNELS"]:
                            data[h] += glb[date][h]["CHANNELS"][chan]
                    stats = [[h, data[h]] for h in data]
                    stats = sorted(stats, key=operator.itemgetter(1), reverse=True)[:5]
                    for heure, num in stats:
                        msgact += "**{}h** {}\n".format(heure, num)
                    em.add_field(name="Pics d'activité", value=msgact)

                    entree = self.day_stats_num(server, date, "JOIN")
                    revenants = self.day_stats_num(server, date, "RETURN")
                    sorties = self.day_stats_num(server, date, "QUIT")
                    bans = self.day_stats_num(server, date, "BAN")
                    solde = entree - sorties
                    msgmir = "**Entrées** {}\n" \
                             "**- dont revenants** {}\n" \
                             "**Sorties** {}\n" \
                             "**- dont bannis** {}\n" \
                             "**Solde** {}".format(entree, revenants, sorties, bans, solde)
                    em.add_field(name="Flux migratoire", value=msgmir)

                    stats = self.day_stats_dict(server, date, "EMOJIS")
                    if stats:
                        stats = [[e, stats[e]] for e in stats]
                        stats = sorted(stats, key=operator.itemgetter(1), reverse=True)[:5]
                        for nom, num in stats:
                            msgemo += "**{}** {}\n".format(nom, num)
                        em.add_field(name="Emojis populaires", value=msgemo)

                    em.set_footer(
                        text="Naviguez avec les réactions ci-dessous | Messages supprimés et réactions pris en compte")
                else:
                    em = discord.Embed(title="Données | **{}**".format(date if date != today else "Aujourd'hui"),
                                       description="Aucune donnée n'est disponible pour ce jour.")
                    em.set_thumbnail(url=server.icon_url)
                    em.set_footer(text="Naviguez avec les réactions ci-dessous")
            else:
                heure = time.strftime("%H", time.localtime())
                now = self.get_glb(server)
                msgtxt = msgact = msgemo = ""
                online = str(len([m.status for m in server.members if
                                  str(m.status) == "online" or str(m.status) == "idle" or str(m.status) == "dnd"]))
                total_users = str(len(server.members))
                passed = (ctx.message.timestamp - server.created_at).days
                presmsg = "**Nom** {}\n" \
                          "**ID** {}\n" \
                          "**Région** {}\n" \
                          "**Propriétaire** {}\n" \
                          "**Membres** {}/{}\n" \
                          "**Age** {}j".format(server.name, server.id, server.region, server.owner, online,
                                               total_users, passed)
                em = discord.Embed(title="Données | En direct ({}h)".format(heure), description=presmsg)
                em.set_thumbnail(url=server.icon_url)

                if now["CHANNELS"]:
                    stats = [[self.bot.get_channel(e), now["CHANNELS"][e]] for e in now["CHANNELS"]]
                    stats = sorted(stats, key=operator.itemgetter(1), reverse=True)
                    msgtxt = ""
                    total = 0
                    for nom, num in stats:
                        msgtxt += "**{}** {}\n".format(nom, num)
                        total += num
                    botmsg = now["BOT_MSG"] if "BOT_MSG" in now else 0
                    msgtxt += "- **Total** {}\n" \
                              "- **Bots exclus** {}".format(total, (total - botmsg))
                    em.add_field(name="Messages", value=msgtxt)

                entree = now["JOIN"]
                revenants = now["RETURN"]
                sorties = now["QUIT"]
                bans = now["BAN"]
                solde = entree - sorties
                msgmir = "**Entrées** {}\n" \
                         "**- dont revenants** {}\n" \
                         "**Sorties** {}\n" \
                         "**- dont bannis** {}\n" \
                         "**Solde** {}".format(entree, revenants, sorties, bans, solde)
                em.add_field(name="Flux migratoire", value=msgmir)

                if now["EMOJIS"]:
                    stats = [[e, now["EMOJIS"][e]] for e in now["EMOJIS"]]
                    stats = sorted(stats, key=operator.itemgetter(1), reverse=True)[:5]
                    msgemo = ""
                    for nom, num in stats:
                        msgemo += "**{}** {}\n".format(nom, num)
                    em.add_field(name="Emojis populaires", value=msgemo)

                em.set_footer(
                    text="Naviguez avec les réactions ci-dessous | Messages supprimés et réactions pris en compte")

            if menu is None:
                menu = await self.bot.say(embed=em)
            else:
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                menu = await self.bot.edit_message(menu, embed=em)
            emolist = ["⬅", "⏬", "⏺"]
            if rewind > -1:
                await self.bot.add_reaction(menu, "⬅")
                await self.bot.add_reaction(menu, "⏬")
                await self.bot.add_reaction(menu, "⏺")
                if rewind > 0:
                    await self.bot.add_reaction(menu, "➡")
                    emolist.append("➡")
            else:
                await self.bot.add_reaction(menu, "⏹")
                await self.bot.add_reaction(menu, "🔄")
                emolist = ["⏹", "🔄"]

            act = await self.bot.wait_for_reaction(emolist, message=menu, timeout=60,
                                                   check=self.check)
            if act is None:
                em.set_footer(text="-- Session expirée --")
                await self.bot.edit_message(menu, embed=em)
                try:
                    await self.bot.clear_reactions(menu)
                except:
                    pass
                return
            elif act.reaction.emoji == "⬅":
                rewind += 1
            elif act.reaction.emoji == "⏬":
                em.set_footer(text="Entrez la date désirée ci-dessous (dd/mm/aaaa)")
                await self.bot.edit_message(menu, embed=em)
                rep = await self.bot.wait_for_message(author=act.user, channel=menu.channel, timeout=30)
                if rep is None:
                    em.set_footer(text="TIMEOUT | Retour au menu...")
                    await self.bot.edit_message(menu, embed=em)
                    await asyncio.sleep(0.5)
                elif len(rep.content) == 10:
                    rewind += int((time.mktime(time.strptime(date, "%d/%m/%Y")) - time.mktime(
                        time.strptime(rep.content, "%d/%m/%Y"))) / 86400)
                    try:
                        await self.bot.delete_message(rep)
                    except:
                        pass
                    if rewind < 0:
                        rewind = 0
                        em.set_footer(text="Impossible d'aller dans le futur")
                        await self.bot.edit_message(menu, embed=em)
                        await asyncio.sleep(0.5)
                else:
                    em.set_footer(text="Invalide | Retour au menu...")
                    await self.bot.edit_message(menu, embed=em)
                    await asyncio.sleep(0.5)
            elif act.reaction.emoji == "➡":
                rewind -= 1
            elif act.reaction.emoji == "⏺":
                rewind = -1
            elif act.reaction.emoji == "🔄":
                continue
            elif act.reaction.emoji == "⏹":
                rewind = 0
            else:
                em.set_footer(text="Invalide !")
                await self.bot.edit_message(menu, embed=em)
                continue


            # TRIGGERS ----------------------------------------------

    async def prism_msg(self, message):
        if not hasattr(message, "server"):
            return
        date = time.strftime("Le %d/%m/%Y à %H:%M", time.localtime())
        author = message.author
        channel = message.channel
        server = message.server
        p = self.app.open(author)
        glb = self.get_glb(server)
        mots = len(message.content.split(" "))
        lettres = len(message.content)
        p["DATA"]["MSG_REEL"] += 1
        p["DATA"]["MSG_PART"] += 1
        p["DATA"]["MOTS_REEL"] += mots
        p["DATA"]["MOTS_PART"] += mots
        p["DATA"]["LETTRES_REEL"] += lettres
        p["DATA"]["LETTRES_PART"] += lettres
        p["SYS"]["D_VU"] = date
        glb["CHANNELS"][channel.id] = glb["CHANNELS"][channel.id] + 1 if channel.id in glb["CHANNELS"] else 1
        if author.bot:
            glb["BOT_MSG"] += 1
        if ":" in message.content:
            output = re.compile(':(.*?):', re.DOTALL | re.IGNORECASE).findall(message.content)
            if output:
                for i in output:
                    if i in [e.name for e in server.emojis]:
                        p["DATA"]["EMOJIS"][i] = p["DATA"]["EMOJIS"][i] + 1 if i in p["DATA"]["EMOJIS"] else 1
                        glb["EMOJIS"][i] = glb["EMOJIS"][i] + 1 if i in glb["EMOJIS"] else 1

    async def prism_msgdel(self, message):
        if not hasattr(message, "server"):
            return
        author = message.author
        p = self.app.open(author)
        mots = len(message.content.split(" "))
        lettres = len(message.content)
        p["DATA"]["MSG_REEL"] -= 1
        p["DATA"]["MOTS_REEL"] -= mots
        p["DATA"]["LETTRES_REEL"] -= lettres

    async def prism_react(self, reaction, author):
        message = reaction.message
        if not hasattr(message, "server"):
            return
        server = message.server
        p = self.app.open(author)
        glb = self.get_glb(server)
        if type(reaction.emoji) is str:
            name = reaction.emoji
        else:
            name = reaction.emoji.name
        if name in [e.name for e in server.emojis]:
            p["DATA"]["EMOJIS"][name] = p["DATA"]["EMOJIS"][name] + 1 if name in p["DATA"]["EMOJIS"] else 1
            glb["EMOJIS"][name] = glb["EMOJIS"][name] + 1 if name in glb["EMOJIS"] else 1

    async def prism_join(self, user: discord.Member):
        p = self.app.open(user, "DATA")
        server = user.server
        glb = self.get_glb(server)
        glb["JOIN"] += 1
        p["JOIN"] += 1
        if p["QUIT"] > 0:
            self.app.add_past(user, "Retour sur le serveur")
            glb["RETURN"] += 1
        else:
            self.app.add_past(user, "Arrivée sur le serveur")

    async def prism_quit(self, user: discord.Member):
        p = self.app.open(user)
        server = user.server
        glb = self.get_glb(server)
        glb["QUIT"] += 1
        p["DATA"]["QUIT"] += 1
        p["SYS"]["QUIT_SAVE"] = [r.name for r in user.roles]
        self.app.add_past(user, "Quitte le serveur")
        msgchannel = self.bot.get_channel("204585334925819904")  # HALL
        grade, img, nomb = self.app.grade(user)
        quitmsg = random.choice(self.quit_msg).format("<@" + str(user.id) + ">")
        em = discord.Embed(description="👋 - {}".format(quitmsg), color=user.color)
        bip = user.top_role.name if user.top_role.name != "@everyone" else "Aucun rôle"
        em.set_footer(text="{} | {}".format(user.display_name, bip), icon_url=img)
        await self.bot.send_message(msgchannel, embed=em)

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
            url = url.split("?")[0]  # On retire le reformatage serveur Discord
            self.app.add_past(after, "Changement d'avatar ([Ancien]({}))".format(url))
        if after.top_role != before.top_role:
            if after.top_role.name.startswith("nvoice"):
                return
            if after.top_role.name is "Prison" and before.top_role.name != "Prison":
                self.app.add_past(after, "Entrée en prison")
            elif before.top_role.name is "Prison" and after.top_role.name != "Prison":
                self.app.add_past(after, "Sortie de prison")
            elif before.top_role.name != "Prison" and after.top_role.name != "Prison":
                if after.top_role > before.top_role:
                    self.app.add_past(after, "A reçu le rôle {}".format(after.top_role.name))
                else:
                    if after.top_role.name != "@everyone":
                        self.app.add_past(after, "A été rétrogradé {}".format(after.top_role.name))
                    else:
                        self.app.add_past(after, "Ne possède plus de rôles")
            else:
                pass
        p = self.app.open(after, "JEUX")
        if after.game:
            if after.game.name:
                if after.game.name.lower() not in p:
                    p[after.game.name.lower()] = 0
                p[after.game.name.lower()] += 1

    async def prism_ban(self, user):
        p = self.app.open(user)
        server = user.server
        glb = self.get_glb(server)
        glb["BAN"] += 1
        p["DATA"]["QUIT"] += 1
        p["DATA"]["BAN"] += 1
        p["SYS"]["QUIT_SAVE"] = [r.name for r in user.roles]
        self.app.add_past(user, "Banni du serveur")

    def __unload(self):
        self.app.save()


def check_folders():
    if not os.path.exists("data/prism"):
        print("Creation du dossier PRISM...")
        os.makedirs("data/prism")


def check_files():
    if not os.path.isfile("data/prism/data.json"):
        print("Création et import de PRISM/data")
        dataIO.save_json("data/prism/data.json", {})
    if not os.path.isfile("data/prism/global.json"):
        print("Création et import de PRISM/global")
        dataIO.save_json("data/prism/global.json", {})


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
    bot.add_cog(n)
