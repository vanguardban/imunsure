# Header :D

A lightweight Discord ticket bot built with discord.py. Users open tickets via a persistent button panel, which creates a private channel under the relevant category. Staff are automatically pinged and can close or archive tickets using in-channel buttons. All text, colours, role names, and category names are controlled from one config block at the top of the file — no digging through the code required.
Features

3 ticket categories: Questions, Product Support, Wholesale
Auto-creates Discord categories if they don't exist
Per-ticket private channels with correct permissions
Staff role ping on ticket open
Close (deletes channel) and Archive (moves to archive category, removes user access) buttons
Persistent views — buttons survive bot restarts
Single /ticketschannel slash command to deploy the panel (admin only)
