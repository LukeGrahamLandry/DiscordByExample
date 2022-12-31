from UserVerification.src import EmailService, DataAccess
import discord

bot = discord.Bot()


@bot.event
async def on_message(message: discord.Message):
    discord_user_id = message.author.id
    if not DataAccess.is_verified(discord_user_id) and not message.author.bot:
        await message.delete()


@bot.event
async def on_ready():
    print(str(bot.user) + " is ready and online!")


@bot.slash_command(name="verify", description="Request a verification link email to speak in the server.")
async def verify_command(ctx: discord.ApplicationContext, user_id: discord.Option(discord.SlashCommandOptionType.string)):
    discord_user_id = ctx.author.id
    if DataAccess.is_verified(discord_user_id):
        await ctx.respond("This discord account has already been verified.")
        return

    email = DataAccess.get_email(user_id)
    if email is None:
        await ctx.respond("Invalid User ID.")
        return

    session = DataAccess.create_session(discord_user_id, user_id)
    EmailService.sendEmail(
        email,
        "Link your discord account {}? Click here: http://localhost:3000/verify/{}".format(ctx.author, session)
    )
    await ctx.respond("Link sent!")


def start(token):
    bot.run(token)
