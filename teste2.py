import discord
from discord import app_commands
from discord.ext import commands

class Teste(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="teste_ranking", description="Mostra a embed de teste com botão de ranking")
    async def teste_ranking(self, interaction: discord.Interaction):
        # 1. Criar a Embed
        embed = discord.Embed(
            title="📊 Central de Estatísticas",
            description="Clique no botão abaixo para verificar quem são os membros mais ativos e com mais pontos no servidor!",
            color=discord.Color.dark_grey()
        )
        
        # URL da imagem no topo
        embed.set_image(url="https://cdn.discordapp.com/attachments/1388994505386229931/1450892924286926939/CENTRAL_DA_AMIZADE_20251217_134822_0000.png")
        
        # 2. Criar a View com o Botão Cinza (Secondary)
        view = discord.ui.View(timeout=None)
        
        button = discord.ui.Button(
            label="Consultar Rank de Pontos", 
            style=discord.ButtonStyle.secondary, 
            custom_id="btn_rank_teste"
        )

        # Função que o botão executa ao ser clicado
        async def button_callback(it: discord.Interaction):
            # Tenta pegar o Cog de Pontos para ler os dados
            pontos_cog = self.bot.get_cog("Pontos")
            if not pontos_cog or not pontos_cog.dados["banco_pontos"]:
                return await it.response.send_message("❌ O ranking ainda está vazio ou o sistema de pontos está offline.", ephemeral=True)
            
            sorted_rank = sorted(pontos_cog.dados["banco_pontos"].items(), key=lambda x: x[1], reverse=True)[:10]
            msg = ""
            for i, (user_id, pts) in enumerate(sorted_rank, 1):
                m = it.guild.get_member(int(user_id))
                nome = m.mention if m else f"ID: {user_id}"
                msg += f"**{i}.** {nome} — `{pts} pts`\n"

            rank_embed = discord.Embed(title="🏆 Ranking de Pontos", description=msg, color=0xf1c40f)
            await it.response.send_message(embed=rank_embed, ephemeral=True)

        button.callback = button_callback
        view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Teste(bot))
