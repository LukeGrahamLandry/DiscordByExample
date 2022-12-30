# User Verification 

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
  - **you will have to install the `flask` pip package**
- main.py: runs your program
  - Bot and LinkServer will run on separate threads, in real life they could be on different physical servers 
