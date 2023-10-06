# bot.py
# python -m venv /path/to/new/virtual/environment ### ./ for the current folder
# pip install --upgrade autopep8
# pip install --upgrade python-dotenv
# pip install --upgrade discord.py
# pip install --upgrade PyMySQL
# pip install --upgrade PyMySQL[rsa]
#
# To run the bot: python bot.py

import discord
import os
import pymysql
from dotenv import load_dotenv
from discord.ext import commands
from re import compile
from random import (
    choice,
    getrandbits
)
from pathlib import Path

####################
# GLOBAL VARIABLES #
####################
load_dotenv()
TOKEN = os.getenv('TOKEN')
INVITEURL = os.getenv('INVITEURL')
APPLICATIONID = os.getenv('APPLICATIONID')
PUBLICKEY = os.getenv('PUBLICKEY')
MYSQLUSER = os.getenv('MYSQLUSER')
MYSQLPASSWORD = os.getenv('MYSQLPASSWORD')
MYSQLDATABASE = os.getenv('MYSQLDATABASE')
MYSQLHOST = os.getenv('MYSQLHOST')
BOTOWNER = os.getenv('BOTOWNER')
BOTCURRENCY = os.getenv('BOTCURRENCY')

intents = discord.Intents().all()
client = commands.Bot(command_prefix='&', intents=intents)

SCRIPTDIR=os.path.realpath(os.path.dirname(__file__))
os.chdir(SCRIPTDIR)
print(os.getcwd()) ### Prints the current working directory to the console

tipsent = ""
newbal = 0
foundWallet = ""
createdDB = "no"

############################################################################
# ESTABLISH MYSQL DATABASE CONNECTION AND PERFORM SOME BASIC CONFIGURATION #
############################################################################
# open connection to MySQL server
connection = pymysql.connect(
    host=MYSQLHOST,
    user=MYSQLUSER,
    password=MYSQLPASSWORD
)
cursor = connection.cursor()

# create Database if it doesn't already exist and close the connection
try:
    cursor.execute('CREATE DATABASE %s' % MYSQLDATABASE)
    createdDB = "yes"
except Exception as exCreateDB:
    print('%s DATABASE already exist' % MYSQLDATABASE)
    print(exCreateDB)
finally:
    connection.close()

# open connection to MySQL server
connection = pymysql.connect(
    host=MYSQLHOST,
    user=MYSQLUSER,
    password=MYSQLPASSWORD,
    db=MYSQLDATABASE
)
cursor = connection.cursor()

# if database was created, then create the tables in the database
if createdDB == "yes":
    tpSql = "CREATE TABLE wallets (discordid varchar(64), balance varchar(30))", "INSERT INTO wallets (discordid, balance) VALUES (" + BOTOWNER + ", 1000000)"
    for sql in tpSql:
        cursor.execute(sql)
    connection.commit()

###################
# ON client READY #
###################
@client.event
async def on_ready():
    for guild in client.guilds:
        print(f'\nBot running in: {guild.name} (id: {guild.id})')
    print(
        f"Bot's Discord name: {client.user}\nInvite Bot: {INVITEURL}"
    )

##########################
# MEMBER WALLET COMMANDS #
##########################
@client.command(name='bothelp')
async def bothelp(interaction):
    response = f'&tip - tips the specified user (ex. &tip @Username 100)\n&balance - displays your balance\n&wallets - displays all known wallets (<@{BOTOWNER}> only command)'
    await interaction.send(response)

@client.command(name='tip', help='tips the mentioned user.')
async def tip(interaction, member: discord.Member, amount):
    tipsent = ""
    newbal = 0
    cursor.execute("SELECT * FROM wallets")
    row = cursor.fetchone()
    while row is not None:
        if row[0] == str(interaction.author.id):
            newbal = int(row[1]) - int(amount)
            if newbal > -1:
                cursor.execute("UPDATE wallets SET balance='%s' WHERE discordid='%s' " % (
                    str(newbal), str(interaction.author.id)))
                connection.commit()
            else:
                response = "<@%s> you can't afford this. Please check your balance." % (
                    str(interaction.author.id))
                await interaction.send(response)
                return None
        row = cursor.fetchone()
    cursor.execute("SELECT * FROM wallets")
    wallets = cursor.fetchall()
    foundWallet = ""
    for wallet in wallets:
        if wallet[0] == str(member.id):
            newbal = int(wallet[1])
            foundWallet = "found"
    if "foun" not in foundWallet:
        sql = "INSERT INTO wallets (discordid, balance) VALUES (" + \
            str(member.id) + ", " + amount + ")"
        cursor.execute(sql)
        connection.commit()
        response = "Wallet created for <@%s>.\n<@%s> sent <@%s> %s %s." % (
            str(member.id), str(interaction.author.id), str(member.id), amount, BOTCURRENCY)
    else:
        newbal += int(amount)
        cursor.execute("UPDATE wallets SET balance='%s' WHERE discordid='%s' " % (
            str(newbal), str(member.id)))
        connection.commit()
        response = "<@%s> sent <@%s> %s %s." % (
            str(interaction.author.id), str(member.id), amount, BOTCURRENCY)
    await interaction.send(response)

@client.command(name='balance', help='Displays your %s balance.' % (BOTCURRENCY))
async def balance(interaction):
    cursor.execute("SELECT * FROM wallets")
    wallets = cursor.fetchall()
    foundWallet = ""
    for wallet in wallets:
        if wallet[0] == str(interaction.author.id):
            memberBal = int(wallet[1])
            foundWallet = "found"
    if "foun" not in foundWallet:
        memberBal = 0
        sql = "INSERT INTO wallets (discordid, balance) VALUES (" + \
            str(interaction.author.id) + ", " + str(memberBal) + ")"
        cursor.execute(sql)
        connection.commit()
        response = "Wallet created for <@%s>.\nYour %s balance: %s" % (
            str(interaction.author.id), BOTCURRENCY, str(memberBal))
    else:
        response = "<@%s>, your %s balance: %s" % (
            str(interaction.author.id), BOTCURRENCY, str(memberBal))
    await interaction.send(response)

#####################
# BOT OWNER COMMANDS #
#####################
@client.command(name='wallets', help='Retrieve all entries in the wallets table.')
async def wallets(interaction):
    if str(interaction.author.id) == BOTOWNER:
        cursor.execute("SELECT * FROM wallets")
        wallets = cursor.fetchall()
        for wallet in wallets:
            await interaction.send(f"<@{wallet[0]}>, DiscordID: {wallet[0]}, {BOTCURRENCY} balance: {wallet[1]}")
    else:
        await interaction.send(f'You MUST be the bot owner to run this command.')

###########
# run BOT #
###########
client.run(TOKEN)
