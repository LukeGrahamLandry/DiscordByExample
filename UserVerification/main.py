from UserVerification.src import Bot, LinkServer
from threading import Thread
import os
import dotenv

Thread(target=LinkServer.start).start()

dotenv.load_dotenv()
Bot.start(os.getenv('TOKEN'))