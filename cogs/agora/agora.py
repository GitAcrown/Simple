import asyncio
import operator
import os
import random
import re
import string
import time

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
        self.ektv = dataIO.load_json("data/agora/ektv.json")
        self.cycle_task = bot.loop.create_task(self.agora_loop())
        self.instances = {}

    def save(self):
        fileIO("data/agora/sys.json", "save", self.sys)
        return True

    async def agora_loop(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(5)  # Temps de mise en route
            if "REFS" not in self.sys:
                self.sys["REFS"] = {}
            channel = self.bot.get_channel("406475230005952512")
            while True:
                self.save()
                for i in self.sys["REFS"]:
                    if self.sys["REFS"][i]["LIMITE"] <= time.time():
                        mess = await self.bot.get_message(channel, self.sys["REFS"][i]["MSGID"])
                        if mess:
                            await self.bot.unpin_message(mess)
                            continue
                        else:
                            await self.bot.send_message(channel, "**Erreur critique** | L'arrêt automatique de #{} est "
                                                                 "impossible car le message lié est introuvable"
                                                                 "".format(i))
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

#EKTV =======================================

    """@commands.group(aliases=["tv"], pass_context=True)
    async def ektv(self, ctx):
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @ektv.command(pass_context=True)
    async def pub(self, *billet: str):"""

# OUTILS ASSEMBLEE :::::::::::::::::::::::::::

    @commands.command(aliases=["r", "ref"], pass_context=True, no_pm=True)
    async def referendum(self, ctx, *qr):
        """Lance un Référendum et épingle celui-ci dans le channel #Assemblee

        Format: &r question ?;réponse 1;réponse 2;réponse n..."""
        emojis = [s for s in "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"]
        server = ctx.message.server
        if qr:
            if qr[0].lower() == "stop":
                if qr[1].upper() in self.sys["POLLS"]:
                    num = qr[1].upper()
                    poll = self.sys["REFS"][num]
                    if not ctx.message.author.server_permissions.ban_members:
                        await self.bot.say("**Erreur** | Vous n'êtes pas autorisé à arrêter le référendum")
                        return
                    mess = await self.bot.get_message(ctx.message.channel, poll["MSGID"])
                    if mess:
                        await self.bot.unpin_message(mess)
                        return
                    else:
                        await self.bot.say("**Erreur** | Vous devez être sur le channel du référendum épinglé pour l'arrêter.")
                        return
                else:
                    await self.bot.say("**Introuvable** | Cet identifiant est introuvable (Ne mettez pas le #)")
                    return
            lim = (int(len([user.id for user in server.members if "Habitué" in [r.name for r in user.roles]])) / 2) + 1
            num = random.randint(100, 999)
            color = 0xf7f7f7
            qr = " ".join(qr)
            qr = qr.split(";")
            question = qr[0]
            reponses = [self.normalize(r) for r in qr[1:]]
            if not 2 <= len(reponses) <= 9:
                await self.bot.say("**Invalide** | Il ne peut y avoir qu'entre 2 et 9 options disponibles.")
                return
            reps = {}
            emos = []
            n = 0
            rtx = stx = ""
            for r in reponses:
                index = reponses.index(r)
                reps[r] = {"EMOJI": emojis[index],
                           "VOTES": []}
                rtx += "\{} - **{}**\n".format(emojis[index], r)
                stx += "\{} - **{}** (*{}*%)\n".format(emojis[index], 0, 0)
                emos.append(emojis[index])
            em = discord.Embed(title="RÉFÉRENDUM | {}".format(question.capitalize()), color=color)
            em.add_field(name="Réponses", value=rtx)
            em.add_field(name="Stats", value=stx)
            em.set_footer(text="#{} ({}) | Votez avec les réactions ci-dessous".format(num, ctx.message.author.name))
            await self.bot.send_typing(ctx.message.channel)
            msg = await self.bot.send_message(server.get_channel("406475230005952512"), embed=em)
            self.sys["REFS"][num] = {"QUESTION": question,
                                     "REPONSES": reps,
                                     "COLOR": color,
                                     "MSGID": str(msg.id),
                                     "DESC": "",
                                     "AUTEUR": str(ctx.message.author.name),
                                     "AUTEUR_ID": str(ctx.message.author.id),
                                     "TIMESTAMP": time.strftime("le %d/%m/%Y à %H:%M", time.localtime()),
                                     "LIMITE": time.time() + 300,  # x*24h
                                     "MIN_VOTES": lim,
                                     "LISTE_Q": reponses}  # Nb de membres habitués / 2 + 1
            self.save()
            for e in emos:
                try:
                    await self.bot.add_reaction(msg, e)
                except:
                    pass
            await self.bot.add_reaction(msg, "📱")
            await self.bot.pin_message(msg)
        else:
            await self.bot.say("**Format** | `&r Question ?;Réponse 1;Réponse 2;Réponse N...`")

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    async def resetrefs(self, ctx):
        """Reset tous les référendums en cours"""
        self.sys["REFS"] = {}
        fileIO("data/agora/sys.json", "save", self.sys)
        await self.bot.say("**Succès** | Tous les référendums en cours ont été supprimés.")

    # FULLCONTROL >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    async def incarne(self, ctx, identifiant: str):
        """Permet de prendre le contrôle du bot en parlant à sa place à travers une interface avancée"""
        if identifiant == "reset":
            if "INCARNE" in self.sys:
                del self.sys["INCARNE"]
                return
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
                                               " bout de 2m d'inactivité. Vous seul pouvez utiliser cette session.".format(channel.name))
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
                if "bis" in art:
                    groupe = art.lower()[:art.index("bis")]
                for a in self.law:
                    if "-" in a:
                        if art == a.split("-")[0]:
                            lie.append(a)
                    if "bis" or "BIS" in a:
                        if art.lower() == a.split("bis")[0]:
                            lie.append(a)
                for e in lie:
                    if e == art:
                        lie.remove(e)
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

    def normalize(self, txt: str):
        if txt.startswith(" "):
            txt = txt[1:]
        if txt.endswith(" "):
            txt = txt[:-1]
        txt = txt.capitalize()
        return txt

    def msgid_to_poll(self, msgid):
        for i in self.sys["POLLS"]:
            if self.sys["POLLS"][i]["MSGID"] == msgid:
                return self.sys["POLLS"][i], i
        return False

    def msgid_to_ref(self, msgid):
        for i in self.sys["REFS"]:
            if self.sys["REFS"][i]["MSGID"] == msgid:
                return self.sys["REFS"][i], i
        return False

    def poll_embed(self, msgid):
        if self.msgid_to_poll(msgid):
            poll, pid = self.msgid_to_poll(msgid)
            rcolor = poll["COLOR"]
            question = poll["TITRE"]
            avatar = poll["IMG"]
            reponses = poll["REPONSES"]
            strict = poll["STRICT"]
            tot = sum([poll["R_STATS"][p]["NB"] for p in poll["R_STATS"]])
            rtx = stx = ""
            for r in reponses:
                nb = poll["R_STATS"][r]["NB"]
                emoji = poll["R_STATS"][r]["EMOJI"]
                prc = nb / tot if int(tot) > 0 else 0
                rtx += "\{} - **{}**\n".format(emoji, r)
                stx += "\{} - **{}** (*{}*%)\n".format(emoji, nb, round(prc * 100, 2))
            em = discord.Embed(color=rcolor)
            em.set_author(name="#{} | {}".format(pid, question), icon_url=avatar)
            em.add_field(name="Réponses", value=rtx)
            em.add_field(name="Stats", value=stx)
            em.set_footer(text="Votez avec une réaction ci-dessous ({}) | Total: {}".format("Vote strict" if strict else
                                                                                            "Vote souple", tot))
            return em
        return False

    def ref_embed(self, msgid, type: str="edit"):
        if self.msgid_to_ref(msgid):
            ref, num = self.msgid_to_ref(msgid)
            color = ref["COLOR"]
            question = ref["QUESTION"]
            reponses = ref["REPONSES"]
            liste = ref["LISTE_Q"]
            auteur = "<@{}>".format(ref["AUTEUR_ID"])
            demar = ref["TIMESTAMP"]
            membretot = (ref["MIN_VOTES"] * 2) - 1
            tot = sum([len(ref["REPONSES"][r]["VOTES"]) for r in ref["REPONSES"]])
            rtx = stx = ""
            for r in liste:
                nb = len(ref["REPONSES"][r]["VOTES"])
                emoji = ref["REPONSES"][r]["EMOJI"]
                prc = nb / tot if int(tot) > 0 else 0
                rtx += "\{} - **{}**\n".format(emoji, r)
                stx += "\{} - **{}** (*{}*%)\n".format(emoji, nb, round(prc * 100, 1))
            if type == "fin":
                em = discord.Embed(title="RÉSULTATS | {}".format(question.capitalize()), color=color)
                em.set_footer(text="#{} ({}) | {} participant·e·s | Merci d'y avoir participé !".format(
                    num, ref["AUTEUR"], tot))
            elif type == "cr":  #compte rendu
                plus = "Lancé par {} {}\n**{}** membres de l'Assemblée y ont participé, soit {}% des membres.\n" \
                       "*Aucun problème n'a eu lieu dans le déroulement du Référendum, le résultat est certifié valide" \
                       " conformément à l'article 31 de la Charte.*".format(auteur, demar, tot, round((tot / membretot) * 100, 2))
                em = discord.Embed(title="COMPTE-RENDU | {}".format(question.capitalize()), description= plus,
                                   color= color)
                em.set_footer(text="Fichier texte disponible dans le salon de l'Assemblée".format(
                    num, ref["AUTEUR"], tot))
            else:
                em = discord.Embed(title="RÉFÉRENDUM | {}".format(question.capitalize()), color=color)
                em.set_footer(text="#{} ({}) | {} participant·e·s".format(num, ref["AUTEUR"], tot))
            em.add_field(name="Réponses", value=rtx)
            em.add_field(name="Stats", value=stx)
            return em
        return False

    def crtext(self, msgid, server: discord.Server):
        if self.msgid_to_ref(msgid):
            ref, num = self.msgid_to_ref(msgid)
            txt = "IDENTIFIANT\t{}\n".format(num)
            txt += "QUESTION\t{}\n".format(ref["QUESTION"])
            txt += "AUTEUR\t{} ({})\n".format(ref["AUTEUR"], ref["AUTEUR_ID"])
            tot = sum([len(ref["REPONSES"][r]["VOTES"]) for r in ref["REPONSES"]])
            txt += "TOTAL DE VOTANTS\t{}\n".format(tot)
            txt += "NB DE MEMBRES\t{}\n".format((ref["MIN_VOTES"] * 2) - 1)
            txt += "=== VOTES ===\n\n"
            for r in ref["REPONSES"]:
                txt += ">>> {}\n".format(r)
                for u in ref["REPONSES"][r]["VOTES"]:
                    try:
                        user = server.get_member(u).name
                    except:
                        user = u
                    txt += "- {}\n".format(user)
                txt += "\n"
            return txt
        else:
            return False


    def find_user(self, msgid, user: discord.Member):
        if self.msgid_to_poll(msgid):
            poll, pid = self.msgid_to_poll(msgid)
            for p in poll["R_STATS"]:
                if user.id in poll["R_STATS"][p]["USERS"]:
                    return p
        return False

    def already_voted(self, msgid, user: discord.Member):
        if self.msgid_to_ref(msgid):
            ref, num = self.msgid_to_ref(msgid)
            for p in ref["REPONSES"]:
                if user.id in ref["REPONSES"][p]["VOTES"]:
                    return p
        return False

    @commands.command(aliases=["fp", "vote"], pass_context=True, no_pm=True)
    async def fancypoll(self, ctx, *qr):
        """Lance un FancyPoll sur le channel en cours et épingle celui-ci

        <qr>: Question?;réponse1;réponse2;réponseN
        Il est possible d'ajouter $ à la fin de la commande pour passer le sondage en mode 'Souple'
        L'arrêt du sondage se fait automatiquement lors du desépinglage de celui-ci ou si vous faîtes [p]fp stop <id>"""
        rs = lambda: random.randint(0, 255)
        rcolor = int('0x%02X%02X%02X' % (rs(), rs(), rs()), 16)
        emojis = [s for s in "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿"]
        pid = str(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(3)))
        if qr:
            if qr[0].lower() == "stop":
                if qr[1].upper() in self.sys["POLLS"]:
                    pid = qr[1].upper()
                    poll = self.sys["POLLS"][pid]
                    if poll["AUTEUR"] != ctx.message.author.id or not ctx.message.author.server_permissions.ban_members:
                        await self.bot.say("**Erreur** | Vous n'êtes pas le propriétaire du sondage")
                        return
                    mess = await self.bot.get_message(ctx.message.channel, poll["MSGID"])
                    if mess:
                        await self.bot.unpin_message(mess)
                        return
                    else:
                        await self.bot.say("**Erreur** | Vous devez être sur le channel du sondage pour l'arrêter")
                        return
                else:
                    await self.bot.say("**Introuvable** | Cet identifiant est introuvable (Ne mettez pas le #)")
                    return
            qr = " ".join(qr)
            strict = True
            if qr.endswith("$"):
                strict = False
                qr = qr.replace("$", "")
            qr = qr.split(";")
            question = qr[0]
            reponses = [self.normalize(r) for r in qr[1:]]
            if not 2 <= len(reponses) <= 9:
                await self.bot.say("**Invalide** | Il doit y avoir entre 2 et 9 options disponibles")
                return
            parsed = {}
            emos = []
            rtx = stx = ""
            for i in reponses:
                index = reponses.index(i)
                parsed[i] = {"NB": 0,
                             "EMOJI": emojis[index],
                             "USERS": []}
                rtx += "\{} - **{}**\n".format(emojis[index], i)
                stx += "\{} - **{}** (*{}*%)\n".format(emojis[index], 0, 0)
                emos.append(emojis[index])
            em = discord.Embed(color=rcolor)
            em.set_author(name="#{} | {}".format(pid, question.capitalize()), icon_url=ctx.message.author.avatar_url)
            em.add_field(name="Réponses", value=rtx)
            em.add_field(name="Stats", value=stx)
            em.set_footer(text="Votez avec une réaction ci-dessous ({})".format("Vote strict" if strict else "Vote "
                                                                                                             "souple"))
            await self.bot.send_typing(ctx.message.channel)
            msg = await self.bot.say(embed=em)
            self.sys["POLLS"][pid] = {"TITRE": question,
                                      "R_STATS": parsed,
                                      "REPONSES": reponses,
                                      "COLOR": rcolor,
                                      "IMG": ctx.message.author.avatar_url,
                                      "AUTEUR": ctx.message.author.id,
                                      "MSGID": msg.id,
                                      "STRICT": strict}
            for e in emos:
                try:
                    await self.bot.add_reaction(msg, e)
                except:
                    pass
            await self.bot.add_reaction(msg, "📱")
            await self.bot.pin_message(msg)
        else:
            await self.bot.say("**Format** | `{}fp Question ?;Réponse 1;Réponse 2;Réponse N...($)`".format(ctx.prefix))

    async def fp_listen_add(self, reaction, user):
        message = reaction.message
        if self.msgid_to_poll(message.id):
            if not user.bot:
                poll, pid = self.msgid_to_poll(message.id)
                if reaction.emoji in [poll["R_STATS"][r]["EMOJI"] for r in poll["R_STATS"]]:
                    if not self.find_user(message.id, user):
                        for r in poll["R_STATS"]:
                            if reaction.emoji == poll["R_STATS"][r]["EMOJI"]:
                                poll["R_STATS"][r]["NB"] += 1
                                poll["R_STATS"][r]["USERS"].append(user.id)
                                await self.bot.edit_message(message, embed=self.poll_embed(message.id))
                                await self.bot.send_message(user, "**#{}** | Merci d'avoir voté !"
                                                                  "".format(pid))
                                return
                    else:
                        await self.bot.remove_reaction(message, reaction.emoji, user)
                        return
                elif reaction.emoji == "📱":
                    txt = "**AFFICHAGE MOBILE** - ***{}***\n\n".format(poll["TITRE"])
                    reponses = poll["REPONSES"]
                    rtx = stx = ""
                    tot = sum([poll["R_STATS"][p]["NB"] for p in poll["R_STATS"]])
                    for r in reponses:
                        nb = poll["R_STATS"][r]["NB"]
                        emoji = poll["R_STATS"][r]["EMOJI"]
                        prc = nb / tot if int(tot) > 0 else 0
                        rtx += "\{} - **{}**\n".format(emoji, r)
                        stx += "\{} - **{}** (*{}*%)\n".format(emoji, nb, round(prc * 100, 2))
                    txt += "__**Réponses**__\n{}\n".format(rtx)
                    txt += "__**Stats**__\n{}".format(stx)
                    await self.bot.send_message(user, txt)
                    await self.bot.remove_reaction(message, reaction.emoji, user)
                else:
                    await self.bot.remove_reaction(message, reaction.emoji, user)
        if self.msgid_to_ref(message.id):
            if not user.bot:
                ref, num = self.msgid_to_ref(message.id)
                if reaction.emoji in [ref["REPONSES"][r]["EMOJI"] for r in ref["REPONSES"]]:
                    if not self.already_voted(message.id, user):
                        for r in ref["REPONSES"]:
                            if reaction.emoji == ref["REPONSES"][r]["EMOJI"]:
                                ref["REPONSES"][r]["VOTES"].append(user.id)
                                await self.bot.edit_message(message, embed=self.ref_embed(message.id))
                                await self.bot.send_message(user, "**RÉFÉRENDUM (#{})** | Vote comptabilisé !".format(
                                    num))
                                return
                    else:
                        await self.bot.remove_reaction(message, reaction.emoji, user)
                elif reaction.emoji == "📱":
                    txt = "**AFFICHAGE MOBILE** - **{}**\n\n".format(ref["QUESTION"])
                    reponses = ref["REPONSES"]
                    liste = ref["LISTE_Q"]
                    rtx = stx = ""
                    tot = sum([len(ref["REPONSES"][r]["VOTES"]) for r in ref["REPONSES"]])
                    for r in liste:
                        nb = len(ref["REPONSES"][r]["VOTES"])
                        emoji = ref["REPONSES"][r]["EMOJI"]
                        prc = nb / tot if int(tot) > 0 else 0
                        rtx += "\{} - **{}**\n".format(emoji, r)
                        stx += "\{} - **{}** (*{}*%)\n".format(emoji, nb, round(prc * 100, 1))
                    txt += "__**Réponses**__\n{}\n".format(rtx)
                    txt += "__**Stats**__\n{}".format(stx)
                    await self.bot.send_message(user, txt)
                    await self.bot.remove_reaction(message, reaction.emoji, user)
                else:
                    await self.bot.remove_reaction(message, reaction.emoji, user)

    async def fp_listen_rem(self, reaction, user):
        message = reaction.message
        if self.msgid_to_poll(message.id):
            if not user.bot:
                poll, pid = self.msgid_to_poll(message.id)
                if not poll["STRICT"]:
                    if self.find_user(message.id, user):
                        if reaction.emoji in [poll["R_STATS"][r]["EMOJI"] for r in poll["R_STATS"]]:
                            for r in poll["R_STATS"]:
                                if reaction.emoji == poll["R_STATS"][r]["EMOJI"]:
                                    if user.id in poll["R_STATS"][r]["USERS"]:
                                        poll["R_STATS"][r]["NB"] -= 1
                                        poll["R_STATS"][r]["USERS"].remove(user.id)
                                        await self.bot.edit_message(message, embed=self.poll_embed(message.id))
                                        await self.bot.send_message(user, "**#{}** | Vous avez retiré votre vote"
                                                                          "".format(pid))
                                        return

    async def fp_listen_pin(self, before, after):
        server = after.server
        if self.msgid_to_poll(before.id):
            if before.pinned and not after.pinned:
                poll, pid = self.msgid_to_poll(before.id)
                em = self.poll_embed(before.id)
                tot = sum([poll["R_STATS"][p]["NB"] for p in poll["R_STATS"]])
                em.set_footer(text="Sondage terminé | {} participant(s) | Merci d'y avoir participé !".format(tot))
                em.set_author(name="RÉSULTATS #{} | {}".format(pid, poll["TITRE"]), icon_url=poll["IMG"])
                await self.bot.send_message(after.channel, embed=em)
                del self.sys["POLLS"][pid]
        if self.msgid_to_ref(before.id):
            if before.pinned and not after.pinned:
                hall = "204585334925819904"
                ref, num = self.msgid_to_ref(before.id)
                await self.bot.send_message(after.channel, embed=self.ref_embed(before.id, "fin"))
                await self.bot.send_message(server.get_channel(hall), embed=self.ref_embed(before.id, "cr"))
                txt = self.crtext(before.id, server)
                filename = "Ref_{}.txt".format(num)
                file = open("data/agora/junk/{}".format(filename), "w", encoding="UTF-8")
                file.write(txt)
                file.close()
                await asyncio.sleep(0.5)
                try:
                    await self.bot.send_file(before.channel, "data/agora/junk/{}".format(filename))
                    os.remove("data/agora/junk/{}".format(filename))
                except Exception as e:
                    await self.bot.say("**Impossible d'upload le Compte-rendu texte** | `{}`".format(e))
                del self.sys["REFS"][num]

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
                                                        art.upper()]["TEXTE"] + lietxt,
                                        url=self.law[art.upper()]["URL"])
                                    if groupe:
                                        em.add_field(name="Art. {}".format(groupe), value=self.law[groupe]["TEXTE"])
                                    em.set_footer(
                                        text="En date du {} | Invoqué via balise".format(self.law[art.upper()]["DATE"],
                                                                                       art.upper()))
                                    await self.bot.send_message(message.channel, embed=em)


def check_folders():
    if not os.path.exists("data/agora"):
        print("Création du dossier Agora...")
        os.makedirs("data/agora")
    if not os.path.exists("data/agora/junk"):
        print("Création du dossier Agora/junk...")
        os.makedirs("data/agora/junk")


def check_files():
    if not os.path.isfile("data/agora/sys.json"):
        print("Création du fichier Agora/sys.json...")
        fileIO("data/agora/sys.json", "save", {"POLLS": {}, "REFS": {}})
    if not os.path.isfile("data/agora/law.json"):
        print("Création du fichier Agora/law.json...")
        fileIO("data/agora/law.json", "save", {})
    if not os.path.isfile("data/agora/ektv.json"):
        print("Création du fichier Agora/ektv.json...")
        fileIO("data/agora/ektv.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Agora(bot)
    bot.add_cog(n)
    bot.add_listener(n.hologram_spawn, "on_message")
    bot.add_listener(n.fp_listen_add, "on_reaction_add")
    bot.add_listener(n.fp_listen_rem, "on_reaction_remove")
    bot.add_listener(n.fp_listen_pin, "on_message_edit")
