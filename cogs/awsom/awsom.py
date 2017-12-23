import os

from .utils.dataIO import fileIO, dataIO


class Awsom:
    """Expérimentations d'un module intelligent, basé sur de l'intelligence artificielle"""
    def __init__(self, bot):
        self.bot = bot
        self.sys = dataIO.load_json("data/awsom/sys.json")



def check_folders():
    if not os.path.exists("data/awsom"):
        print("Création du dossier Awsom...")
        os.makedirs("data/awsom")


def check_files():
    if not os.path.isfile("data/awsom/sys.json"):
        print("Création du fichier Awsom/sys.json...")
        fileIO("data/awsom/sys.json", "save", {})


def setup(bot):
    check_folders()
    check_files()
    n = Awsom(bot)
    bot.add_cog(n)
