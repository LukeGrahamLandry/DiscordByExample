# User Verification

This project assumes you have some database of users and want to allow them to link those user accounts to their discord accounts. 
We will create a discord bot that only allows people to speak in the server if they verify thier discord account by linking it 
to an account in that preexisting database. 

I've encountered a real example of this at university.
They set up discord servers for some class's online office hours, and they want to link your real identity to your discord account.
So they email your student email with a [uuid](https://en.wikipedia.org/wiki/Universally_unique_identifier), and you paste it into the welcome channel.
Then it gives you a role that lets you talk in the server, and it sets your nickname to your real name from your student account.
So if you flagrantly violate academic integrity on the discord server they can actually do something about it because they know who you are.
Plus, if you get banned for that you can't just make a new discord account and rejoin because you only have one student email with the magic uuid.

Another application of this would be creating a paid community on discord. You could make a server that people can only use 
if they've logged into your website and paid a fee. 

## Code Organization

This project will be split into a few files to organize our code better.

- DataAccess.py: store user data
    - in this demo it just reads and writes to a file but in real life you'd use an actual database
    - must be threadsafe (explained later)
- Bot.py: the discord bot
    - delete messages from unverified users
    - add a slash command to request a verification email
- EmailService.py: send emails
    - in this demo it just prints to the console but in real life you'd use [SES](https://aws.amazon.com/ses/) or something
- LinkServer.py: host magic links
    - when the user clicks the emailed link, it will take them to this website
    - verify the user, linking their discord id to their internal user id in our database
    - in this demo it will run on your computer, and you can access it at https://localhost:3000
    - **you will need to install the [flask](https://flask.palletsprojects.com/) pip package**
- main.py: runs your program
    - Bot and LinkServer will run on separate threads, in real life they could be on different physical servers

Splitting the code up like this makes it easy to reason about the parts individually.
While working on a given component we can imagine the others as magic black boxes that perform their
task correctly. That way you don't have to think about the implementation details of the program as a whole
the entire time you're working on it. You can just focus on the parts you're working on right now.

## DataAccess

We will need to load and store some data that persists when the bot is restarted.
In any serious application you'd use a real database for this but since that's not really the point of this project,
I'll just save it in a json file since that's easy. `DataAccess.py` will provide functions for interacting with this data so if you wanted to
switch to using a real database, this is the only file you'd need to change.

`database.json` has two fields. `users` which maps user_id values to some data (`email` and `name`).
This represents your system's internal database. These users will be linked to discord accounts. The `discord` field maps
discord_user_id values to user_id values. We will update this when someone verifies themselves.

Let's start by loading the data from our file.

```python
import json

with open("database.json", "r") as f:
    data = json.loads(f.read())
user_data = data["users"]
discord_data = data["discord"]
```

### Concurrency

DataAccess will be used by both Bot and LinkServer, which will be running at the same time on separate threads.
This means we will need to do a bit of extra work to prevent concurrent access. It gets very bad very quickly
if different threads try to modify the same data at the same time. For a demo example like this it probably wouldn't actually
be a problem, but it's an easy fix, so I'm not going to just ignore it. In general your database software would probably handle this for you.

Additionally, In CPython, due to the [Global Interpreter Lock](https://docs.python.org/3/glossary.html#term-global-interpreter-lock)
only one thread can execute code at a time. So it really doesn't matter, but it's an important concept to be aware of.
To take real advantage of having multiple CPU cores you can use the [multiprocessing](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing) module
which gets around this problem but adds extra work in passing data between them. 
However, the use of threading in this project is not for performance.

Both the discord bot and the web server effectively spend most of their time sitting there, doing nothing,
waiting for an event to react to. The threading module allows us to tell the computer, "hey instead of running
the bot until it halts and then the web server, just run them both at the same time and switch which one actually gets
CPU time based on who has events in the queue". So if the bot and the web server get requests at the same time, they won't be
handled at the same time. They'll go one after another. 
So again the concurrency can't actually be a problem in this example, but we're going to over engineer a solution anyway. 

Python's threading module provides a `Lock` class. We create a lock object, and before we do anything with a
piece of data shared between threads, we it as "locked", when we're done reading or modifying the data,
we mark it as "unlocked". If your code ever tries to "lock" a `Lock` that is already "locked", it will freeze until something
else unlocks it and then relock it and continue as it was. This ensures that only one thing can be messing with our data at a time.

Python allows you to use the `with` keyword to specify that a block code should "lock" before running and "unlock" when it's done.
This ensures you can't accidentally forget to "unlock" something and leave your program stuck forever. Here's what that looks like.

```python
from threading import Lock
data_lock = Lock()

# now data_lock is unlocked
with data_lock:
    # now data_lock is locked
# we can run some code here
# now data_lock is unlocked again
```

### Simple Data Accessors 

Recall that we want to keep all access to our data abstract enough that the implementation could easily be swapped out for a database. 
So instead of our other code directly accessing the dictionary we loaded, we'll write some functions that work with 
specific data from the dictionary for them to import. 

`get_email` simply retrieves the email associated with a given user_id and 
`is_verified` checks if a discord_user_id has already been linked to a user_id.

```python
def get_email(user_id):
    with data_lock:
        if user_id not in user_data:
            return None
        return user_data[user_id]["email"]


def is_verified(discord_user_id):
    with data_lock:
        return str(discord_user_id) in discord_data
```

Now we'll set up a function to save any changes we've made to the file. 
We'll call this after any modification gets made so the state can persist when we restart the program. 
Note that `_write_data` does not use the `data_lock`. 
It will only be called from other methods, inside their `with data_lock` block. 
If we used the `data_lock` again here, the program would get stuck forever if it was called that way. 

Since python does not have a concept of private methods, we use an underscore prefix on the name to indicate 
that it should not be called from outside this file. Remember, it would be unsafe to do so without using 
our `data_lock` object. 

```python
def _write_data():
    with open("database.json", "w") as f:
        f.write(json.dumps(data, indent=4))
```

### Sessions

When a user requests verification from our discord bot we want to email them a unique link that can be used to confirm 
that they can access that email account (and thus own the account and have permission to link it to their discord account). 
We will do this by generating a random number (from a wide enough range that it would be hard to guess). This random number 
will be included in the link we email later. We also store the random number in a dictionary (sessions) where it is associated 
with the discord_user_id and user_id used to create it. This will be used shortly. 

```python
sessions = {}
def create_session(discord_user_id, user_id):
    with data_lock:
        session = str(randrange(9999999999))
        sessions[session] = (str(discord_user_id), user_id)
        return session
```

Now we want a way to take a session and actually preform the link between the discord_user_id and user_id it represents. 
This will be called when the user clicks their verification link. We'll start by just checking that the session is actually 
a valid one we've created before and return early if not. 

```python
def set_verified(session):
    with data_lock:
        if session not in sessions:
            return False

        pass
```

Then we'll retrieve the ids the session corresponds to and delete the session from the dictionary since they only need to 
use it once. Then we set the relationship between the discord_user_id and the user_id in our data storage 
(which gets read by is_verified above). Finally, save that change to the file system and return True to indicate a successful verification. 

```python
discord_user_id, user_id = sessions[session]
del sessions[session]
discord_data[discord_user_id] = user_id
_write_data()
return True
```

The word "session" is taken from the idea of [session cookies](https://allaboutcookies.org/what-are-session-cookies) which are 
how websites keep a user logged in as they move between pages. This implementation is different but its the same idea 
of giving a user a big random number that they can use later to identify themselves and let you look up secret information 
that you wouldn't want other users to be able to access. 

Creating a session will require access to the discord account. Getting the link to consume the session will require 
access to the email account. So if someone can create and then consume a session they must have access to both. 

## EmailService

`EmailService.py` is responsible for one thing: providing the `sendEmail` function.
In this demo, I won't actually be sending an email. I'll just print the information to the console.
But there are many APIs that allows sending emails programmatically. Since we've isolated this functionality
away in its own file, it would be easy to actually implement it without accidentally messing up the rest of the program.

```python
def sendEmail(email, content):
    print("Email to {}: {}".format(email, content))
```

## LinkServer

`LinkServer.py` implements a web server that will handle when the user clicks the magic link from their "email"
and link their discord account with the user_id they entered from the bot.

We will be using the [flask](https://flask.palletsprojects.com/) package, so you'll need to install that with pip.

### Basic Website

The `@app.route` annotation defines a page you can go to in the browser.
The parameter of the annotation defines the path that goes after the domain name.
A slash represents the root, no path, just the raw domain name.
The method will be called when a user enters that url in their browser and
the text returned will be rendered as html (so in this case it will just be a single link).

The `start` method will be called from our `main.py` program to actually start the web server listening for requests from a web browser.
Then you can access the website at `http://localhost:3000`. This will only work from your computer.
Other people on your wifi network could access it if they use your computer's local ip address instead of "localhost"
but allowing the internet at large to access it would require "port forwarding". That means telling your router that
random incoming traffic from the outside world should be sent to your computer instead of ignored.

```python
from flask import Flask
from UserVerification.src import DataAccess

app = Flask(__name__)

@app.route("/")
def home():
    return '<a href="https://github.com/LukeGrahamLandry/PycordByExample/UserVerification"> DiscordByExample </a>'

def start():
    app.run(host="0.0.0.0", port=3000)
```

For a real program in production you'd have to set it up on a computer that always stays on and allows the
internet access to the correct port. Perhaps a server in the cloud that you rent from some big tech company.
You'd buy a domain name and use the DNS setting from your registrar's website to point it at the computer's IP address.

### Handling Verification Links

Now we want to create a route that includes a session number from the user. 
It would be crazy to manually set up a separate route for every possible session number 
but luckily flask allows us to create url variables. When we use `@app.route("/verify/<session>")`, 
the text in the `<session>` portion of the url gets passed to the handler function as an argument. 
The route will match any path beginning with `/verify/`.

```python
@app.route("/verify/<session>")
def verify_user(session):
    pass
```

All we're going to do is try to set them as verified based on that session value by calling a method from DataAccess. 
We return a message letting them know if it was successful. 

```python
was_valid_session = DataAccess.set_verified(session)
if was_valid_session:
    return "Your discord account has been linked. You may now speak in the server."
else:
    return "Invalid Session. Please request a new link from the bot."
```

**Extension Challenge:** Have the program track when the same ip address tries to verify an unreasonable number of times.
Perhaps implement an exponential time out. For example, if they request 5 times, they must wait 10 seconds,
10 times -> 20 seconds, 15 times -> 40 seconds, etc.
That will make any automated scanning of all the possible session numbers impractical.
Use [`flask.request.environ.get('HTTP_X_REAL_IP', flask.request.remote_addr)`](https://stackoverflow.com/questions/3759981/get-ip-address-of-visitors-using-flask-for-python) to get the user's ip address.

**Extension Challenge:** Add another route that lets the user explicitly deny the verification. 
So include an extra link when you send the email that they can click if someone evil tried to link their discord account 
with an account they don't own the email address of. 

**Extension Challenge:** Set the user's discord nickname to the `name` field from the database. 

## Bot

`Bot.py` will define the bot responsible for actually interacting with discord through the [py-cord](https://pycord.dev) package. 

The `@bot.event` annotation subscribes a method to a discord event based on its name. 
The `on_ready` method will fire once the bot it set up and ready to respond to events.
We just log some text, so you know when it's ready for you to test it. 

I've separated out the actual running of the bot into a method that can be called from `main.py` later. 

```python
from UserVerification.src import EmailService, DataAccess
import discord

bot = discord.Bot()

@bot.event
async def on_ready():
    print(str(bot.user) + " is ready and online!")

def start(token):
    bot.run(token)
```

### Blocking Messages

The `on_message` method will fire whenever someone sends a message in a connected server. 
We will retrieve the `discord_user_id` of the message sender and user `DataAccess` to check if they've verified their
account already. If not we just delete the message.
Since this event will also fire for bot messages we check `not message.author.bot` before
deleting the message since we want to allow the bot to talk (but it's never gonna jump through hoops with your website lol).

```python
@bot.event
async def on_message(self, message):
    discord_user_id = message.author.id
    if not DataAccess.is_verified(discord_user_id) and not message.author.bot:
        await message.delete()
```

**Extension Challenge:** Do this based on a role instead of checking is_verified. 
Make sure you give someone the role when they click a verification link. 

### Slash Command to Request Link

First we'll register the command. In the `@bot.slash_command` annotation parameters we specify the name and description to show in the discord UI.
The extra arguments to the function (other than ctx) define options that the user will be able to enter when they use the command.
Giving it the type `discord.Option(discord.SlashCommandOptionType.string)` tells it we want to receive a string.

```python
@bot.slash_command(name="verify", description="Request a verification link email to speak in the server.")
async def verify_command(ctx, user_id: discord.Option(discord.SlashCommandOptionType.string)):
    pass
```

Before we bother doing anything else, let's check if the person that invoked the command is already verified. 
If they've already linked their discord to an account, we shouldn't let them relink it to another one. 

```python
discord_user_id = ctx.author.id
if DataAccess.is_verified(discord_user_id):
    await ctx.respond("This discord account has already been verified.")
    return
```

Now we'll use DataAccess to retrieve the email associated with the user_id they entered. If we can't find an email, the
user_id wasn't found, and we just send back a message to let them know.

```python
email = DataAccess.get_email(user_id)
if email is None:
    await ctx.respond("Invalid User ID.")
    return
```

Then, we'll create a new session that links the discord_user_id and the user_id.

```python
session = DataAccess.create_session(discord_user_id, user_id)
```

Finally, we'll "send an email" to the registered email address of that user_id.
The email contains the link with that session which will link its discord_user_id and user_id if clicked. 
In real life you'd put your domain name here instead of "localhost" 
but this link will be accessible only on your computer since it's just an example. 

```python
EmailService.sendEmail(
    email,
    "Link your discord account {}? Click here: http://localhost:3000/verify/{}".format(ctx.author, session)
)
await ctx.respond("Link sent!")
```

The only place that knows the magic session number is the person who owns the email address associated with the user_id entered by the user.
That means that if someone goes to that link, and confirms that it's their discord account, they must have access to both
the discord account (to request the link) and the email account (to retrieve the link).

**Extension Challenge:** Have the session also save the time it was created and expire after a few minutes.
Use `time.time()` (with `import time`) to get the current time in seconds since January 1st 1970.

## Main Program

`main.py` will just run Bot and LinkServer at the same time. 

```python
from UserVerification.src import Bot, LinkServer
from threading import Thread
import os
import dotenv

Thread(target=LinkServer.start).start()

dotenv.load_dotenv()
Bot.start(os.getenv('TOKEN'))
```

**Extension Challenge:** Have the bot support multiple user databases. So when invited to different discord servers 
users would verify themselves separately on each individual server to speak there. So multiple servers can invite the bot, 
with a different set of existing user accounts, without needing to host a separate bot instance for each server. 
