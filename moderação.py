import discord
from discord import app_commands
from discord.ext import commands
import datetime
import json
import os

# --- NOVOS COMPONENTES V2 ---
class AvisoContainer(discord.ui.LayoutView):    
    def __init__(self, membro: discord.Member, motivo: str, staff: str, total: int):
        super().__init__()
        self.container1 = discord.ui.Container(
            discord.ui.TextDisplay(content="## ⚠️ NOVO AVISO"),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.Section(
                discord.ui.TextDisplay(content=f"**{membro.mention} recebeu um aviso.**"),
                discord.ui.TextDisplay(content=f"**Motivo:** {motivo}"),
                discord.ui.TextDisplay(content=f"Punido por: {staff}\nTotal de avisos: {total}/3"),
                accessory=discord.ui.Thumbnail(
                    media=membro.display_avatar.url,
                ),
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            accent_colour=discord.Colour(1472221), # Cor solicitada
        )

class Moderacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.arquivo = "dados_avisos.json"
        self.avisos_usuarios = self.carregar_avisos()
        
        # IDs dos Cargos
        self.ID_COORDENADOR = 1449808134993608886
        self.ID_MODERADOR = 1449808744711061596
        self.ID_AJUDANTE = 1449809359659077798

    def carregar_avisos(self):
        if os.path.exists(self.arquivo):
            with open(self.arquivo, "r") as f:
                return json.load(f)
        return {}

    def salvar_avisos(self):
        with open(self.arquivo, "w") as f:
            json.dump(self.avisos_usuarios, f, indent=4)

    def tem_cargo(self, interaction, *cargos_permitidos):
        user_roles = [role.id for role in interaction.user.roles]
        return any(role_id in user_roles for role_id in cargos_permitidos)

    remover_group = app_commands.Group(name="remover", description="Remove punições de membros")

    # --- BANIR ---
    @app_commands.command(name="banir", description="Bane um membro do servidor")
    async def banir(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não informado"):
        if not self.tem_cargo(interaction, self.ID_COORDENADOR):
            return await interaction.response.send_message("❌ Erro de permissão.", ephemeral=True)
        
        try:
            embed = discord.Embed(title="🚫 Você foi Banido", color=discord.Color.dark_red())
            embed.add_field(name="Servidor", value=interaction.guild.name)
            embed.add_field(name="Motivo", value=motivo)
            await membro.send(embed=embed)
        except: pass

        await membro.ban(reason=motivo)
        await interaction.response.send_message("✅ Membro Banido", ephemeral=True)
        await interaction.channel.send(f"{membro.mention} foi banido.")

    # --- DESBANIR ---
    @remover_group.command(name="banimento", description="Remove o banimento de um membro")
    async def desbanir(self, interaction: discord.Interaction, id_membro: str):
        if not self.tem_cargo(interaction, self.ID_COORDENADOR):
            return await interaction.response.send_message("❌ Erro de permissão.", ephemeral=True)
        
        user = await self.bot.fetch_user(int(id_membro))
        await interaction.guild.unban(user)
        await interaction.response.send_message("✅ Banimento Removido", ephemeral=True)
        await interaction.channel.send(f"banimento de {user.mention} removido.")

    # --- EXPULSAR ---
    @app_commands.command(name="expulsar", description="Expulsa um membro")
    async def expulsar(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não informado"):
        if not self.tem_cargo(interaction, self.ID_COORDENADOR, self.ID_MODERADOR):
            return await interaction.response.send_message("❌ Erro de permissão.", ephemeral=True)
        
        try:
            embed = discord.Embed(title="👢 Você foi Expulso", color=discord.Color.orange())
            embed.add_field(name="Servidor", value=interaction.guild.name)
            embed.add_field(name="Motivo", value=motivo)
            await membro.send(embed=embed)
        except: pass

        await membro.kick(reason=motivo)
        await interaction.response.send_message("✅ Membro Expulso", ephemeral=True)
        await interaction.channel.send(f"{membro.mention} foi expulso.")

    # --- CASTIGAR ---
    @app_commands.command(name="castigar", description="Muta um membro (Timeout)")
    async def castigar(self, interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str = "Não informado"):
        if not self.tem_cargo(interaction, self.ID_COORDENADOR, self.ID_MODERADOR, self.ID_AJUDANTE):
            return await interaction.response.send_message("❌ Erro de permissão.", ephemeral=True)
        
        duracao = datetime.timedelta(minutes=minutos)
        await membro.timeout(duracao, reason=motivo)
        
        try:
            embed = discord.Embed(title="🔇 Você foi Castigado", color=discord.Color.gold())
            embed.add_field(name="Duração", value=f"{minutos} minutos")
            embed.add_field(name="Motivo", value=motivo)
            await membro.send(embed=embed)
        except: pass

        await interaction.response.send_message("✅ Membro Castigado", ephemeral=True)
        await interaction.channel.send(f"{membro.mention} foi castigado.")

    @remover_group.command(name="castigo", description="Remove o castigo de um membro")
    async def remover_castigo(self, interaction: discord.Interaction, membro: discord.Member):
        if not self.tem_cargo(interaction, self.ID_COORDENADOR, self.ID_MODERADOR, self.ID_AJUDANTE):
            return await interaction.response.send_message("❌ Erro de permissão.", ephemeral=True)
        
        await membro.timeout(None)
        await interaction.response.send_message("✅ Castigo Removido", ephemeral=True)
        await interaction.channel.send(f"castigo de {membro.mention} removido.")

    # --- AVISAR (ATUALIZADO PARA CONTAINER V2 NO CANAL) ---
    @app_commands.command(name="avisar", description="Aplica um aviso")
    async def avisar(self, interaction: discord.Interaction, membro: discord.Member, motivo: str):
        if not self.tem_cargo(interaction, self.ID_COORDENADOR, self.ID_MODERADOR, self.ID_AJUDANTE):
            return await interaction.response.send_message("❌ Erro de permissão.", ephemeral=True)

        uid = str(membro.id)
        if uid not in self.avisos_usuarios: self.avisos_usuarios[uid] = []
        
        staff_nome = interaction.user.display_name
        self.avisos_usuarios[uid].append({
            "staff": staff_nome,
            "motivo": motivo,
            "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        total = len(self.avisos_usuarios[uid])
        self.salvar_avisos()

        # DM continua em Embed (para privacidade do usuário)
        try:
            embed_dm = discord.Embed(title="⚠️ Você recebeu um Aviso", color=discord.Color.red())
            embed_dm.add_field(name="Motivo", value=motivo)
            embed_dm.set_footer(text=f"Avisos totais: {total}/3")
            await membro.send(embed=embed_dm)
        except: pass

        await interaction.response.send_message(f"✅ Membro Avisado ({total}/3)", ephemeral=True)
        
        # LOG NO CANAL USANDO O CONTAINER V2
        view_aviso = AvisoContainer(membro, motivo, staff_nome, total)
        await interaction.channel.send(view=view_aviso)

        if total >= 3:
            await membro.kick(reason="Acúmulo de 3 avisos.")
            self.avisos_usuarios[uid] = []
            self.salvar_avisos()
            await interaction.channel.send(f"🚨 {membro.mention} atingiu 3 avisos e foi expulso!")

    @remover_group.command(name="aviso", description="Remove o último aviso de um membro")
    async def remover_aviso(self, interaction: discord.Interaction, membro: discord.Member):
        if not self.tem_cargo(interaction, self.ID_COORDENADOR, self.ID_MODERADOR):
            return await interaction.response.send_message("❌ Erro de permissão.", ephemeral=True)
        
        uid = str(membro.id)
        if uid in self.avisos_usuarios and len(self.avisos_usuarios[uid]) > 0:
            self.avisos_usuarios[uid].pop()
            self.salvar_avisos()
            await interaction.response.send_message("✅ Aviso Removido", ephemeral=True)
            await interaction.channel.send(f"aviso de {membro.mention} removido.")
        else:
            await interaction.response.send_message("❌ Este membro não possui avisos.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderacao(bot))
