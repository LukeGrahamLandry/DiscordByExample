from UserVerification.src import Bot, LinkServer
import threading

threading.Thread(target=LinkServer.start).start()
Bot.start()
