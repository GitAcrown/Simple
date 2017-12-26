import asyncio
import operator
import os
import random
import re

import discord
from __main__ import send_cmd_help
from discord.ext import commands

from .utils import checks
from .utils.dataIO import fileIO, dataIO


class Agora:
    """Fonctionnalités communautaires"""
    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/agora/sys.json")
        self.law = dataIO.load_json("data/agora/law.json")

    def gen_txt(self, idp: int):
        if idp in self.sys["POLLS"]:
            data = self.sys["POLLS"][idp]
            em = discord.Embed(color=data["COLOR"])
            em.set_author(name="#{} | {}".format(idp, data["QUESTION"]), icon_url=data["AUTEURIMG"])
            txt = ""
            val = ""
            n = 0
            while n < len(data["REPONSES"]):
                for r in data["REPONSES"]:
                    if data["REPONSES"][r]["ORG"] == n:
                        txt += "\{} - **{}**\n".format(data["REPONSES"][r]["EMOJI"], r)
                        tot = sum([self.sys["POLLS"][idp]["REPONSES"][p]["NB"] for p in self.sys["POLLS"][idp]["REPONSES"]])
                        prc = data["REPONSES"][r]["NB"] / tot if int(tot) > 0 else 0
                        val += "**{}** (*{}*%)\n".format(data["REPONSES"][r]["NB"], round(prc * 100, 2))
                        n += 1
            em.add_field(name="Réponses", value=txt)
            em.add_field(name="Statistiques", value=val)
            em.set_footer(text="Votez avec les réactions correspondantes ci-dessous | Total: {}".format(tot))
            return em
        else:
            return False


    def gen_idp(self):
        r = 100
        while r in self.sys["POLLS"]:
            r = random.randint(100, 999)
        return r

    def find_idp(self, msgid, ignore: bool= False):
        for i in self.sys["POLLS"]:
            if self.sys["POLLS"][i]["MSGID"] == msgid:
                if not ignore:
                    return i if self.sys["POLLS"][i]["ACTIF"] else False
                else:
                    return i
        else:
            return False

    def find_reponse(self, idp, emoji):
        if idp in self.sys["POLLS"]:
            for i in self.sys["POLLS"][idp]["REPONSES"]:
                if emoji == self.sys["POLLS"][idp]["REPONSES"][i]["EMOJI"]:
                    return i
            else:
                return False
        else:
            return False

# FULLCONTROL >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @checks.admin_or_permissions(manage_server=True)
    async def incarne(self, ctx, identifiant: str):
        """Permet de prendre le contrôle du bot en parlant à sa place à travers une interface avancée"""
        if ctx.message.channel.id != "395319484711305217":
            await self.bot.say("Eheheh, bien essayé mais cette commande n'est disponible que dans la **PhoneRoom**")
            return
        channel = self.bot.get_channel(identifiant)
        controle = self.bot.get_channel("395316684292096005")
        if channel:
            if "INCARNE" not in self.sys:
                await self.bot.say("**Préparation** | Veuillez patienter pendant la connexion entre les deux "
                                   "channels...")
                await asyncio.sleep(3)
                em = discord.Embed(title="Incarnation | {}".format(channel.name),
                                   description="**Connexion réussie** - Les messages provenant du salon seront copiés"
                                               " dans ce channel. Tout message que vous enverrez ici sera reproduit par"
                                               " moi-même sur le channel *{}*.\nLa session s'arrête automatiquement au"
                                               " bout de 2m d'inactivité. Vous seul pouvez utiliser cette session.")
                em.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
                await self.bot.say(embed=em)
                await self.bot.send_message(controle, "<@{}> `a démarré une session de INCARNE`".format(
                    ctx.message.author.id))
                await asyncio.sleep(2)
                self.sys["INCARNE"] = {"CHANNEL_SORTIE": channel.id,
                                       "CHANNEL_ENTREE": ctx.message.channel.id}
                while True:
                    msg = await self.bot.wait_for_message(channel=ctx.message.channel,
                                                          author=ctx.message.author, timeout=120)
                    if not msg:
                        await self.bot.say("**Session terminée** | "
                                           "Ce channel n'est plus connecté à *{}*".format(channel.name))
                        del self.sys["INCARNE"]
                        return
                    else:
                        await self.bot.send_typing(channel)
                        await self.bot.send_message(channel, msg.content)
            else:
                await self.bot.say("**Erreur** | Une session est déjà en cours")
        else:
            await self.bot.say("**Erreur** | Le channel n'est pas valide/impossible à atteindre")

# LEGIKHEYS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @commands.group(aliases=["lkm"], pass_context=True)
    @checks.admin_or_permissions(ban_members=True)
    async def legikheysmod(self, ctx):
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @legikheysmod.command(pass_context=True)
    async def add(self, ctx, source: str, url: str, date: str, classt: str, *texte: str):
        """Ajoute un texte à LégiKheys

        <source> - nom de la source
        <url> - lien web public de la source
        <date> - date d'application
        <classt> - classement (exs: 28-3; A01/12bis...)
        [texte] - texte de l'article"""
        if classt.upper() not in self.law:
            if url.startswith("http"):
                if "/" in date:
                    self.law[classt.upper()] = {"SOURCE": source.upper(),
                                                "URL": url,
                                                "DATE": date,
                                                "TEXTE": " ".join(texte),
                                                "MODIFS": []}
                    fileIO("data/agora/law.json", "save", self.law)
                    await self.bot.say("**Succès** | Texte ajouté !")
                else:
                    await self.bot.say("**Erreur** | La date doit être au format jj/mm/aaaa")
            else:
                await self.bot.say("**Erreur** | L'URL n'est pas valide")
        else:
            await self.bot.say("**Déjà existant** | Il semblerait que cet article existe déjà")


    @legikheysmod.command(pass_context=True)
    async def modif(self, ctx, classt: str, date: str, *texte: str):
        """Modifie un texte LégiKheys

        <classt> - classement (exs: 28-3; A01/12bis...)
        <date> - date du changement
        [texte] - nouveau texte de l'article"""
        if classt.upper() in self.law:
            if "/" in date:
                old = self.law[classt.upper()]["TEXTE"]
                dateold = self.law[classt.upper()]["DATE"]
                self.law[classt.upper()]["MODIFS"].append([dateold, old])
                self.law[classt.upper()]["TEXTE"] = " ".join(texte)
                self.law[classt.upper()]["DATE"] = date
                fileIO("data/agora/law.json", "save", self.law)
                await self.bot.say("**Succès** | Texte modifié !")
            else:
                await self.bot.say("**Erreur** | La date doit être au format jj/mm/aaaa")
        else:
            await self.bot.say("**Introuvable** | Vérifiez l'identifiant fourni")

    @legikheysmod.command(pass_context=True)
    async def remove(self, ctx, classt: str):
        """Supprime un texte LégiKheys

        <classt> - classement (exs: 28-3; A01/12bis...)"""
        if classt.upper() in self.law:
            del self.law[classt.upper()]
            fileIO("data/agora/law.json", "save", self.law)
            await self.bot.say("**Succès** | Texte supprimé !")
        else:
            await self.bot.say("**Introuvable** | Vérifiez l'identifiant fourni")

    @commands.command(aliases=["lk"], pass_context=True)
    async def legikheys(self, ctx, *recherche):
        """Recherche dans la base de données LégiKheys

        -- Si le terme recherché est directement l'identifiant d'un article : renvoie l'article demandé
        -- Sinon : renvoie les articles contenant les termes recherchés"""
        if not recherche:
            txt = "__**Index des Articles**__\n"
            liste = []
            for a in self.law:
                liste.append(a)
            liste.sort()
            n = 1
            for i in liste:
                txt += "**Art. {}**\n".format(i)
                if len(txt) > (1990 * n):
                    txt += "$$"
                    n += 1
            msgs = txt.split("$$")
            for msg in msgs:
                await self.bot.whisper(msg)
            return
        elif len(recherche) == 1:
            uid = recherche[0]
            if uid.upper() in self.law:
                art = uid
                groupe = None
                lie = []
                if "-" in art:
                    groupe = art[:art.index("-")]
                for a in self.law:
                    if "-" in a:
                        if art == a.split("-")[0]:
                            lie.append(a)
                if lie:
                    lie.sort()
                    lietxt = "\n\n**Articles liés**: {}".format(", ".join(lie))
                else:
                    lietxt = ""
                em = discord.Embed(title="LégiKheys | Art. {}{}".format(
                    art.upper(), " (Groupe art. {})".format(groupe) if groupe else ""),
                    description=self.law[
                                    art.upper()]["TEXTE"] + lietxt, url=self.law[art.upper()]["URL"])
                if groupe:
                    em.add_field(name="Art. {}".format(groupe), value=self.law[groupe]["TEXTE"])
                em.set_footer(text="En date du {} | Partager: /lk:{}/".format(self.law[uid.upper()]["DATE"],
                                                                              uid.upper()))
                await self.bot.say(embed=em)
                return
            else:
                txt = ""
                for art in self.law:
                    if uid.upper() in art:
                        txt += "**Art. {}** : *{}*\n".format(art, self.law[art]["TEXTE"] if len(
                            self.law[art]["TEXTE"]) <= 60 else self.law[art]["TEXTE"][:60] + "...")
                if txt != "":
                    em = discord.Embed(title="LégiKheys | Similaire à {}".format(uid.upper()),
                                       description=txt)
                    em.set_footer(text="Faîtes '&lk <art>' pour voir l'article")
                    await self.bot.say(embed=em)
                    return
        smart = {}
        for r in recherche:
            for art in self.law:
                if r in self.law[art]["TEXTE"]:
                    smart[art] = smart[art] + 1 if art in smart else 1
        l = [[art, smart[art]] for art in smart]
        l = sorted(l, key=operator.itemgetter(1), reverse=True)
        txt = ""
        for art in l:
            txt += "**Art. {}** : *{}*\n".format(art[0], self.law[art[0]]["TEXTE"] if len(
                        self.law[art[0]]["TEXTE"]) <= 40 else self.law[art[0]]["TEXTE"][:40] + "...")
        if txt != "":
            em = discord.Embed(title="LégiKheys | Recherche de {}".format(", ".join(recherche)),
                               description=txt)
            em.set_footer(text="Du + au - pertinent | Faîtes '&lk <art>' pour voir l'article")
            await self.bot.say(embed=em)
        else:
            await self.bot.say("**Introuvable** | Aucun article ne contient le(s) terme(s) recherché(s)")

# POLLS >>>>>>>>>>>>>>>>>

    @commands.command(pass_context=True, hidden=True)
    async def resetpoll(self, ctx):
        """Permet de reset le fichier de FancyPoll en cas de problèmes"""
        del self.sys["POLLS"]
        self.sys = {"POLLS": {}}
        fileIO("data/agora/sys.json", "save", self.sys)
        await self.bot.say("**Succès** | Tous les polls en cours ont été tués et le fichier a été reset.")

    @commands.command(aliases=["fp", "vote"], pass_context=True, no_pm=True)
    async def fancypoll(self, ctx, *qr: str):
        """Lance un FancyPoll sur le channel en cours et épingle celui-ci

        <qr>: Question?;réponse1;réponse2;réponseN
        L'arrêt du sondage se fait automatiquement lors du desépinglage de celui-ci"""
        rs = lambda: random.randint(0, 255)
        rcolor = int('0x%02X%02X%02X' % (rs(), rs(), rs()), 16)
        if qr:
            qr = " ".join(qr)
            split = qr.split(";")
            q = split[0]
            r = split[1:]
            if len(r) > 9:
                await self.bot.say("**Impossible** | Vous ne pouvez pas mettre plus de 9 options")
                return
            elif len(r) < 2:
                await self.bot.say("**Impossible** | Il faut au moins 2 options de réponse")
                return
            emojis = [s for s in "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"]
            idp = self.gen_idp()
            parsedr = {}
            emos = []
            n = 0
            for i in r:
                if i.startswith(" "):
                    i = i[1:]
                if i.endswith(" "):
                    i = i[:-1]
                parsedr[i] = {"EMOJI": emojis[n],
                              "NB": 0,
                              "ORG": n}
                emos.append(emojis[n])
                n += 1
            self.sys["POLLS"][idp] = {"QUESTION": q,
                                      "REPONSES": parsedr,
                                      "VOTES": {},
                                      "COLOR": rcolor,
                                      "AUTEURIMG": ctx.message.author.avatar_url,
                                      "MSGID": None,
                                      "ACTIF": False,
                                      "ABUS" : {}}
            msg = self.gen_txt(idp)
            msg.set_footer(text="CHARGEMENT... | Patientez pendant que j'organise le sondage")
            menu = await self.bot.say(embed=msg)
            await self.bot.pin_message(menu)
            self.sys["POLLS"][idp]["MSGID"] = menu.id
            self.sys["POLLS"][idp]["ACTIF"] = True
            fileIO("data/agora/sys.json", "save", self.sys)
            for r in emos:
                try:
                    await self.bot.add_reaction(menu, r)
                except:
                    pass
            await self.bot.edit_message(menu, embed=self.gen_txt(idp))
        else:
            await self.bot.say("**Format** | *Question;Réponse1;Réponse2;RéponseN...*")

    async def fp_listen_add(self, reaction, user):
        message = reaction.message
        save = lambda: fileIO("data/agora/sys.json", "save", self.sys)
        idp = self.find_idp(message.id)
        if not user.bot:
            if idp:
                data = self.sys["POLLS"][idp]
                if reaction.emoji in [data["REPONSES"][r]["EMOJI"] for r in data["REPONSES"]]:
                    if user.id not in data["VOTES"]:
                        if user.id in data["ABUS"]:
                            if data["ABUS"][user.id] > 3:
                                await self.bot.send_message(user, "**#{}** | ABUS - Vous ne pouvez plus "
                                                                  "voter.".format(idp))
                                return
                        r = self.find_reponse(idp, reaction.emoji)
                        data["REPONSES"][r]["NB"] += 1
                        data["ABUS"][user.id] = data["ABUS"][user.id] + 1 if user.id in data["ABUS"] else 0
                        data["VOTES"][user.id] = r
                        fileIO("data/agora/sys.json", "save", self.sys)
                        await self.bot.send_message(user, "**#{}** | Merci d'avoir voté \{} !".format(idp, reaction.emoji))
                        await self.bot.edit_message(message, embed=self.gen_txt(idp))
                    else:
                        await self.bot.send_message(user, "**#{}** | Vous avez déjà voté !".format(idp))
                        await self.bot.remove_reaction(message, reaction.emoji, user)
                else:
                    await self.bot.remove_reaction(message, reaction.emoji, user)

    async def fp_listen_rem(self, reaction, user):
        message = reaction.message
        save = lambda: fileIO("data/agora/sys.json", "save", self.sys)
        idp = self.find_idp(message.id)
        if idp:
            data = self.sys["POLLS"][idp]
            if reaction.emoji in [data["REPONSES"][r]["EMOJI"] for r in data["REPONSES"]]:
                if user.id in data["VOTES"]:
                    if user.id in data["ABUS"]:
                        if data["ABUS"][user.id] > 3:
                            await self.bot.send_message(user, "**#{}** | ABUS - Vous ne pouvez pas retirer "
                                                              "votre vote.".format(idp))
                            return
                    data["ABUS"][user.id] = data["ABUS"][user.id] + 1 if user.id in data["ABUS"] else 0
                    r = self.find_reponse(idp, reaction.emoji)
                    if data["VOTES"][user.id] == r:
                        data["REPONSES"][r]["NB"] -= 1
                        del data["VOTES"][user.id]
                    else:
                        return
                    fileIO("data/agora/sys.json", "save", self.sys)
                    await self.bot.send_message(user, "**#{}** | Vous avez retiré votre vote \{}".format(idp,
                                                                                                        reaction.emoji))
                    await self.bot.edit_message(message, embed=self.gen_txt(idp))

    async def fp_listen_pin(self, before, after):
        save = lambda: fileIO("data/agora/sys.json", "save", self.sys)
        idp = self.find_idp(after.id, True)
        if idp:
            tot = sum([self.sys["POLLS"][idp]["REPONSES"][p]["NB"] for p in self.sys["POLLS"][idp]["REPONSES"]])
            if before.pinned and not after.pinned:
                em = self.gen_txt(idp)
                em.set_footer(text="Sondage terminé | {} participant(s) | Merci d'y avoir participé !".format(tot))
                await self.bot.clear_reactions(after)
                await self.bot.edit_message(after, embed=em)
                em.set_author(name="RÉSULTATS #{} | {}".format(idp, self.sys["POLLS"][idp]["QUESTION"]),
                              icon_url=self.sys["POLLS"][idp]["AUTEURIMG"])
                await self.bot.send_message(after.channel, embed=em)
                del self.sys["POLLS"][idp]
                fileIO("data/agora/sys.json", "save", self.sys)

    async def hologram_spawn(self, message):
        if "INCARNE" in self.sys:
            if message.channel.id == self.sys["INCARNE"]["CHANNEL_SORTIE"]:
                if "<@{}>".format(self.bot.user.id) in message.content:
                    color = 0xfab84c
                else:
                    color = 0xd6dfe5
                em = discord.Embed(description=message.content, color=color)
                em.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                userchan = self.bot.get_channel(self.sys["INCARNE"]["CHANNEL_ENTREE"])
                await self.bot.send_message(userchan, embed=em)

        if "Habitué" or "Oldfag" or "Modérateur" or "Malsain" in [r.name for r in message.author.roles]:
            if "/" in message.content:
                output = re.compile('/(.*?)/', re.DOTALL | re.IGNORECASE).findall(message.content)
                if output:
                    for e in output:
                        if ":" in e:
                            art = e.split(":")[1]
                            if e.split(":")[0].lower() == "lk":
                                if art.upper() in self.law:
                                    groupe = None
                                    lie = []
                                    if "-" in art:
                                        groupe = art[:art.index("-")]
                                    for a in self.law:
                                        if "-" in a:
                                            if art == a.split("-")[0]:
                                                lie.append(a)
                                    if lie:
                                        lie.sort()
                                        lietxt = "\n\n**Articles liés**: {}".format(", ".join(lie))
                                    else:
                                        lietxt = ""
                                    em = discord.Embed(title="LégiKheys | Art. {}{}".format(
                                        art.upper(), " (Groupe art. {})".format(groupe) if groupe else ""),
                                        description=self.law[
                                                        art.upper()]["TEXTE"] + lietxt, url=self.law[art.upper()]["URL"])
                                    if groupe:
                                        em.add_field(name="Art. {}".format(groupe), value=self.law[groupe]["TEXTE"])
                                    em.set_footer(text="En date du {} | Invoqué via Holo".format(self.law[art.upper()]["DATE"],
                                                                                                  art.upper()))
                                    await self.bot.send_message(message.channel, embed=em)

def check_folders():
    if not os.path.exists("data/agora"):
        print("Création du dossier Agora...")
        os.makedirs("data/agora")


def check_files():
    if not os.path.isfile("data/agora/sys.json"):
        print("Création du fichier Agora/sys.json...")
        fileIO("data/agora/sys.json", "save", {"POLLS": {}})
    if not os.path.isfile("data/agora/law.json"):
        print("Création du fichier Agora/law.json...")
        fileIO("data/agora/law.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Agora(bot)
    bot.add_cog(n)
    bot.add_listener(n.hologram_spawn, "on_message")
    bot.add_listener(n.fp_listen_add, "on_reaction_add")
    bot.add_listener(n.fp_listen_rem, "on_reaction_remove")
    bot.add_listener(n.fp_listen_pin, "on_message_edit")

