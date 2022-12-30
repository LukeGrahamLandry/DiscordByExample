from UserVerification.src import EmailService, DataAccess
import discord
import dotenv
import os

dotenv.load_dotenv()


class MyBot(discord.Bot):
    async def on_message(self, message):
        discord_user_id = message.author.id
        if not DataAccess.is_verified(discord_user_id) and not message.author.bot:
            await message.delete()

    async def on_ready(self):
        print(f"{bot.user} is ready and online!")


bot = MyBot()


@bot.slash_command(name="verify", description="Request a verification link email to speak in the server.")
async def verify_command(ctx, user_id: discord.Option(discord.SlashCommandOptionType.string)):
    email = DataAccess.get_email(user_id)
    if email is None:
        await ctx.respond("Invalid User ID.")
        return

    discord_user_id = ctx.author.id
    session = DataAccess.create_session(discord_user_id, user_id)
    EmailService.sendEmail(
        email,
        "Link your discord account! Click here: http://localhost:3000/verify/" + session
    )
    await ctx.respond("Link sent!")


def start():
    bot.run(os.getenv('TOKEN'))
