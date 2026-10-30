import discord
from discord import app_commands
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 1. Vista per chiudere il ticket
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Chiudi Ticket", style=discord.ButtonStyle.danger, custom_id="btn_chiudi_ticket")
    async def chiudi_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Chiusura del ticket in corso...", ephemeral=True)
        await asyncio.sleep(2)
        try:
            await interaction.channel.delete()
        except Exception:
            pass

# 2. Menù a tendina per i ticket generali
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Assistenza Generale", description="Domande generali sul server di Padova", emoji="💬", value="generale"),
            discord.SelectOption(label="Problemi Tecnici", description="Bug o problemi con i servizi", emoji="🛠️", value="tecnico"),
            discord.SelectOption(label="Segnalazioni Staff", description="Segnala un comportamento scorretto", emoji="🚨", value="segnalazioni")
        ]
        super().__init__(placeholder="Seleziona il motivo del ticket...", min_values=1, max_values=1, options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        motivo = self.values[0]

        nomi_categorie = {
            "generale": "supp",
            "tecnico": "tech",
            "segnalazioni": "report"
        }
        
        channel_name = f"{nomi_categorie.get(motivo, 'ticket')}-{interaction.user.name.lower()}"

        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.followup.send(f"⚠️ Hai già un ticket aperto in questa categoria: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)

        embed = discord.Embed(
            title=f"🎫 Ticket: {self.values[0].capitalize()}",
            description=f"Benvenuto {interaction.user.mention}!\nEsponi qui sotto il tuo problema. Lo staff di Padova ti risponderà presto.",
            color=discord.Color.purple()
        )

        await ticket_channel.send(embed=embed, view=CloseTicketView())
        await interaction.followup.send(f"✅ Ticket creato con successo: {ticket_channel.mention}", ephemeral=True)

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# 3. Modulo Cittadinanza
class ModuloCittadinanza(discord.ui.Modal, title="Richiesta di Cittadinanza - Padova"):
    nome_pg = discord.ui.TextInput(label="Nome e Cognome del Personaggio", placeholder="Es. Mario Rossi", required=True, max_length=100)
    eta_pg = discord.ui.TextInput(label="Età e Storia del Personaggio", placeholder="Es. 25 anni / Breve storia...", style=discord.TextStyle.paragraph, required=True, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        canale_ticket = await guild.create_text_channel(name=f"cittadinanza-{interaction.user.name}", overwrites=overwrites)

        embed = discord.Embed(title="📜 Nuova Richiesta di Cittadinanza", description=f"Richiesta inviata da {interaction.user.mention}", color=discord.Color.blue())
        embed.add_field(name="Nome Personaggio", value=self.nome_pg.value, inline=False)
        embed.add_field(name="Storia / Dettagli", value=self.eta_pg.value, inline=False)

        await canale_ticket.send(embed=embed, view=CloseTicketView())
        await interaction.followup.send(f"✅ Modulo inviato! Controlla il canale creato: {canale_ticket.mention}", ephemeral=True)

class SportelloView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Richiedi Cittadinanza 📜", style=discord.ButtonStyle.primary, custom_id="btn_cittadinanza")
    async def richiedi_cittadinanza(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModuloCittadinanza())

@bot.event
async def on_ready():
    print(f"✅ Bot online come: {bot.user.name}")

@bot.event
async def setup_hook():
    bot.add_view(TicketPanelView())
    bot.add_view(SportelloView())
    bot.add_view(CloseTicketView())
    await bot.tree.sync()
    print("Comandi sincronizzati!")

# Comando /setup_sportello
@bot.tree.command(name="setup_sportello", description="Crea il pannello cittadinanza")
@app_commands.checks.has_permissions(administrator=True)
async def setup_sportello(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="🏛️ SPORTELLO CITTADINANZA PADOVA", description="Clicca sul pulsante per compilare il modulo di cittadinanza.", color=discord.Color.blue())
    await interaction.channel.send(embed=embed, view=SportelloView())
    await interaction.followup.send("Pannello creato!", ephemeral=True)

# Comando /ticketpanel
@bot.tree.command(name="ticketpanel", description="Crea il pannello di assistenza con menù a tendina")
@app_commands.checks.has_permissions(administrator=True)
async def ticketpanel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="🎫 CENTRO ASSISTENZA PADOVA", description="Seleziona dal menu a tendina la categoria per aprire un ticket.", color=discord.Color.gold())
    await interaction.channel.send(embed=embed, view=TicketPanelView())
    await interaction.followup.send("Pannello ticket creato!", ephemeral=True)

# Comando /purge
@bot.tree.command(name="purge", description="Elimina i messaggi")
@app_commands.describe(quantita="Numero di messaggi (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, quantita: int):
    await interaction.response.defer(ephemeral=True)
    if quantita < 1 or quantita > 100:
        await interaction.followup.send("⚠️ Scegli tra 1 e 100.", ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=quantita)
    await interaction.followup.send(f"🗑️ Eliminati {len(deleted)} messaggi.", ephemeral=True)

bot.run("MTU2NTcyOTUxNTcyMzAzNDc3NQ.GUnNdf.mOVNxzABEXxf8oTcA6YuY8LTewD1Cv7dW3umzg")
