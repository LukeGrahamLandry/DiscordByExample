import discord
import dotenv
import os
import random

dotenv.load_dotenv()
bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


class Selection:
    def __init__(self, name):
        self.name = name

    def beats(self, other):
        if self == Selection.ROCK:
            return other == Selection.SCISSORS
        elif self == Selection.PAPER:
            return other == Selection.ROCK
        elif self == Selection.SCISSORS:
            return other == Selection.PAPER

    def ties(self, other):
        return self == other


Selection.ROCK = Selection("rock")
Selection.PAPER = Selection("paper")
Selection.SCISSORS = Selection("scissors")


class GameView(discord.ui.View):
    @discord.ui.button(label="Rock", style=discord.ButtonStyle.primary, emoji="🪨")
    async def chooseRock(self, button, interaction):
        await endGame(interaction, Selection.ROCK)

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.primary, emoji="📄")
    async def choosePaper(self, button, interaction):
        await endGame(interaction, Selection.PAPER)

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.primary, emoji="✂️")
    async def chooseScissors(self, button, interaction):
        await endGame(interaction, Selection.SCISSORS)


async def endGame(interaction, player_choice):
    options = [Selection.ROCK, Selection.PAPER, Selection.SCISSORS]
    computer_choice = options[random.randrange(len(options))]

    response = "{} chose {} and the computer chose {}. \n".format(interaction.user, player_choice.name, computer_choice.name)
    if player_choice.beats(computer_choice):
        response += "You win!"
    elif player_choice.ties(computer_choice):
        response += "You tie."
    else:
        response += "You lose."

    await interaction.response.send_message(response)


@bot.slash_command(name="game", description="Play rock paper scissors")
async def startGame(ctx):
    await ctx.respond("Hey. let's play a game!", view=GameView())


bot.run(os.getenv('TOKEN'))
