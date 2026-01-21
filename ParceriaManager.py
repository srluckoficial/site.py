import discord
from discord.ext import commands
from discord import app_commands

class ParceriaManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.canal_parceria_id = 1461150206958637088
        self.role_id = 1461158465174245571

    @app_commands.command(name="parceria", description="Envia um anúncio de parceria no contêiner V2")
    @app_commands.describe(texto_parceria="O texto descritivo da nova parceria")
    async def parceria(self, interaction: discord.Interaction, texto_parceria: str):
        canal = self.bot.get_channel(self.canal_parceria_id)
        
        if not canal:
            return await interaction.response.send_message(
                "❌ Erro: Canal de parceria não encontrado ou o bot não tem acesso.", 
                ephemeral=True
            )

        # Pegando a URL da foto do usuário que executou o comando
        user_avatar = interaction.user.display_avatar.url

        # Classe da View com o Contêiner V2
        class ParceriaView(discord.ui.LayoutView):
            def __init__(self, avatar_url, texto, role_mention):
                super().__init__(timeout=None)
                
                container = discord.ui.Container(
                    discord.ui.TextDisplay(content="## NOVA PARCERIA"),
                    discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
                    discord.ui.Section(
                        discord.ui.TextDisplay(content=texto),
                        accessory=discord.ui.Thumbnail(media=avatar_url),
                    ),
                    discord.ui.TextDisplay(content=f"-# <@&{role_mention}>"),
                    discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
                    accent_colour=discord.Colour(1472221),
                )
                self.add_item(container)

        # Criando a view e enviando para o canal de parcerias
        view = ParceriaView(user_avatar, texto_parceria, self.role_id)
        
        try:
            await canal.send(view=view)
            # Resposta para o usuário que usou o comando
            await interaction.response.send_message("✅ Mensagem de Parceria Enviada", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao enviar: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ParceriaManager(bot))
