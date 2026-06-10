# 🎫 Nebula Ticket Bot
# A simple, clean Discord ticket bot built with discord.py. Drop a support panel anywhere in your server and let users open tickets in seconds.

✨ Features

📂 3 Ticket Categories — Questions, Product Support & Wholesale
🏗️ Auto Category Creation — Creates Discord categories automatically if they don't exist
🔒 Private Channels — Each ticket is visible only to the user and staff
📣 Staff Pinging — Automatically pings your staff role when a ticket is opened
🗂️ Archive & Close — Staff can archive (hides from user, keeps logs) or close (deletes) tickets with one click
♻️ Persistent Buttons — Buttons keep working even after the bot restarts
⚙️ One-Block Config — All names, colours, messages & categories are edited in a single CONFIG block — no hunting through code


🚀 Setup

Clone the repo and install dependencies:
```
bashpip install discord.py
```
Add your token, inside the .env file
Edit the CONFIG block at the top of the file to match your server
Run the bot:
```
python bot.py
```
Deploy the panel — use /ticketschannel in any channel (admin only)
