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

class Systex:
    """Gestion des stickers et autres fonctions à l'écrit | Corrigé"""
    def __init__(self, bot):
        self.bot = bot
        self.stk = dataIO.load_json("data/systex/stk.json")
        self.user = dataIO.load_json("data/systex/user.json")
        self.app = self.bot.get_cog('Prism').app
        self.cycle_task = bot.loop.create_task(self.systex_loop())

    def save(self):
        fileIO("data/systex/stk.json", "save", self.stk)
        fileIO("data/systex/user.json", "save", self.user)
        return True

    def list_stk(self):
        lst = [self.stk["STK"][e]["NOM"] for e in self.stk["STK"]]
        return lst

    @commands.command(pass_context=True, hidden=True)
    async def sysprism(self):
        """Permet de s'assurer de la connexion entre Systex et Prism"""

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

    def get_stk(self, nom):
        for n in self.stk["STK"]:
            if nom == self.stk["STK"][n]["NOM"]:
                return n
        else:
            return False

    def get_stk_opt(self, nom):
        for n in self.stk["OPT"]["APPROB"]:
            if nom == self.stk["OPT"]["APPROB"][n]["NOM"]:
                return n
        else:
            return False

    def add_sticker(self, clef, nom: str, chemin, auteur: discord.Member, url, autbis=None, importe=None,
                    tags=None):
        if tags is None: tags = []
        grade = self.app.grade(auteur)[2]
        if clef not in self.stk:
            autorise = False if not auteur.server_permissions.manage_messages or grade < 3 else True
            if autorise:
                self.stk["STK"][clef] = {"NOM": nom,
                                         "CHEMIN": chemin,
                                         "AUTEUR": auteur.id if not autbis else autbis,
                                         "URL": url,
                                         "TIMESTAMP": time.time(),
                                         "COMPTAGE": 0,
                                         "AFFICHAGE": "upload",
                                         "IMPORT": importe,
                                         "TAGS": tags}
                if "APPROB" not in self.stk["OPT"]:
                    self.stk["OPT"]["APPROB"] = {}
                if clef in self.stk["OPT"]["APPROB"]:
                    del self.stk["OPT"]["APPROB"][clef]
            else:
                self.stk["OPT"]["APPROB"][clef] = {"NOM": nom,
                                                   "CHEMIN": chemin,
                                                   "AUTEUR": auteur.id,
                                                   "URL": url,
                                                   "TAGS": tags}
            self.save()
            return True
        return False

    async def systex_loop(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(10)  # Temps de mise en route
            channel = self.bot.get_channel("228154509946388480")
            while True:
                if "RAPPEL" not in self.stk["OPT"]:
                    self.stk["OPT"]["RAPPEL"] = False
                    self.save()
                if self.stk["OPT"]["RAPPEL"]:
                    if self.stk["OPT"]["APPROB"]:
                        await self.bot.send_message(channel, "@Modérateur **Rappel** | Des stickers sont en "
                                                             "attente approbation")
                await asyncio.sleep(86400)
        except asyncio.CancelledError:
            pass


    #MEMEMAKER

    def make_meme(self, topString, bottomString, filename):

        img = Image.open(filename)
        imageSize = img.size

        fontSize = int(imageSize[1] / 5)
        font = ImageFont.truetype("/data/systex/ressources/impact.ttf", fontSize)
        topTextSize = font.getsize(topString)
        bottomTextSize = font.getsize(bottomString)
        while topTextSize[0] > imageSize[0] - 20 or bottomTextSize[0] > imageSize[0] - 20:
            fontSize = fontSize - 1
            font = ImageFont.truetype("/data/systex/ressources/impact.ttf", fontSize)
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
            filepath = os.path.join("data/systex/img/", filename)

            async with aiohttp.get(url) as new:
                f = open(filepath, "wb")
                f.write(await new.read())
                f.close()
            chemin = filepath
        else:
            if url.endswith("jpg") or url.endswith("gif") or url.endswith("png") or url.endswith("jpeg"):
                filename = url.split('/')[-1]
                if filename in os.listdir("data/systex/img"):
                    exten = filename.split(".")[1]
                    nomsup = random.randint(1, 999999)
                    filename = filename.split(".")[0] + str(nomsup) + "." + exten
                try:
                    f = open(filename, 'wb')
                    f.write(request.urlopen(url).read())
                    f.close()
                    file = "data/systex/img/" + filename
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
            os.remove("data/systex/img/{}".format(filename))
        except:
            print("ERREUR : Impossible de supprimer temp.png")

    @commands.group(name="stkmod", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def _stkmod(self, ctx):
        """Commandes de gestion des stickers"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_stkmod.command()
    async def stop(self, user: discord.Member):
        """Interdir/autoriser un utilisateur à utiliser les stickers"""
        if user.id not in self.user:
            self.user[user.id] = {}
        if "STK_STOP" not in self.user[user.id]:
            self.user[user.id]["STK_STOP"] = False
        if self.user[user.id]["STK_STOP"]:
            self.user[user.id]["STK_STOP"] = False
            self.save()
            await self.bot.say("**L'utilisateur est maintenant autorisé à utiliser des stickers**")
        else:
            self.user[user.id]["STK_STOP"] = True
            self.save()
            await self.bot.say("**L'utilisateur n'a plus le droit d'utiliser des stickers**")

    @_stkmod.command()
    async def rappel(self):
        """Active/Désactive le rappel d'approbation des stickers en attente"""
        if "RAPPEL" not in self.stk["OPT"]:
            self.stk["OPT"]["RAPPEL"] = False
        if self.stk["OPT"]["RAPPEL"]:
            self.stk["OPT"]["RAPPEL"] = False
            await self.bot.say("**Rappel désactivé**")
        else:
            self.stk["OPT"]["RAPPEL"] = True
            await self.bot.say("**Rappel activé**")
        self.save()

    @_stkmod.command()
    async def customstop(self, user: discord.Member):
        """Interdir/autoriser l'utilisateur de faire un sticker customisé

        Cette commande retire le sticker custom de l'utilisateur si il en a un."""
        if user.id not in self.user:
            self.user[user.id] = {}
        if "STK_CUSTOM" not in self.user[user.id]:
            self.user[user.id]["STK_CUSTOM"] = None
        if self.user[user.id]["STK_CUSTOM"] or self.user[user.id]["STK_CUSTOM"] is None:
            self.user[user.id]["STK_CUSTOM"] = False
            self.save()
            await self.bot.say("**L'utilisateur ne peut plus utiliser de sticker custom**")
        else:
            self.user[user.id]["STK_CUSTOM"] = None
            self.save()
            await self.bot.say("**L'utilisateur peut de nouveau utiliser un sticker custom**")

    @_stkmod.command(pass_context=True, hidden=True)
    async def reimport(self, ctx):
        """Réimporte tous les anciens stickers et remplace ceux ayant le même nom

        !!! A vos risques et périls !!!"""
        await self.bot.say("**Fonctionnalité bloquée !**")
        return
        nb = 0
        for s in self.old["STICKERS"]:
            nom = s
            url = self.old["STICKERS"][s]["URL"]
            chemin = self.old["STICKERS"][s]["CHEMIN"]
            format = 'web'
            clef = ''.join(
                random.SystemRandom().choice(
                    string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in
                range(6))
            filename = chemin.split('/')[-1]
            file = "data/systex/img/" + filename
            try:
                os.rename(chemin, file)
            except:
                filename = url.split('/')[-1]
                if filename in os.listdir("data/systex/img"):
                    exten = filename.split(".")[1]
                    nomsup = random.randint(1, 999999)
                    filename = filename.split(".")[0] + str(nomsup) + "." + exten
                try:
                    f = open(filename, 'wb')
                    f.write(request.urlopen(url).read())
                    f.close()
                    file = "data/systex/img/" + filename
                    os.rename(filename, file)
                except:
                    pass
            chemin = file
            self.add_sticker(clef, nom, chemin, ctx.message.author, url, importe=True)
            nb += 1
        self.save()
        await self.bot.say("**{} stickers ont été transférés avec succès**".format(nb))

    @commands.group(name="stk", pass_context=True, no_pm=True)
    async def _stk(self, ctx):
        """Commandes de gestion des stickers"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_stk.command(pass_context=True)
    async def taille(self, ctx):
        """Renvoie la taille du fichier de stockage des stickers en bytes"""
        result = self.get_size("data/systex/img/")
        await self.bot.say(str(result) + "B")

    def get_size(self, start_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    @_stk.command(pass_context=True)
    async def custom(self, ctx, url):
        """Modifier son sticker :custom:

        URL Seulement"""
        user = ctx.message.author
        if user.id not in self.user:
            self.user[user.id] = {}
        if "STK_CUSTOM" not in self.user[user.id]:
            self.user[user.id]["STK_CUSTOM"] = None
        if url.startswith("http"):
            if not self.user[user.id]["STK_CUSTOM"]:
                await self.bot.say("**Sticker custom modifié avec succès !**")
                self.user[user.id]["STK_CUSTOM"] = url
                self.save()
            else:
                await self.bot.say("**Vous n'avez pas le droit de mettre un sticker customisé**")
        else:
            await self.bot.say("**Ceci n'est pas une URL valide**")

    @_stk.command(pass_context=True)
    async def correct(self, ctx, tolerance:int):
        """Permet de régler la tolérance de la correction automatique des stickers (0-3)
        0 = Désactivé
        1 = Faible
        2 = Moyenne
        3 = Elevée"""
        user = ctx.message.author
        if user.id not in self.user:
            self.user[user.id] = {}
        if "STK_TOL" not in self.user[user.id]:
            self.user[user.id]["STK_TOL"] = 0
        if 0 <= tolerance <= 3:
            txt = "**Tolérance de correction reglée à {}**".format(tolerance) if tolerance > 0 else "**Correction désactivée**"
            await self.bot.say(txt)
            self.user[user.id]["STK_TOL"] = tolerance
            self.save()
        else:
            await self.bot.say("**Le chiffre doit être compris entre 0 et 3**")

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
        if not tags: tags = []
        if url == "":
            url = None
        if nom not in self.list_stk():
            if author.server_permissions.manage_messages:
                msgplus = "**Sticker ajouté avec succès !** | Il est disponible avec :{}:".format(nom)
            else:
                msgplus = "**En attente d'approbation** | Un modérateur pourra approuver le sticker avec '&stk approb {}'".format(nom)
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
                filepath = os.path.join("data/systex/img/", filename)
                clef = ''.join(
                    random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in
                    range(6))
                if clef in os.listdir("data/systex/img/"):
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
                    if filename in os.listdir("data/systex/img"):
                        exten = filename.split(".")[1]
                        nomsup = random.randint(1, 999999)
                        filename = filename.split(".")[0] + str(nomsup) + "." + exten
                    try:
                        f = open(filename, 'wb')
                        f.write(request.urlopen(url).read())
                        f.close()
                        file = "data/systex/img/" + filename
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
        author = ctx.message.author
        for r in self.stk["STK"]:
            if self.stk["STK"][r]["NOM"] == nom:
                chemin = self.stk["STK"][r]["CHEMIN"]
                file = self.stk["STK"][r]["CHEMIN"].split('/')[-1]
                splitted = "/".join(chemin.split('/')[:-1]) + "/"
                if file in os.listdir(splitted):
                    try:
                        os.remove(chemin)
                    except:
                        pass
                del self.stk["STK"][r]
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
        author = ctx.message.author
        if not termes:
            msg = "**__Liste des stickers disponibles__**\n\n"
            n = 1
            listtot = [self.stk["STK"][s]["NOM"] for s in self.stk["STK"]]
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
                for s in self.stk["STK"]:
                    if tem in self.stk["STK"][s]["NOM"]:
                        t = "**{}** (c)".format(self.stk["STK"][s]["NOM"])
                        results.append(t)
            for t in termes:
                for s in self.stk["STK"]:
                    if "TAGS" in self.stk["STK"][s]:
                        if t in self.stk["STK"][s]["TAGS"]:
                            b = "**{}** (t)".format(self.stk["STK"][s]["NOM"])
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
        for s in self.stk["STK"]:
            if "TAGS" not in self.stk["STK"][s]:
                self.stk["STK"][s]["TAGS"] = []
            if not self.stk["STK"][s]["TAGS"]:
                em = discord.Embed(title="STK| Tagguer « {} »".format(self.stk["STK"][s]["NOM"]),
                                   description="**Entrez les tags de ce sticker, séparés par des virgules (,)**\n"
                                               "- *Si l'image ne charge pas, passez avec 'pass'*\n"
                                               "- *Stoppez cette section avec 'stop' ou en ignorant ce message "
                                               "quelques secondes*")
                em.set_image(url=self.stk["STK"][s]["URL"])
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
                        self.stk["STK"][s]["TAGS"] = tags
                        self.save()
                        await self.bot.whisper("**Tags ajoutés** | Merci ! Au suivant...")
                        valid = True
                        continue
                    else:
                        await self.bot.say("**Erreur** | Il faut au moins un tag...")
        else:
            await self.bot.say("**Complet** | Il semblerait que tous les stickers soient déjà taggués. Merci !")

    @commands.command(pass_context=True)
    async def pepe(self, ctx):
        """Génère un Pepe aléatoirement"""
        channel = ctx.message.channel
        chemin = os.listdir("data/systex/pepeimg/")
        chemin = "data/systex/pepeimg/" + random.choice(chemin)
        await self.bot.send_typing(channel)
        await self.bot.send_file(channel, chemin)

    @_stk.command(aliases=["approuve"], pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def approb(self, ctx, nom: str= None):
        """Accorder l'approbation du staff sur des sticker"""
        author = ctx.message.author
        server = ctx.message.server
        if nom == "fullreset":
            self.stk["OPT"]["APPROB"] = {}
            self.save()
            await self.bot.say("**Succès** | Le reset total des stickers en approbation a été réalisé")
            return
        if not nom:
            msg = "\n".join([self.stk["OPT"]["APPROB"][r]["NOM"] for r in self.stk["OPT"]["APPROB"]])
            em = discord.Embed(title="STK| En attente d'approbation", description=msg, color=0x7af442)
            em.set_footer(text="Faîtes '&stk approb <nom>' pour voir un sticker en détail.")
            await self.bot.say(embed=em)
        else:
            if nom in [self.stk["OPT"]["APPROB"][r]["NOM"] for r in self.stk["OPT"]["APPROB"]]:
                tr = self.get_stk_opt(nom)
                pseudo = server.get_member(self.stk["OPT"]["APPROB"][tr]["AUTEUR"])
                if not pseudo:
                    pseudo = "???"
                else:
                    pseudo = pseudo.name
                em = discord.Embed(title="STK| {} - par {}".format(self.stk["OPT"]["APPROB"][tr]["NOM"],
                                                                   pseudo), color=0x7af442)
                em.set_image(url=self.stk["OPT"]["APPROB"][tr]["URL"])
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
                    self.add_sticker(tr, self.stk["OPT"]["APPROB"][tr]["NOM"],
                                     self.stk["OPT"]["APPROB"][tr]["CHEMIN"],
                                     author,
                                     self.stk["OPT"]["APPROB"][tr]["URL"],
                                     autbis=self.stk["OPT"]["APPROB"][tr]["AUTEUR"],
                                     tags=self.stk["OPT"]["APPROB"][tr]["TAGS"])
                    await self.bot.say("**Sticker approuvé !**")
                    await asyncio.sleep(1)
                else:
                    del self.stk["OPT"]["APPROB"][tr]
                    await self.bot.say("**Sticker refusé !**")
                    self.save()
            else:
                await self.bot.say("**Introuvable** | Ce sticker n'existe pas, vérifiez l'orthographe.")

    @_stk.command(pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def edit(self, ctx, nom):
        """Editer un sticker : Nom, Url, Affichage..."""
        for r in self.stk["STK"]:
            if nom == self.stk["STK"][r]["NOM"]:
                stk = self.stk["STK"][r]
                if "TAGS" not in self.stk["STK"][r]:
                    self.stk["STK"][r]["TAGS"] = []
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
                                    self.stk["STK"][r]["NOM"] = rep.content
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
                                    self.stk["STK"][r]["URL"] = rep.content
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
                                    self.stk["STK"][r]["AFFICHAGE"] = rep.content.lower()
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
                                    self.stk["STK"][r]["TAGS"] = tags
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
        content = message.content
        server = message.server
        channel = message.channel
        if author.id in self.user:
            if "STK_STOP" in self.user[author.id]:
                if self.user[author.id]["STK_STOP"]:
                    return
        else:
            self.user[author.id] = {"STK_STOP": False}
        nb = 0
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
                            listtot = [self.stk["STK"][s]["NOM"] for s in self.stk["STK"]]
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
                    if tr == "vent": #EE
                        await asyncio.sleep(0.10)
                        await self.bot.send_typing(channel)
                        return
                    if tr == "halloween":
                        chemin = os.listdir("data/systex/halimg/")
                        chemin = "data/systex/halimg/" + random.choice(chemin)
                        await self.bot.send_typing(channel)
                        await self.bot.send_file(channel, chemin)
                        return #Restes de l'event Halloween 2017
                    if img["TAGS"]:
                        tot = []
                        for s in self.stk["STK"]:
                            if "TAGS" in self.stk["STK"][s]:
                                for t in tags:
                                    if t.lower() in self.stk["STK"][s]["TAGS"]:
                                        tot.append(self.stk["STK"][s]["NOM"])
                        tr = random.choice(tot)
                    if img["CONTENANT"] is False:
                        if tr in self.list_stk():
                            for r in self.stk["STK"]:
                                if tr == self.stk["STK"][r]["NOM"]:
                                    img["NOM"] = self.stk["STK"][r]["NOM"]
                                    img["CHEMIN"] = self.stk["STK"][r]["CHEMIN"]
                                    img["URL"] = self.stk["STK"][r]["URL"]
                                    self.stk["STK"][r]["COMPTAGE"] += 1
                                    self.save()
                                    if img["AFFICHAGE"] is None:
                                        img["AFFICHAGE"] = self.stk["STK"][r]["AFFICHAGE"]
                        else:
                            if author.id in self.user:
                                if "STK_TOL" in self.user[author.id]:
                                    if self.user[author.id]["STK_TOL"] > 0:
                                        liste = []
                                        for s in self.list_stk():
                                            liste.append(s)
                                        found = self.similarite(stk, liste, self.user[author.id]["STK_TOL"])
                                        found = self.get_stk(found)
                                        img["CHEMIN"] = self.stk["STK"][found]["CHEMIN"]
                                        img["URL"] = self.stk["STK"][found]["URL"]
                                        img["NOM"] = self.stk["STK"][found]["NOM"]
                                        self.stk["STK"][found]["COMPTAGE"] += 1
                                        self.save()
                                        if img["AFFICHAGE"] is None:
                                            img["AFFICHAGE"] = self.stk["STK"][found]["AFFICHAGE"]
                                    else:
                                        continue
                                else:
                                    continue
                            else:
                                continue
                    else:
                        rd = []
                        for r in self.stk["STK"]:
                            if tr in self.stk["STK"][r]["NOM"]:
                                rd.append(r)
                        if rd:
                            r = random.choice(rd)
                            img["NOM"] = self.stk["STK"][r]["NOM"]
                            img["CHEMIN"] = self.stk["STK"][r]["CHEMIN"]
                            img["URL"] = self.stk["STK"][r]["URL"]
                            self.stk["STK"][r]["COMPTAGE"] += 1
                            self.save()
                            if img["AFFICHAGE"] is None:
                                img["AFFICHAGE"] = self.stk["STK"][r]["AFFICHAGE"]
                    if tr == "custom":
                        if author.id in self.user:
                            if "STK_CUSTOM" in self.user[author.id]:
                                if self.user[author.id]["STK_CUSTOM"]:
                                    img["AFFICHAGE"] = "web"
                                    img["URL"] = self.user[author.id]["STK_CUSTOM"]
                                    img["NOM"] = "Custom de {}".format(author.name)
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue

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
                        for r in self.stk["STK"]:
                            if tr == self.stk["STK"][r]["NOM"]:
                                tr = r
                                txt = "**Importé depuis la V3**" if self.stk["STK"][tr]["IMPORT"] else "**Ajouté par** <@{}>".format(
                                    self.stk["STK"][tr]["AUTEUR"])
                                if "TAGS" in self.stk["STK"][tr]:
                                    txt += "\nTags: *Aucun tags*" if not self.stk["STK"][tr]["TAGS"] else \
                                        "\nTags: *{}*".format(", ".join(self.stk["STK"][tr]["TAGS"]))
                                em = discord.Embed(title= img["NOM"], description=txt, color=author.color)
                                em.set_image(url=img["URL"])
                                em.set_footer(text="Invoqué {} fois".format(self.stk["STK"][tr]["COMPTAGE"]))
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
    if not os.path.exists("data/systex"):
        print("Création du dossier Systex...")
        os.makedirs("data/systex")
    if not os.path.exists("data/systex/img"):
        print("Création du dossier d'Images Systex...")
        os.makedirs("data/systex/img")
    if not os.path.exists("data/systex/ressources"):
        print("Création du dossier de ressources Systex...")
        os.makedirs("data/systex/ressources")

def check_files():
    if not os.path.isfile("data/systex/stk.json"):
        print("Création du fichier Systex/stk.json...")
        fileIO("data/systex/stk.json", "save", {"OPT": {}, "STK": {}})
    if not os.path.isfile("data/systex/user.json"):
        print("Création du fichier Systex/user.json...")
        fileIO("data/systex/user.json", "save", {})

def setup(bot):
    check_folders()
    check_files()
    n = Systex(bot)
    bot.add_cog(n)
    bot.add_listener(n.stkmsg, "on_message")