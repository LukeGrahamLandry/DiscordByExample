# Pycord By Example

Each directory is a self-contained project implementing a discord bot using the [py-cord](https://github.com/Pycord-Development/pycord) library. 
The README file will have a step by step explanation of how it was made. 

## Official Resources

PycordByExample explains practical examples of discord bots. 
Depending on how you learn, you may be better served by the official Guide or 
Docs which provide a more abstract explanation of how things work rather than diving into examples. 

- [Pycord Guide](https://guide.pycord.dev): Overview of how to use pycord features. 
- [Pycord Docs](https://docs.pycord.dev): API reference built from the comments in pycord code.

You can always come back for inspiration once you've got a better sense of how the library works in general. 

## Empty Bot

All example explanations will assume you've already set up your discord bot project.
Make sure you've installed python (>= 3.8) then go through Pycord's ["Installation"](https://guide.pycord.dev/installation) and ["Creating Your First Bot"](https://guide.pycord.dev/getting-started/creating-your-first-bot) guides. 
They'll lead you through installing the library, setting up a bot token and inviting it to a discord server for testing. 
It is very important that you don't skip this step. Nothing will work without it. 

The code below creates a bot that does absolutely nothing. It will be the starting point for each project. 

```python
import discord
import dotenv
import os

dotenv.load_dotenv()
bot = discord.Bot()

# The rest of your code will go here

bot.run(os.getenv('TOKEN'))
```

## Projects

Roughly ordered by difficulty. 

- RockPaperScissors: a simple game as a slash command