import asyncio
import os
import random
import re
import string
import sys
import time
from urllib import request

import aiohttp
import discord
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from __main__ import send_cmd_help
from discord.ext import commands

from .utils import checks
from .utils.dataIO import fileIO, dataIO


# Affichages : Web/Upload/Billet/Infos (W.U.B.I.)


class Stickers:
    """Gestion des stickers et autres fonctions à l'écrit | Version universelle"""

    def __init__(self, bot):
        self.bot = bot
        self.stk = dataIO.load_json("data/stickers/stk.json")
        self.user = dataIO.load_json("data/stickers/user.json")

    def save(self):
        fileIO("data/stickers/stk.json", "save", self.stk)
        fileIO("data/stickers/user.json", "save", self.user)
        return True

    def list_stk(self, server: discord.Server):
        lst = [self.stk[server.id]["STK"][e]["NOM"] for e in self.stk[server.id]["STK"]]
        return lst

    def levenshtein(self, s1, s2):
        if len(s1) < len(s2):
            m = s1
            s1 = s2
            s2 = m
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[
                                 j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def similarite(self, mot, liste, tolerance=3):
        prochenb = tolerance
        prochenom = None
        for i in liste:
            if self.levenshtein(i, mot) < prochenb:
                prochenom = i
                prochenb = self.levenshtein(i, mot)
        else:
            return prochenom

    def get_stk(self, server: discord.Server, nom):
        if server.id not in self.stk:
            self.stk[server.id] = {}
        for n in self.stk[server.id]["STK"]:
            if nom == self.stk[server.id]["STK"][n]["NOM"]:
                return n
        else:
            return False

    def get_stk_opt(self, server: discord.Server, nom):
        if server.id not in self.stk:
            self.stk[server.id] = {}
        for n in self.stk[server.id]["OPT"]["APPROB"]:
            if nom == self.stk[server.id]["OPT"]["APPROB"][n]["NOM"]:
                return n
        else:
            return False

    def add_sticker(self, clef, nom: str, chemin, auteur: discord.Member, url, autbis=None, importe=None,
                    tags=None):
        if tags is None: tags = []
        server = auteur.server
        if server.id not in self.stk:
            self.stk[server.id] = {}
        if clef not in self.stk[server.id]:
            autorise = False if not auteur.server_permissions.manage_messages else True
            if autorise:
                self.stk[server.id]["STK"][clef] = {"NOM": nom,
                                                    "CHEMIN": chemin,
                                                    "AUTEUR": auteur.id if not autbis else autbis,
                                                    "URL": url,
                                                    "TIMESTAMP": time.time(),
                                                    "COMPTAGE": 0,
                                                    "AFFICHAGE": "upload",
                                                    "IMPORT": importe,
                                                    "TAGS": tags}
                if "APPROB" not in self.stk[server.id]["OPT"]:
                    self.stk[server.id]["OPT"]["APPROB"] = {}
                if clef in self.stk[server.id]["OPT"]["APPROB"]:
                    del self.stk[server.id]["OPT"]["APPROB"][clef]
            else:
                self.stk[server.id]["OPT"]["APPROB"][clef] = {"NOM": nom,
                                                              "CHEMIN": chemin,
                                                              "AUTEUR": auteur.id,
                                                              "URL": url,
                                                              "TAGS": tags}
            self.save()
            return True
        return False

    # MEMEMAKER

    def make_meme(self, topString, bottomString, filename):

        img = Image.open(filename)
        imageSize = img.size

        fontSize = int(imageSize[1] / 5)
        font = ImageFont.truetype("/data/stickers/ressources/impact.ttf", fontSize)
        topTextSize = font.getsize(topString)
        bottomTextSize = font.getsize(bottomString)
        while topTextSize[0] > imageSize[0] - 20 or bottomTextSize[0] > imageSize[0] - 20:
            fontSize = fontSize - 1
            font = ImageFont.truetype("/data/stickers/ressources/impact.ttf", fontSize)
            topTextSize = font.getsize(topString)
            bottomTextSize = font.getsize(bottomString)

        topTextPositionX = (imageSize[0] / 2) - (topTextSize[0] / 2)
        topTextPositionY = 0
        topTextPosition = (topTextPositionX, topTextPositionY)

        bottomTextPositionX = (imageSize[0] / 2) - (bottomTextSize[0] / 2)
        bottomTextPositionY = (imageSize[1] - bottomTextSize[1]) / 1.005
        bottomTextPosition = (bottomTextPositionX, bottomTextPositionY)

        draw = ImageDraw.Draw(img)

        outlineRange = int(fontSize / 15)
        for x in range(-outlineRange, outlineRange + 1):
            for y in range(-outlineRange, outlineRange + 1):
                draw.text((topTextPosition[0] + x, topTextPosition[1] + y), topString, (0, 0, 0), font=font)
                draw.text((bottomTextPosition[0] + x, bottomTextPosition[1] + y), bottomString, (0, 0, 0), font=font)

        draw.text(topTextPosition, topString, (255, 255, 255), font=font)
        draw.text(bottomTextPosition, bottomString, (255, 255, 255), font=font)

        img.save("temp.png")

    def get_upper(self, somedata):
        '''
        Handle Python 2/3 differences in argv encoding
        '''
        result = ''
        try:
            result = somedata.decode("utf-8").upper()
        except:
            result = somedata.upper()
        return result

    def get_lower(self, somedata):
        '''
        Handle Python 2/3 differences in argv encoding
        '''
        result = ''
        try:
            result = somedata.decode("utf-8").lower()
        except:
            result = somedata.lower()

        return result

    if __name__ == '__main__':

        args_len = len(sys.argv)
        topString = ''
        meme = 'standard'

        if args_len == 1:
            # no args except the launch of the script
            print('args plz')

        elif args_len == 2:
            # only one argument, use standard meme
            bottomString = get_upper(sys.argv[-1])

        elif args_len == 3:
            # args give meme and one line
            bottomString = get_upper(sys.argv[-1])
            meme = get_lower(sys.argv[1])

        elif args_len == 4:
            # args give meme and two lines
            topString = get_upper(sys.argv[-2])
            bottomString = get_upper(sys.argv[-1])
            meme = get_lower(sys.argv[1])
        else:
            # so many args
            # what do they mean
            # too intense
            print('to many argz')

        print(meme)
        filename = str(meme) + '.jpg'
        make_meme(topString, bottomString, filename)

    @commands.command(pass_context=True)
    async def meme(self, ctx, dessus: str, dessous: str, url=None):
        """Créer un MEME !

        <dessus> = Message du dessus
        <dessous> = Message du dessous
        [url] = Optionnel, permet d'utiliser une image web
        Supporte l'upload à travers Discord"""
        channel = ctx.message.channel
        if not url:
            attach = ctx.message.attachments
            if len(attach) > 1:
                await self.bot.say("Vous ne pouvez ajouter qu'une seule image à la fois.")
                return
            if attach:
                a = attach[0]
                url = a["url"]
                filename = a["filename"]
            else:
                await self.bot.say("**Erreur** | Ce type de fichier n'est pas pris en charge.")
                return
            filepath = os.path.join("data/stickers/img/", filename)

            async with aiohttp.get(url) as new:
                f = open(filepath, "wb")
                f.write(await new.read())
                f.close()
            chemin = filepath
        else:
            if url.endswith("jpg") or url.endswith("gif") or url.endswith("png") or url.endswith("jpeg"):
                filename = url.split('/')[-1]
                if filename in os.listdir("data/stickers/img"):
                    exten = filename.split(".")[1]
                    nomsup = random.randint(1, 999999)
                    filename = filename.split(".")[0] + str(nomsup) + "." + exten
                try:
                    f = open(filename, 'wb')
                    f.write(request.urlopen(url).read())
                    f.close()
                    file = "data/stickers/img/" + filename
                    os.rename(filename, file)
                    chemin = file
                except Exception as e:
                    print("Impossible de télécharger une image : {}".format(e))
                    await self.bot.say(
                        "**Erreur** | Impossible de télécharger l'image - Essayez de changer l'hébergeur")
            else:
                await self.bot.say("**Erreur** | Ce format n'est pas supporté.")
        self.make_meme(dessus, dessous, chemin)
        try:
            await self.bot.send_file(channel, "temp.png")
            os.remove("temp.png")
            os.remove("data/stickers/img/{}".format(filename))
        except:
            print("ERREUR : Impossible de supprimer temp.png")

    @commands.group(name="stk", pass_context=True, no_pm=True)
    async def _stk(self, ctx):
        """Commandes de gestion des stickers"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_stk.command(pass_context=True)
    async def taille(self, ctx):
        """Renvoie la taille du fichier de stockage des stickers en bytes"""
        result = self.get_size("data/stickers/img/")
        await self.bot.say(str(result) + "B")

    def get_size(self, start_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    @_stk.command(pass_context=True)
    async def add(self, ctx, nom, url=None, *tags: str):
        """Ajouter un sticker

        <nom> = Nom de votre sticker
        [url] = Optionnel, permet de télécharger le sticker depuis un lien (Noelshack, Imgur ou Giphy)
        [tags] = Optionnel, permet d'ajouter des tags afin de simplifier la recherche
        Vous pouvez ajouter des tags sans mettre l'url en remplaçant celui-ci par
        Supporte l'upload d'image à travers Discord"""
        author = ctx.message.author
        server = ctx.message.server
        if server.id not in self.stk:
            self.stk[server.id] = {}
        if not tags: tags = []
        if url == "":
            url = None
        if nom not in self.list_stk(server):
            if author.server_permissions.manage_messages or grade == 3:
                msgplus = "**Sticker ajouté avec succès !** | Il est disponible avec :{}:".format(nom)
            else:
                msgplus = "**En attente d'approbation** | Un modérateur pourra approuver le sticker avec '&stk approb {}'".format(
                    nom)
            if not url:
                attach = ctx.message.attachments
                if len(attach) > 1:
                    await self.bot.say("Vous ne pouvez ajouter qu'une seule image à la fois.")
                    return
                if attach:
                    a = attach[0]
                    url = a["url"]
                    filename = a["filename"]
                else:
                    await self.bot.say("**Erreur** | Ce type de fichier n'est pas pris en charge.")
                    return
                filepath = os.path.join("data/stickers/img/", filename)
                clef = ''.join(
                    random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _
                    in
                    range(6))
                if clef in os.listdir("data/stickers/img/"):
                    await self.bot.reply("**Une erreur s'est produite lors du stockage de votre image** | "
                                         "Veuillez réessayer.")
                    return

                async with aiohttp.get(url) as new:
                    f = open(filepath, "wb")
                    f.write(await new.read())
                    f.close()
                self.add_sticker(clef, nom, filepath, author, url, tags=tags)
                await self.bot.say(msgplus)
                return
            else:
                if url.endswith("jpg") or url.endswith("gif") or url.endswith("png") or url.endswith("jpeg"):
                    filename = url.split('/')[-1]
                    if filename in os.listdir("data/stickers/img"):
                        exten = filename.split(".")[1]
                        nomsup = random.randint(1, 999999)
                        filename = filename.split(".")[0] + str(nomsup) + "." + exten
                    try:
                        f = open(filename, 'wb')
                        f.write(request.urlopen(url).read())
                        f.close()
                        file = "data/stickers/img/" + filename
                        os.rename(filename, file)
                        clef = ''.join(
                            random.SystemRandom().choice(
                                string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in
                            range(6))
                        self.add_sticker(clef, nom, file, author, url, tags=tags)
                        await self.bot.say(msgplus)
                        return
                    except Exception as e:
                        print("Impossible de télécharger une image : {}".format(e))
                        await self.bot.say(
                            "**Erreur** | Impossible de télécharger l'image - Essayez de changer l'hébergeur")
                else:
                    await self.bot.say("**Erreur** | Ce format n'est pas supporté.")
        else:
            await self.bot.say("**Indisponible** | Un sticker sous ce nom existe déjà !")

    @_stk.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def delete(self, ctx, nom):
        """Supprimer un sticker"""
        server = ctx.message.server
        if server.id not in self.stk:
            self.stk[server.id] = {}
        for r in self.stk[server.id]["STK"]:
            if self.stk[server.id]["STK"][r]["NOM"] == nom:
                chemin = self.stk[server.id]["STK"][r]["CHEMIN"]
                file = self.stk[server.id]["STK"][r]["CHEMIN"].split('/')[-1]
                splitted = "/".join(chemin.split('/')[:-1]) + "/"
                if file in os.listdir(splitted):
                    try:
                        os.remove(chemin)
                    except:
                        pass
                del self.stk[server.id]["STK"][r]
                self.save()
                await self.bot.say("**Succès** | Sticker supprimé avec succès.")
                return
        else:
            await self.bot.say("**Introuvable** | Le sticker ne semble pas exister.")

    def check(self, reaction, user):
        return not user.bot

    @commands.command(aliases=["rs"], pass_context=True)
    async def search(self, ctx, *termes: str):
        """Recherche dans les stickers

        Si aucun terme n'est rentré, renvoie une liste des stickers"""
        server = ctx.message.server
        if server.id not in self.stk:
            await self.bot.say("**Vide** | Ce serveur ne possède pas de stickers")
            return
        if not termes:
            msg = "**__Liste des stickers disponibles__**\n\n"
            n = 1
            listtot = [self.stk[server.id]["STK"][s]["NOM"] for s in self.stk[server.id]["STK"]]
            listtot.sort()
            for s in listtot:
                msg += "***{}***\n".format(s)
                if len(msg) > 1990 * n:
                    msg += "!!"
                    n += 1
            else:
                msglist = msg.split("!!")
                for m in msglist:
                    await self.bot.whisper(m)
        else:
            results = []
            if len(termes) == 1:
                tem = termes[0]
                for s in self.stk[server.id]["STK"]:
                    if tem in self.stk[server.id]["STK"][s]["NOM"]:
                        t = "**{}** (c)".format(self.stk[server.id]["STK"][s]["NOM"])
                        results.append(t)
            for t in termes:
                for s in self.stk[server.id]["STK"]:
                    if "TAGS" in self.stk[server.id]["STK"][s]:
                        if t in self.stk[server.id]["STK"][s]["TAGS"]:
                            b = "**{}** (t)".format(self.stk[server.id]["STK"][s]["NOM"])
                            results.append(b)
            msg = "__**Résultats**__\n"
            n = 1
            for i in results:
                msg += "{}\n".format(i)
                if len(msg) > 1990 * n:
                    msg += "!!"
                    n += 1
            else:
                msglist = msg.split("!!")
                for m in msglist:
                    await self.bot.whisper(m)

    @_stk.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def tag(self, ctx):
        """Permet de taguer des stickers qui ne le sont pas encore

        Ajouter des tags = meilleure recherche de stickers"""
        server = ctx.message.server
        if server.id not in self.stk:
            self.stk[server.id] = {}
        for s in self.stk[server.id]["STK"]:
            if "TAGS" not in self.stk[server.id]["STK"][s]:
                self.stk[server.id]["STK"][s]["TAGS"] = []
            if not self.stk[server.id]["STK"][s]["TAGS"]:
                em = discord.Embed(title="STK| Tagguer « {} »".format(self.stk[server.id]["STK"][s]["NOM"]),
                                   description="**Entrez les tags de ce sticker, séparés par des virgules (,)**\n"
                                               "- *Si l'image ne charge pas, passez avec 'pass'*\n"
                                               "- *Stoppez cette section avec 'stop' ou en ignorant ce message "
                                               "quelques secondes*")
                em.set_image(url=self.stk[server.id]["STK"][s]["URL"])
                em.set_footer(text="Tapez au moins un tag | Ex: animal,fun,cool,gif")
                m = await self.bot.whisper(embed=em)
                valid = False
                while valid is False:
                    rep = await self.bot.wait_for_message(channel=m.channel,
                                                          author=ctx.message.author,
                                                          timeout=60)
                    if rep is None:
                        em.set_footer(text="**Session annulée** | Bye :wave:")
                        await self.bot.edit_message(m, embed=em)
                        return
                    if rep.content.lower() == "pass":
                        valid = True
                        continue
                    elif rep.content.lower() == "stop":
                        await self.bot.whisper("**Session annulée** | Bye :wave:")
                        return

                    tags = rep.content.lower().split(",")
                    correcttags = []
                    for t in tags:
                        if t.startswith(" "):
                            t = t[1:]
                        if t.endswith(" "):
                            t = t[:-1]
                        correcttags.append(t)
                    tags = correcttags
                    if tags:
                        self.stk[server.id]["STK"][s]["TAGS"] = tags
                        self.save()
                        await self.bot.whisper("**Tags ajoutés** | Merci ! Au suivant...")
                        valid = True
                        continue
                    else:
                        await self.bot.say("**Erreur** | Il faut au moins un tag...")
        else:
            await self.bot.say("**Complet** | Il semblerait que tous les stickers soient déjà taggués. Merci !")

    @_stk.command(aliases=["approuve"], pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def approb(self, ctx, nom: str = None):
        """Accorder l'approbation du staff sur des sticker"""
        author = ctx.message.author
        server = ctx.message.server
        if server.id not in self.stk:
            self.stk[server.id] = {}
        if nom == "fullreset":
            self.stk[server.id]["OPT"]["APPROB"] = {}
            self.save()
            await self.bot.say("**Succès** | Le reset total des stickers en approbation a été réalisé")
            return
        if not nom:
            msg = "\n".join(
                [self.stk[server.id]["OPT"]["APPROB"][r]["NOM"] for r in self.stk[server.id]["OPT"]["APPROB"]])
            em = discord.Embed(title="STK| En attente d'approbation", description=msg, color=0x7af442)
            em.set_footer(text="Faîtes '&stk approb <nom>' pour voir un sticker en détail.")
            await self.bot.say(embed=em)
        else:
            if nom in [self.stk[server.id]["OPT"]["APPROB"][r]["NOM"] for r in self.stk[server.id]["OPT"]["APPROB"]]:
                tr = self.get_stk_opt(server, nom)
                pseudo = server.get_member(self.stk[server.id]["OPT"]["APPROB"][tr]["AUTEUR"])
                if not pseudo:
                    pseudo = "???"
                else:
                    pseudo = pseudo.name
                em = discord.Embed(title="STK| {} - par {}".format(self.stk[server.id]["OPT"]["APPROB"][tr]["NOM"],
                                                                   pseudo), color=0x7af442)
                em.set_image(url=self.stk[server.id]["OPT"]["APPROB"][tr]["URL"])
                em.set_footer(text="Acceptez-vous ce sticker ?")
                menu = await self.bot.say(embed=em)
                await self.bot.add_reaction(menu, "✔")
                await self.bot.add_reaction(menu, "✖")
                await asyncio.sleep(0.25)
                rep = await self.bot.wait_for_reaction(["✔", "✖"], message=menu, timeout=30,
                                                       check=self.check)
                if rep is None:
                    await self.bot.say("**TIMEOUT** | Bye :wave:")
                    return
                elif rep.reaction.emoji == "✔":
                    self.add_sticker(tr, self.stk[server.id]["OPT"]["APPROB"][tr]["NOM"],
                                     self.stk[server.id]["OPT"]["APPROB"][tr]["CHEMIN"],
                                     author,
                                     self.stk[server.id]["OPT"]["APPROB"][tr]["URL"],
                                     autbis=self.stk[server.id]["OPT"]["APPROB"][tr]["AUTEUR"],
                                     tags=self.stk[server.id]["OPT"]["APPROB"][tr]["TAGS"])
                    await self.bot.say("**Sticker approuvé !**")
                    await asyncio.sleep(1)
                else:
                    del self.stk[server.id]["OPT"]["APPROB"][tr]
                    await self.bot.say("**Sticker refusé !**")
                    self.save()
            else:
                await self.bot.say("**Introuvable** | Ce sticker n'existe pas, vérifiez l'orthographe.")

    @_stk.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def edit(self, ctx, nom):
        """Editer un sticker : Nom, Url, Affichage..."""
        server = ctx.message.server
        if server.id not in self.stk:
            self.stk[server.id] = {}
        for r in self.stk[server.id]["STK"]:
            if nom == self.stk[server.id]["STK"][r]["NOM"]:
                stk = self.stk[server.id]["STK"][r]
                if "TAGS" not in self.stk[server.id]["STK"][r]:
                    self.stk[server.id]["STK"][r]["TAGS"] = []
                while True:
                    txt = "1/**Nom:** {}\n" \
                          "2/**URL:** {}\n" \
                          "3/**Affichage:** {}\n" \
                          "4/**Tags:** {}".format(stk["NOM"], stk["URL"], stk["AFFICHAGE"], stk["TAGS"])
                    em = discord.Embed(title="STK| Modifier {}".format(r), description=txt)
                    em.set_image(url=stk["URL"])
                    em.set_footer(text="Tapez le chiffre correspondant à l'action désirée | Q pour quitter")
                    m = await self.bot.say(embed=em)
                    valid = False
                    while valid is False:
                        rep = await self.bot.wait_for_message(channel=ctx.message.channel, author=ctx.message.author,
                                                              timeout=30)
                        if rep is None:
                            em.set_footer(text="TIMEOUT | Bye !")
                            await self.bot.edit_message(m, embed=em)
                            return
                        elif rep.content.lower() == "q":
                            em.set_footer(text="ANNULATION | Bye !")
                            await self.bot.edit_message(m, embed=em)
                            return
                        elif rep.content == "1":
                            em = discord.Embed(title="STK| Modifier {} > Nom".format(r),
                                               description="**Quel nom voulez-vous lui donner ?**")
                            em.set_footer(text="Il est déconseillé de mettre un espace dans le nom | "
                                               "Majuscules supportées")
                            m = await self.bot.say(embed=em)
                            valid = False
                            while valid is False:
                                rep = await self.bot.wait_for_message(channel=ctx.message.channel,
                                                                      author=ctx.message.author,
                                                                      timeout=60)
                                if rep is None:
                                    em.set_footer(text="TIMEOUT | Bye !")
                                    await self.bot.edit_message(m, embed=em)
                                    return
                                else:
                                    self.stk[server.id]["STK"][r]["NOM"] = rep.content
                                    self.save()
                                    await self.bot.say("**Modifié** | Retour au menu...")
                                    valid = True
                        elif rep.content == "2":
                            em = discord.Embed(title="STK| Modifier {} > URL".format(r),
                                               description="**Copiez ici l'URL désirée**")
                            em.set_footer(text="Formats supportés : png, jpg, jpeg, gif")
                            m = await self.bot.say(embed=em)
                            valid = False
                            while valid is False:
                                rep = await self.bot.wait_for_message(channel=ctx.message.channel,
                                                                      author=ctx.message.author,
                                                                      timeout=60)
                                if rep is None:
                                    em.set_footer(text="TIMEOUT | Bye !")
                                    await self.bot.edit_message(m, embed=em)
                                    return
                                elif rep.content.startswith("http"):
                                    self.stk[server.id]["STK"][r]["URL"] = rep.content
                                    self.save()
                                    await self.bot.say("**Modifiée** | Retour au menu...")
                                    valid = True
                                else:
                                    await self.bot.say("**Erreur** | Ce n'est pas une url.")
                        elif rep.content == "3":
                            em = discord.Embed(title="STK| Modifier {} > Affichage".format(r),
                                               description="**Ecrivez le format désiré**")
                            em.set_footer(text="Formats supportés : 'web', 'upload', 'billet'")
                            m = await self.bot.say(embed=em)
                            valid = False
                            while valid is False:
                                rep = await self.bot.wait_for_message(channel=ctx.message.channel,
                                                                      author=ctx.message.author,
                                                                      timeout=60)
                                if rep is None:
                                    em.set_footer(text="TIMEOUT | Bye !")
                                    await self.bot.edit_message(m, embed=em)
                                    return
                                elif rep.content.lower() in ['web', 'upload', 'billet']:
                                    self.stk[server.id]["STK"][r]["AFFICHAGE"] = rep.content.lower()
                                    self.save()
                                    await self.bot.say("**Modifiée** | Retour au menu...")
                                    valid = True
                                else:
                                    await self.bot.say("**Erreur** | Ce format n'existe pas (web, upload ou billet)")
                        elif rep.content == "4":
                            em = discord.Embed(title="STK| Modifier {} > Tags".format(r),
                                               description="**Tapez ci-dessous les tags, séparés par une virgule (,)**")
                            em.set_footer(text="Tapez au minimum un tag | Ex: fun,cool,animal,chat")
                            m = await self.bot.say(embed=em)
                            valid = False
                            while valid is False:
                                rep = await self.bot.wait_for_message(channel=ctx.message.channel,
                                                                      author=ctx.message.author,
                                                                      timeout=60)
                                if rep.content:
                                    tags = rep.content.lower().split(",")
                                    correcttags = []
                                    for t in tags:
                                        if t.startswith(" "):
                                            t = t[1:]
                                        if t.endswith(" "):
                                            t = t[:-1]
                                        correcttags.append(t)
                                    tags = correcttags
                                if rep.content is None:
                                    em.set_footer(text="TIMEOUT | Bye !")
                                    await self.bot.edit_message(m, embed=em)
                                    return
                                elif tags:
                                    self.stk[server.id]["STK"][r]["TAGS"] = tags
                                    self.save()
                                    await self.bot.say("**Modifiés** | Retour au menu...")
                                    valid = True
                                else:
                                    await self.bot.say("**Erreur** | Il faut au moins un tag...")
                        else:
                            await self.bot.say("**Erreur** | Cette option n'existe pas")
        else:
            await self.bot.say("**Introuvable** | Je n'ai pas trouvé ce sticker.")

    async def stkmsg(self, message):
        author = message.author
        server = message.server
        channel = message.channel
        if author.id in self.user:
            if "STK_STOP" in self.user[author.id]:
                if self.user[author.id]["STK_STOP"]:
                    return
        else:
            self.user[author.id] = {"STK_STOP": False}
        nb = 0
        if not server.id in self.stk:
            return
        if ":" in message.content:
            output = re.compile(':(.*?):', re.DOTALL | re.IGNORECASE).findall(message.content)
            if output:
                for stk in output:
                    if stk in [e.name for e in server.emojis]:
                        continue
                    if nb > 3:
                        await self.bot.send_message(author, "**Ne spammez pas les stickers SVP.**")
                        return
                    nb += 1
                    img = {"NOM": None,
                           "CHEMIN": None,
                           "URL": None,
                           "AFFICHAGE": None,
                           "CONTENANT": False,
                           "SECRET": False,
                           "TAGS": False}
                    tags = []
                    if "/" in stk:
                        tr = stk.split("/")[1]
                        pr = stk.split("/")[0]
                        if "w" in pr:
                            img["AFFICHAGE"] = "web"
                        elif "u" in pr:
                            img["AFFICHAGE"] = "upload"
                        elif "b" in pr:
                            img["AFFICHAGE"] = "billet"
                        elif "i" in pr:
                            img["AFFICHAGE"] = "infos"
                        else:
                            pass
                        if "s" in pr:
                            img["SECRET"] = True
                        if "?" in pr:
                            img["CONTENANT"] = True
                        elif "t" in pr:
                            img["TAGS"] = True
                            tags = tr.split(",")
                            correcttags = []
                            for t in tags:
                                if t.startswith(" "):
                                    t = t[1:]
                                if t.endswith(" "):
                                    t = t[:-1]
                                correcttags.append(t)
                            tags = correcttags
                            tr = ""
                    else:
                        tr = stk
                    if tr == "list" or tr == "liste":
                        msg = "**__Liste des stickers disponibles__**\n\n"
                        n = 1
                        listtot = [self.stk[server.id]["STK"][s]["NOM"] for s in self.stk[server.id]["STK"]]
                        listtot.sort()
                        for s in listtot:
                            msg += "***{}***\n".format(s)
                            if len(msg) > 1980 * n:
                                msg += "!!"
                                n += 1
                        else:
                            msglist = msg.split("!!")
                            for m in msglist:
                                await self.bot.send_message(author, m)
                            continue
                    if tr == "vent":  # EE
                        await asyncio.sleep(0.10)
                        await self.bot.send_typing(channel)
                        return
                    if img["TAGS"]:
                        tot = []
                        for s in self.stk[server.id]["STK"]:
                            if "TAGS" in self.stk[server.id]["STK"][s]:
                                for t in tags:
                                    if t.lower() in self.stk[server.id]["STK"][s]["TAGS"]:
                                        tot.append(self.stk[server.id]["STK"][s]["NOM"])
                        tr = random.choice(tot)
                    if img["CONTENANT"] is False:
                        if tr in self.list_stk(server):
                            for r in self.stk[server.id]["STK"]:
                                if tr == self.stk[server.id]["STK"][r]["NOM"]:
                                    img["NOM"] = self.stk[server.id]["STK"][r]["NOM"]
                                    img["CHEMIN"] = self.stk[server.id]["STK"][r]["CHEMIN"]
                                    img["URL"] = self.stk[server.id]["STK"][r]["URL"]
                                    self.stk[server.id]["STK"][r]["COMPTAGE"] += 1
                                    self.save()
                                    if img["AFFICHAGE"] is None:
                                        img["AFFICHAGE"] = self.stk[server.id]["STK"][r]["AFFICHAGE"]
                        else:
                            continue
                    else:
                        rd = []
                        for r in self.stk[server.id]["STK"]:
                            if tr in self.stk[server.id]["STK"][r]["NOM"]:
                                rd.append(r)
                        if rd:
                            r = random.choice(rd)
                            img["NOM"] = self.stk[server.id]["STK"][r]["NOM"]
                            img["CHEMIN"] = self.stk[server.id]["STK"][r]["CHEMIN"]
                            img["URL"] = self.stk[server.id]["STK"][r]["URL"]
                            self.stk[server.id]["STK"][r]["COMPTAGE"] += 1
                            self.save()
                            if img["AFFICHAGE"] is None:
                                img["AFFICHAGE"] = self.stk[server.id]["STK"][r]["AFFICHAGE"]

                    if img["SECRET"]:
                        try:
                            await self.bot.delete_message(message)
                        except:
                            print("Impossible de supprimer le message, l'auteur est mon supérieur")
                    if img["AFFICHAGE"] == 'billet':
                        em = discord.Embed(color=author.color)
                        em.set_image(url=img["URL"])
                        try:
                            await self.bot.send_typing(channel)
                            await self.bot.send_message(channel, embed=em)
                        except:
                            print("L'URL de :{}: est indisponible. Je ne peux pas l'envoyer. (Format: billet)"
                                  "".format(img["NOM"]))
                    elif img["AFFICHAGE"] == 'infos':
                        for r in self.stk[server.id]["STK"]:
                            if tr == self.stk[server.id]["STK"][r]["NOM"]:
                                tr = r
                                txt = "**Importé depuis la V3**" if self.stk[server.id]["STK"][tr][
                                    "IMPORT"] else "**Ajouté par** <@{}>".format(
                                    self.stk[server.id]["STK"][tr]["AUTEUR"])
                                if "TAGS" in self.stk[server.id]["STK"][tr]:
                                    txt += "\nTags: *Aucun tags*" if not self.stk[server.id]["STK"][tr]["TAGS"] else \
                                        "\nTags: *{}*".format(", ".join(self.stk[server.id]["STK"][tr]["TAGS"]))
                                em = discord.Embed(title=img["NOM"], description=txt, color=author.color)
                                em.set_image(url=img["URL"])
                                em.set_footer(text="Invoqué {} fois".format(self.stk[server.id]["STK"][tr]["COMPTAGE"]))
                                await self.bot.send_typing(channel)
                                await self.bot.send_message(channel, embed=em)
                        else:
                            continue
                    elif img["AFFICHAGE"] == 'upload':
                        try:
                            await self.bot.send_typing(channel)
                            await self.bot.send_file(channel, img["CHEMIN"])
                        except:
                            print(
                                "Le fichier de :{}: n'existe plus ou n'a jamais existé. Je ne peux pas l'envoyer. "
                                "(Format: upload)\nJe vais envoyer l'URL liée à la place...".format(img["NOM"]))
                            try:  # En cas que l'upload fail, on envoie l'URL brute
                                await self.bot.send_message(channel, img["URL"])
                            except:
                                print("L'URL de :{}: est indisponible. Je ne peux pas l'envoyer. (Format: web)"
                                      "".format(img["NOM"]))
                    else:
                        try:
                            await self.bot.send_typing(channel)
                            await self.bot.send_message(channel, img["URL"])
                        except:
                            print("L'URL de :{}: est indisponible. Je ne peux pas l'envoyer. (Format: web/defaut)"
                                  "".format(img["NOM"]))


def check_folders():
    if not os.path.exists("data/stickers"):
        print("Création du dossier Stickers...")
        os.makedirs("data/stickers")
    if not os.path.exists("data/stickers/img"):
        print("Création du dossier d'Images Stickers...")
        os.makedirs("data/stickers/img")
    if not os.path.exists("data/stickers/ressources"):
        print("Création du dossier de ressources Stickers...")
        os.makedirs("data/stickers/ressources")


def check_files():
    if not os.path.isfile("data/stickers/stk.json"):
        print("Création du fichier Stickers/stk.json...")
        fileIO("data/stickers/stk.json", "save", {"OPT": {}, "STK": {}})
    if not os.path.isfile("data/stickers/user.json"):
        print("Création du fichier Stickers/user.json...")
        fileIO("data/stickers/user.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Stickers(bot)
    bot.add_cog(n)
    bot.add_listener(n.stkmsg, "on_message")
