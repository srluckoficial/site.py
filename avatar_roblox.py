import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio

class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_verificado = "<:verificado:1451409776570400810>" 
        self.emoji_comum = "<:vip:1451409805762760848>"
        self.ok_emoji = "<:ok:1451395221517631570>"
        self.no_emoji = "<:No:1451395266765914274>"
        # ID ATUALIZADO CONFORME SOLICITADO
        self.id_canal_especifico = 1451641109200769165
        self.ultima_instrucao = None 

    # Listener para apagar mensagens, figurinhas e emojis no canal específico
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora se for o próprio Bot (para não apagar a instrução e a embed)
        if message.author.id == self.bot.user.id: 
            return
            
        # Apaga TUDO que não for o Bot no canal específico
        if message.channel.id == self.id_canal_especifico:
            try:
                await message.delete()
            except:
                pass

    @app_commands.command(name="roblox", description="Busca informações de um usuário no Roblox")
    async def roblox(self, interaction: discord.Interaction, username: str):
        nome_limpo = username.replace("@", "")
        
        async with aiohttp.ClientSession() as session:
            # 1. Busca Dados
            payload = {"usernames": [nome_limpo], "excludeBannedUsers": True}
            async with session.post("https://users.roblox.com/v1/usernames/users", json=payload) as resp:
                data = await resp.json()

            if not data.get("data"):
                return await interaction.response.send_message(
                    f"{self.no_emoji} | Ué, parece que não existe ninguém com o nome \"{nome_limpo}\", tente outro nome.",
                    ephemeral=True
                )

            user_info = data["data"][0]
            user_id, display_name, name = user_info["id"], user_info["displayName"], user_info["name"]
            has_verified_badge = user_info.get("hasVerifiedBadge", False)

            # 2. Busca Avatar
            thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false"
            async with session.get(thumb_url) as resp:
                thumb_data = await resp.json()
                image_url = thumb_data["data"][0]["imageUrl"]

            # 3. Confirmação Ephemeral
            await interaction.response.send_message(f"{self.ok_emoji} | Avatar de **{display_name}** enviado com sucesso!", ephemeral=True)

            # 4. Construção da Embed
            emoji = self.emoji_verificado if has_verified_badge else self.emoji_comum
            embed = discord.Embed(
                title=f"{emoji} {display_name} (@{name})",
                url=f"https://www.roblox.com/users/{user_id}/profile",
                color=discord.Color.from_rgb(0, 162, 255)
            )
            embed.set_image(url=image_url)
            embed.set_footer(text=f"{name} | {user_id}")
            
            if has_verified_badge:
                embed.description = f"{self.ok_emoji} Esse usuário possui selo de verificação oficial."

            # Envia a Embed
            canal = interaction.channel
            msg_embed = await canal.send(embed=embed)

            # 5. Reações em qualquer canal
            await msg_embed.add_reaction(self.ok_emoji)
            await msg_embed.add_reaction(self.no_emoji)

            # 6. Lógica da Mensagem de Instrução (Apaga a anterior e manda nova)
            if self.ultima_instrucao:
                try: await self.ultima_instrucao.delete()
                except: pass

            texto_instrucao = (
                f"**Reaja com <:bonito:1317885888478449734> ou <:feio:1317885890709684296>** para dizer o que achou do **avatar!**\n"
                f"<:verificado_diamante:1342911257526931650> Mostre também seu avatar para a comunidade.\n"
                f"Basta utilizar o comando </roblox:10>"
            )
            self.ultima_instrucao = await canal.send(texto_instrucao)

async def setup(bot):
    await bot.add_cog(Roblox(bot))
