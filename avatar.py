import discord
from discord import app_commands
from discord.ext import commands
import requests

class AvatarRoblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configurações de IDs
        self.target_channel_id = 1450812011897163857
        self.emoji_verificado = "<:Verificado:1450905951119999096>"
        self.emoji_nao_verificado = "<:Vip:1450905985370554582>"
        self.last_instruction_msg = None

    @app_commands.command(name="avatar", description="Obtém o avatar do Roblox para o nick fornecido.")
    @app_commands.describe(username="O nome de usuário (nick) do Roblox")
    async def avatar(self, interaction: discord.Interaction, username: str):
        clean_username = username.replace("@", "")
        await interaction.response.defer()

        try:
            # 1. Buscar dados no Roblox
            user_req = requests.post("https://users.roblox.com/v1/usernames/users", json={
                "usernames": [clean_username],
                "excludeBannedUsers": True
            })
            user_data = user_req.json().get("data")

            if not user_data:
                return await interaction.followup.send(f"😅 | Não encontrei `{clean_username}`.", ephemeral=True)

            user_id = user_data[0]["id"]
            display_name = user_data[0]["displayName"]
            name = user_data[0]["name"]
            has_verified_badge = user_data[0].get("hasVerifiedBadge", False)
            status_emoji = self.emoji_verificado if has_verified_badge else self.emoji_nao_verificado

            # 2. Imagem do Avatar
            thumb_req = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false")
            image_url = thumb_req.json()["data"][0]["imageUrl"]

            # 3. Embed
            embed = discord.Embed(
                title=f"{status_emoji} {display_name} (@{name})",
                url=f"https://www.roblox.com/users/{user_id}/profile",
                color=discord.Color.blue()
            )
            embed.set_image(url=image_url)
            embed.set_footer(text=f"{interaction.user.name} | {interaction.user.id}", icon_url=interaction.user.display_avatar.url)

            # Envia o Avatar (Embed)
            msg_avatar = await interaction.followup.send(embed=embed)

            # 4. Lógica de reações e Instrução no canal específico
            if interaction.channel_id == self.target_channel_id:
                await msg_avatar.add_reaction("<:Yes:1450906032263135425>")
                await msg_avatar.add_reaction("<:No:1450906008376447038>")

                # Deleta a instrução antiga (se houver) e manda a nova abaixo da embed IMEDIATAMENTE
                if self.last_instruction_msg:
                    try: await self.last_instruction_msg.delete()
                    except: pass

                instruction_text = (
                    "> **Mostre seu visual! 💖**\n"
                    "> Utilize o comando </avatar:123> para mostrar o seu também."
                )
                # Envia como mensagem nova para ficar abaixo da embed
                self.last_instruction_msg = await interaction.channel.send(content=instruction_text)

        except Exception as e:
            print(f"Erro: {e}")
            await interaction.followup.send("❌ Erro ao buscar avatar.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id: return
        if message.channel.id == self.target_channel_id:
            if not message.interaction:
                try: await message.delete()
                except: pass

async def setup(bot):
    await bot.add_cog(AvatarRoblox(bot))
