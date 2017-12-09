import asyncio
import os
import random
import time
import discord
from .utils import checks
from .utils.dataIO import fileIO
from discord.ext import commands
from __main__ import send_cmd_help
from .utils.dataIO import fileIO, dataIO

class Agora:
    """Fonctionnalités communautaires"""
    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/agora/sys.json")

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
                        data["ABUS"][user.id] = data["ABUS"][user.id] + 1 if data["ABUS"][user.id] else 0
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
                    data["ABUS"][user.id] = data["ABUS"][user.id] + 1 if data["ABUS"][user.id] else 0
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


def check_folders():
    if not os.path.exists("data/agora"):
        print("Création du dossier Agora...")
        os.makedirs("data/agora")


def check_files():
    if not os.path.isfile("data/agora/sys.json"):
        print("Création du fichier Agora/sys.json...")
        fileIO("data/agora/sys.json", "save", {"POLLS": {}})


def setup(bot):
    check_folders()
    check_files()
    n = Agora(bot)
    bot.add_cog(n)
    bot.add_listener(n.fp_listen_add, "on_reaction_add")
    bot.add_listener(n.fp_listen_rem, "on_reaction_remove")
    bot.add_listener(n.fp_listen_pin, "on_message_edit")

