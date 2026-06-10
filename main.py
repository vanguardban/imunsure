import discord
from discord.ext import commands
from discord import app_commands
import asyncio

import os
from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────
#  EASY CONFIGURATION — Edit everything here
# ─────────────────────────────────────────────
CONFIG = {
    "TOKEN": os.getenv("DISCORD_TOKEN"),
    
    "STAFF_ROLE_NAME": "🙋",

    # Category names the bot will create automatically (if it doesn't already exist)
    "CATEGORY_QUESTIONS":  "📩 Questions",
    "CATEGORY_SUPPORT":    "🔧 Product Support",
    "CATEGORY_WHOLESALE":  "📦 Wholesale",
    "CATEGORY_ARCHIVED":   "📁 Archived",

    "TICKET_PREFIX": "ticket",

    # Panel embed (the message users click to open a ticket) ──
    "PANEL_TITLE": "Nebula — Tickets",
    "PANEL_DESCRIPTION": (
        "Welcome to Nebula Support! 👋\n\n"
        "Click one of the buttons below to open a support ticket.\n"
        "Our team will get back to you as soon as possible.\n\n"
        "**Please choose the category that best fits your request:**\n"
        "• ❓ **Questions** — General questions about our products or services\n"
        "• 🔧 **Product Issues** — Defective devices, refunds, or store credit\n"
        "• 📦 **Wholesale** — Bulk orders & partnership enquiries"
    ),
    "PANEL_COLOR": 0x5865F2,   #Color, change to any hex colour

    # Per category ticket embed content
    "TICKETS": {
        "questions": {
            "button_label": "❓ Questions",
            "button_style": discord.ButtonStyle.primary,   # Blue
            "embed_title": "Thank you for contacting us",
            "embed_description": (
                "We're happy to help! 😊\n\n"
                "Please send a message letting us know what you'd like to know — "
                "whether it's about our products, services, availability, or anything else. "
                "The more detail you provide, the faster we can assist you."
            ),
            "embed_color": 0x5865F2,   # Blue
        },
        "support": {
            "button_label": "🔧 Product Issues",
            "button_style": discord.ButtonStyle.danger,    # Red
            "embed_title": "Thank you for contacting us",
            "embed_description": (
                "We're sorry to hear you're experiencing an issue! 🛠️\n\n"
                "Please describe the problem in as much detail as possible — "
                "including your order number, the device or product affected, "
                "and what the issue is. For refunds or store credit requests, "
                "please also include proof of purchase if you have it."
            ),
            "embed_color": 0xED4245,   # Red
        },
        "wholesale": {
            "button_label": "📦 Wholesale",
            "button_style": discord.ButtonStyle.success,   # Green
            "embed_title": "Thank you for contacting us",
            "embed_description": (
                "Thanks for your interest in wholesale with Nebula! 📦\n\n"
                "Please let us know:\n"
                "• Which **products** you're interested in\n"
                "• The **quantities** you require\n"
                "• Your **business name** and any relevant details\n\n"
                "We'll review your request and get back to you shortly."
            ),
            "embed_color": 0x57F287,   # Green
        },
    },

    # Inside ticket buttons (for staff)
    "BTN_CLOSE":   "🔒 Close Ticket",
    "BTN_ARCHIVE": "📁 Archive Ticket",

    # Messages sent inside each ticket
    "TICKET_NOTIFY_MESSAGE": "Everyone has been notified — we'll get back to you as soon as possible! 🙏",
}
# ─────────────────────────────────────────────
#  END OF CONFIGURATION
# ─────────────────────────────────────────────


intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def get_or_create_category(guild: discord.Guild, name: str) -> discord.CategoryChannel:
    """Return an existing category by name or create it."""
    existing = discord.utils.get(guild.categories, name=name)
    if existing:
        return existing
    return await guild.create_category(name)


async def get_staff_role(guild: discord.Guild) -> discord.Role | None:
    return discord.utils.get(guild.roles, name=CONFIG["STAFF_ROLE_NAME"])


async def next_ticket_number(guild: discord.Guild) -> str:
    prefix = CONFIG["TICKET_PREFIX"] + "-"
    nums = []
    for ch in guild.text_channels:
        if ch.name.startswith(prefix):
            try:
                nums.append(int(ch.name[len(prefix):]))
            except ValueError:
                pass
    n = max(nums, default=0) + 1
    return f"{n:04d}"


class TicketPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label=CONFIG["TICKETS"]["questions"]["button_label"],
        style=CONFIG["TICKETS"]["questions"]["button_style"],
        custom_id="ticket_open_questions",
    )
    async def open_questions(self, interaction: discord.Interaction, button: discord.ui.Button):
        await open_ticket(interaction, "questions")

    @discord.ui.button(
        label=CONFIG["TICKETS"]["support"]["button_label"],
        style=CONFIG["TICKETS"]["support"]["button_style"],
        custom_id="ticket_open_support",
    )
    async def open_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        await open_ticket(interaction, "support")

    @discord.ui.button(
        label=CONFIG["TICKETS"]["wholesale"]["button_label"],
        style=CONFIG["TICKETS"]["wholesale"]["button_style"],
        custom_id="ticket_open_wholesale",
    )
    async def open_wholesale(self, interaction: discord.Interaction, button: discord.ui.Button):
        await open_ticket(interaction, "wholesale")


class TicketManageView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label=CONFIG["BTN_CLOSE"],
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket and deleting channel…", ephemeral=True)
        await asyncio.sleep(2)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

    @discord.ui.button(
        label=CONFIG["BTN_ARCHIVE"],
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_archive",
    )
    async def archive_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=False)

        guild = interaction.guild
        channel = interaction.channel
        archive_cat = await get_or_create_category(guild, CONFIG["CATEGORY_ARCHIVED"])

        creator_id = None
        if channel.topic:
            try:
                creator_id = int(channel.topic.split("creator:")[1].strip())
            except (IndexError, ValueError):
                pass

        overwrites = dict(channel.overwrites)

        if creator_id:
            creator = guild.get_member(creator_id)
            if creator and creator in overwrites:
                del overwrites[creator]

        await channel.edit(
            category=archive_cat,
            overwrites=overwrites,
            topic=channel.topic,
            reason=f"Ticket archived by {interaction.user}",
        )
        for child in self.children:
            child.disabled = True
        await interaction.followup.send("📁 Ticket archived.", ephemeral=True)

        await channel.send(f"📁 This ticket has been **archived** by {interaction.user.mention}.")



async def open_ticket(interaction: discord.Interaction, ticket_type: str):
    await interaction.response.defer(ephemeral=True, thinking=False)

    guild = interaction.guild
    member = interaction.user
    cfg = CONFIG["TICKETS"][ticket_type]

    cat_map = {
        "questions": CONFIG["CATEGORY_QUESTIONS"],
        "support":   CONFIG["CATEGORY_SUPPORT"],
        "wholesale": CONFIG["CATEGORY_WHOLESALE"],
    }
    category_name = cat_map[ticket_type]
    category = await get_or_create_category(guild, category_name)

    staff_role = await get_staff_role(guild)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        ),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_messages=True,
        )

    ticket_num = await next_ticket_number(guild)
    channel_name = f"{CONFIG['TICKET_PREFIX']}-{ticket_num}"

    channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites,
        topic=f"creator:{member.id}",
    )
    embed = discord.Embed(
        title=cfg["embed_title"],
        description=cfg["embed_description"],
        color=cfg["embed_color"],
    )
    embed.set_footer(text="Nebula Support • Use the buttons below to manage this ticket.")

    ping_msg = staff_role.mention if staff_role else ""

    await channel.send(
        content=f"{member.mention} {ping_msg}\n{CONFIG['TICKET_NOTIFY_MESSAGE']}",
        embed=embed,
        view=TicketManageView(),
    )

    await interaction.followup.send(
        f"✅ Your ticket has been created: {channel.mention}",
        ephemeral=True,
    )

@bot.tree.command(name="ticketschannel", description="Send the Nebula ticket panel to this channel.")
@app_commands.checks.has_permissions(administrator=True)
async def ticketschannel(interaction: discord.Interaction):
    # Defer first — then do the work
    await interaction.response.defer(ephemeral=True, thinking=False)

    embed = discord.Embed(
        title=CONFIG["PANEL_TITLE"],
        description=CONFIG["PANEL_DESCRIPTION"],
        color=CONFIG["PANEL_COLOR"],
    )
    embed.set_footer(text="Nebula Support")

    try:
        await interaction.channel.send(embed=embed, view=TicketPanelView())
        await interaction.followup.send("✅ Ticket panel sent!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(
            "❌ **Missing permission!** Please give the bot **Send Messages** and "
            "**Embed Links** permissions in this channel, then try again.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Unexpected error: `{e}`", ephemeral=True)


@ticketschannel.error
async def ticketschannel_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You need **Administrator** permissions to use this command.",
            ephemeral=True,
        )

@bot.event
async def on_ready():
    bot.add_view(TicketPanelView())
    bot.add_view(TicketManageView())

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    print("─" * 40)

if __name__ == "__main__":
    bot.run(CONFIG["TOKEN"])
