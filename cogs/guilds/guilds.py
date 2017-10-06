import asyncio
import operator
import os
import random
import re
import time
from urllib import request
import string
import discord
from __main__ import send_cmd_help
from discord.ext import commands
from .utils import checks
from .utils.dataIO import fileIO, dataIO
import copy

#MODULE EN BETA

class Guilds:
    """Gestion des Guildes de jeu"""
    def __init__(self, bot):
        self.bot = bot
        self.data = dataIO.load_json("data/guilds/data.json")
        self.grp = dataIO.load_json("data/guilds/grp.json")

    def save(self): #Sauvegarde
        fileIO("data/guilds/data.json", "save", self.data)
        fileIO("data/guilds/grp.json", "save", self.grp)
        return True

    def open(self, user): #Ouvre un compte utilisateur, ou en retourne un le cas échéant
        if user.id not in self.data:
            self.data[user.id] = {"NV_GAMES": [],
                                  "CUSTOMS": {}}
            self.save()
        return self.data[user.id]

    def get_gid(self, guildname:str): #Retrouve la clef d'une guilde avec son nom
        for g in self.grp:
            if self.grp[g]["NOM"].lower() == guildname.lower():
                return g
        return False

    def joinguild(self, user: discord.Member, gid: str): #Permet de rejoindre une guilde
        if not gid.startswith("$"):
            gid = self.get_gid(gid)
        if gid in self.grp:
            if user.id not in self.grp[gid]["MEMBRES"]:
                if self.grp[gid]["LIMITE_GRP"] is None:
                    self.grp[gid]["MEMBRES"].append(user.id)
                    self.save()
                    return True
                else:
                    for g in self.grp[gid]["GROUPES"]:
                        if len(self.grp[gid]["GROUPES"][g]) < int(self.grp[gid]["LIMITE_GRP"]):
                            self.grp[gid]["GROUPES"][g].append(user.id)
                            self.grp[gid]["MEMBRES"].append(user.id)
                            self.save()
                            return g
                    else:
                        nb = len(self.grp[gid]["GROUPES"]) + 1
                        self.grp[gid]["GROUPES"][nb] = [user.id]
                        self.grp[gid]["MEMBRES"].append(user.id)
                        self.save()
                        return nb
            else:
                return False
        else:
            return False

    def quitguild(self, user: discord.Member, gid: str): #Permet de quitter une guilde
        if not gid.startswith("$"):
            gid = self.get_gid(gid)
        if gid in self.grp:
            if user.id in self.grp[gid]["MEMBRES"]:
                if self.grp[gid]["LIMITE_GRP"] is None:
                    self.grp[gid]["MEMBRES"].remove(user.id)
                    self.save()
                    return True
                else:
                    if len(self.grp[gid]["GROUPES"]) > 0:
                        for g in self.grp[gid]["GROUPES"]:
                            if user.id in self.grp[gid]["GROUPES"][g]:
                                self.grp[gid]["GROUPES"][g].remove(user.id)
                                self.grp[gid]["MEMBRES"].remove(user.id)
                                ver = self.reorganise(gid)
                                if not ver:
                                    print("Problème avec reorganise")
                                self.save()
                                return True if ver else False
                        else:
                            return False
                    else:
                        self.grp[gid]["MEMBRES"].remove(user.id)
                        self.save()
                        return True
            else:
                return False
        else:
            return False


    def reorganise(self, gid: str): #Réorganise les groupes
        if not gid.startswith("$"):
            gid = self.get_gid(gid)
        if gid in self.grp:
            if self.grp[gid]["GROUPES"] is not None:
                datacop = copy.deepcopy(self.grp[gid]["GROUPES"])
                for g in self.grp[gid]["GROUPES"]: #1) On vérifie si il y a pas des groupes vides
                    if len(self.grp[gid]["GROUPES"][g]) == 0:
                        del datacop[g] #On les supprime
                self.grp[gid]["GROUPES"] = datacop
                if len(self.grp[gid]["GROUPES"]) > 0:
                    groupes = []
                    for g in self.grp[gid]["GROUPES"]: #2) On classe les groupes par nb de joueurs en ignorant les groupes pleins
                        if len(self.grp[gid]["GROUPES"][g]) < self.grp[gid]["LIMITE_GRP"]:
                            groupes.append([g, len(self.grp[gid]["GROUPES"][g])])
                    if groupes != []:
                        sort = sorted(groupes, key=operator.itemgetter(1)) #On obtient une liste des groupes non-pleins
                        last = sort[len(sort) - 1]
                        last = last[0] #On prend le groupe le moins rempli
                        first = sort[0]
                        first = first[0] #On prend le groupe le plus rempli (sans pour autant qu'il soit plein)
                        membre = random.choice(self.grp[gid]["GROUPES"][last]) #On choisi un membre au hasard
                        self.grp[gid]["GROUPES"][last].remove(membre)
                        self.grp[gid]["GROUPES"][first].append(membre) #On l'enlève du dernier et on le rajoute au premier en nombre
                        datacop = copy.deepcopy(self.grp[gid]["GROUPES"])
                        for g in self.grp[gid]["GROUPES"]: #1bis) On revérifie si il y a pas des groupes vides
                            if len(self.grp[gid]["GROUPES"][g]) == 0:
                                del datacop[g]  # On les supprime
                        self.grp[gid]["GROUPES"] = datacop
                self.save()
                return True
            else:
                return False
        else:
            return False

    def newguild(self, nom, jeu, descr, nbpg:int = None):
        clef = "$" + str(''.join(
            random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in
            range(6)))
        for g in self.grp:
            if self.grp[g]["NOM"].lower() == nom:
                return False
        self.grp[clef] = {"NOM": nom,
                          "JEU": jeu,
                          "DESCR": descr,
                          "LIMITE_GRP": nbpg,
                          "GROUPES": {},
                          "MEMBRES": [],
                          "ACTIF": False,
                          "BILL": {"CHAN": None, "MSG": None}}
        self.save()
        return clef

    @commands.group(pass_context=True, no_pm=True)
    async def gld(self, ctx):
        """Gestion des Guildes de jeu"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @gld.command(pass_context=True)
    async def new(self, ctx, nom:str, jeu:str, descr:str, nbpg:int = None):
        """Permet de créer une nouvelle guilde
        /!\ Chaque terme doit être entre guillements (sauf nbpg) /!\
        Nom: nom de votre guilde (peut être différent de celui du jeu)
        Jeu: nom du jeu joué par les membres de la guilde (nom EXACT si possible)
        Descr: description rapide de votre guilde
        nbpg (optionnel): permet de définir le nombre de joueurs par groupe/équipe"""
        create = self.newguild(nom, jeu, descr, nbpg)
        if create:
            await self.bot.say("**Guilde créée avec succès** | Faîtes *&gld spawn* pour l'activer !")
            await self.bot.whisper("**Clef de votre guilde:** *{}*\n\n"
                                   "Conservez-là précieusement, elle vous permet de réaliser des actions de "
                                   "modification. Elle est confidentielle, partagez-là qu'aux personnes à qui vous "
                                   "faîtes confiance.\nSous aucun prétexte vous pourrez l'obtenir de "
                                   "nouveau en cas de perte.".format(create))
        else:
            await self.bot.say("**Echec** | Je n'ai pas réussi à créer la guilde...")

    @gld.command(pass_context=True, no_pm=True)
    async def spawn(self, ctx):
        """Permet de faire apparaitre un billet de guilde sur le channel pour l'activer."""
        server = ctx.message.server
        channel = ctx.message.channel
        quest = await self.bot.whisper("**Clef de guilde ?** | Tapez le clef de la guilde que vous voulez activer.")
        rep = await self.bot.wait_for_message(author=ctx.message.author, channel=quest.channel, timeout=30)
        if rep is None:
            await self.bot.whisper("**TIMEOUT** | Bye :wave:")
            return
        elif rep.content in self.grp:
            clef = rep.content
            if self.grp[clef]["ACTIF"] is False:
                await self.bot.whisper("**Clef reconnue !** | Patientez pendant que je prépare le billet de guilde...")
                em = discord.Embed(title="G| {} ({})".format(self.grp[clef]["NOM"], self.grp[clef]["JEU"]),
                                   description=self.grp[clef]["DESCR"])
                if self.grp[clef]["LIMITE_GRP"] is None:
                    psd = [server.get_member(n).name for n in self.grp[clef]["MEMBRES"]]
                    em.add_field(name="Membres ({})".format(len(self.grp[clef]["MEMBRES"])),
                                 value="\n".join(psd) if len(self.grp[clef]["MEMBRES"]) > 0 else "Vide")
                else:
                    for gr in self.grp[clef]["GROUPES"]:
                        psd = [server.get_member(n).name for n in self.grp[clef]["GROUPES"][gr]]
                        em.add_field(name="GRP{} ({}/{})".format(gr, len(self.grp[clef]["GROUPES"][gr]),
                                                                 self.grp[clef]["LIMITE_GRP"]), value="\n".join(
                            psd) if len(self.grp[clef]["GROUPES"][gr]) > 0 else "Vide")
                em.set_footer(text="Cliquez sur + pour rejoindre/quitter cette guilde")
                bill = await self.bot.send_message(channel, embed=em)
                await self.bot.add_reaction(bill, "➕")
                await asyncio.sleep(1)
                await self.bot.pin_message(bill)
                self.grp[clef]["BILL"]["MSG"] = bill.id
                self.grp[clef]["BILL"]["CHAN"] = bill.channel.id
                self.grp[clef]["ACTIF"] = True
                self.save()
                await self.bot.whisper("**Votre guilde est prête** | Bon jeu !")
            else:
                await self.bot.whisper("**Clef reconnue mais un billet existe déjà...**")
                return
        else:
            await self.bot.whisper("**Désolé mais je n'ai pas reconnu cette clef...**")

    async def join(self, reaction, user):
        server = reaction.message.server
        if reaction.emoji == "➕":
            for g in self.grp:
                if self.grp[g]["BILL"]["MSG"] == reaction.message.id:
                    val = self.joinguild(user, g)
                    if val is True:
                        await self.bot.send_message(user, "**Vous avez rejoint la guilde {} !**".format(
                            self.grp[g]["NOM"]))
                    elif str(val).isdigit():
                        await self.bot.send_message(user, "**Vous avez rejoint la guilde {} dans le groupe n°{} !**"
                                                    .format(self.grp[g]["NOM"], str(val)))
                    else:
                        await self.bot.send_message(user, "**Impossible de rejoindre la guilde :(**")
                        return
                    clef = g
                    em = discord.Embed(title="G| {} ({})".format(self.grp[clef]["NOM"], self.grp[clef]["JEU"]),
                                       description=self.grp[clef]["DESCR"])
                    if self.grp[clef]["LIMITE_GRP"] is None:
                        psd = [server.get_member(n).name for n in self.grp[clef]["MEMBRES"]]
                        em.add_field(name="Membres ({})".format(len(self.grp[clef]["MEMBRES"])),
                                     value="\n".join(psd) if len(self.grp[clef]["MEMBRES"]) > 0 else "Vide")
                    else:
                        for gr in self.grp[clef]["GROUPES"]:
                            psd = [server.get_member(n).name for n in self.grp[clef]["GROUPES"][gr]]
                            em.add_field(name="GRP{} ({}/{})".format(gr, len(self.grp[clef]["GROUPES"][gr]),
                                                                     self.grp[clef]["LIMITE_GRP"]), value="\n".join(
                                psd) if len(self.grp[clef]["GROUPES"][gr]) > 0 else "Vide")
                    em.set_footer(text="Cliquez sur + pour rejoindre/quitter cette guilde")
                    await self.bot.edit_message(reaction.message, embed=em)

    async def quit(self, reaction, user):
        server = reaction.message.server
        if reaction.emoji == "➕":
            for g in self.grp:
                if self.grp[g]["BILL"]["MSG"] == reaction.message.id:
                    val = self.quitguild(user, g)
                    if val is True:
                        await self.bot.send_message(user, "**Vous avez quitté la guilde {} !**".format(
                            self.grp[g]["NOM"]))
                    else:
                        await self.bot.send_message(user, "**Je n'ai pas réussi à vous faire quitter la guilde :(**")
                        return
                    clef = g
                    em = discord.Embed(title="G| {} ({})".format(self.grp[clef]["NOM"], self.grp[clef]["JEU"]),
                                       description=self.grp[clef]["DESCR"])
                    if self.grp[clef]["LIMITE_GRP"] is None:
                        psd = [server.get_member(n).name for n in self.grp[clef]["MEMBRES"]]
                        em.add_field(name="Membres ({})".format(len(self.grp[clef]["MEMBRES"])),
                                     value="\n".join(psd) if len(self.grp[clef]["MEMBRES"]) > 0 else "Vide")
                    else:
                        for gr in self.grp[clef]["GROUPES"]:
                            psd = [server.get_member(n).name for n in self.grp[clef]["GROUPES"][gr]]
                            em.add_field(name="GRP{} ({}/{})".format(gr, len(self.grp[clef]["GROUPES"][gr]),
                                                                     self.grp[clef]["LIMITE_GRP"]), value="\n".join(
                                psd) if len(self.grp[clef]["GROUPES"][gr]) > 0 else "Vide")
                    em.set_footer(text="Cliquez sur + pour rejoindre/quitter cette guilde")
                    await self.bot.edit_message(reaction.message, embed=em)

def check_folders():
    if not os.path.exists("data/guilds"):
        print("Création du dossier de Guilds...")
        os.makedirs("data/guilds")


def check_files():
    if not os.path.isfile("data/guilds/data.json"):
        print("Ouverture de Guilds/data")
        fileIO("data/guilds/data.json", "save", {})
    if not os.path.isfile("data/guilds/grp.json"):
        print("Ouverture de Guilds/grp")
        fileIO("data/guilds/grp.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Guilds(bot)
    bot.add_listener(n.join, "on_reaction_add")
    bot.add_listener(n.quit, "on_reaction_remove")
    bot.add_cog(n)
