import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import io, aiohttp, os, traceback, json

class Rankings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GUILDA_ID = "1449803169193394178"
        self.arquivo_json = "dados.json"
        self.diretorio_principal = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.fundo_path = os.path.join(self.diretorio_principal, "rank.png")
        self.font_black_path = os.path.join(self.diretorio_principal, "Roboto-Black.ttf")
        self.font_bold_path = os.path.join(self.diretorio_principal, "Roboto-Bold.ttf")

    def carregar_dados(self):
        if os.path.exists(self.arquivo_json):
            with open(self.arquivo_json, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    async def gerar_ranking_img(self, dados_rank):
        try:
            img = Image.open(self.fundo_path).convert("RGBA")
            draw = ImageDraw.Draw(img)
            f_n = ImageFont.truetype(self.font_black_path, 28)
            f_m = ImageFont.truetype(self.font_bold_path, 20)
            
            y_init, space = 85, 82
            for i, (uid, msgs) in enumerate(dados_rank[:10]):
                pos_y = y_init + (i * space)
                cor = "#00FFFF" if i == 0 else "#FFD700" if i == 1 else "#C0C0C0" if i == 2 else "white"
                draw.rounded_rectangle((35, pos_y, 650, pos_y + 70), radius=15, fill=cor)
                
                user = self.bot.get_user(int(uid)) or await self.bot.fetch_user(int(uid))
                nome = f"@{user.name}" if user else f"ID: {uid}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(user.display_avatar.url) as resp:
                        if resp.status == 200:
                            av_b = await resp.read()
                            av = Image.open(io.BytesIO(av_b)).resize((56, 56)).convert("RGBA")
                            mask = Image.new('L', (56, 56), 0)
                            ImageDraw.Draw(mask).ellipse((0, 0, 56, 56), fill=255)
                            img.paste(av, (50, pos_y + 7), mask)

                draw.text((120, pos_y + 12), f"#{i+1} {nome}", font=f_n, fill="black")
                draw.text((120, pos_y + 42), f"📝 {msgs} mensagens", font=f_m, fill="#333333")

            out = io.BytesIO()
            img.save(out, format="PNG")
            out.seek(0)
            return discord.File(fp=out, filename="ranking.png")
        except Exception:
            print(f"❌ ERRO NO RANKING:\n{traceback.format_exc()}")
            return None

    @app_commands.command(name="rank_mensagens", description="Ranking diário")
    async def rank_diario(self, interaction: discord.Interaction):
        await interaction.response.defer()
        dados = self.carregar_dados()
        usuarios = dados.get(self.GUILDA_ID, {}).get("usuarios", {})
        rank_f = sorted([(u, d["msgs_hoje"]) for u, d in usuarios.items() if d.get("msgs_hoje", 0) > 0], key=lambda x: x[1], reverse=True)
        
        if not rank_f: return await interaction.followup.send("Ninguém falou hoje.")
        file = await self.gerar_ranking_img(rank_f)
        await interaction.followup.send(file=file) if file else await interaction.followup.send("Erro ao gerar imagem.")

    @app_commands.command(name="ranking_mensal", description="Ranking mensal")
    async def rank_mensal(self, interaction: discord.Interaction):
        await interaction.response.defer()
        dados = self.carregar_dados()
        usuarios = dados.get(self.GUILDA_ID, {}).get("usuarios", {})
        rank_f = sorted([(u, d["msgs_mensal"]) for u, d in usuarios.items() if d.get("msgs_mensal", 0) > 0], key=lambda x: x[1], reverse=True)
        
        if not rank_f: return await interaction.followup.send("Sem dados mensais.")
        file = await self.gerar_ranking_img(rank_f)
        await interaction.followup.send(file=file) if file else await interaction.followup.send("Erro ao gerar imagem.")

async def setup(bot):
    await bot.add_cog(Rankings(bot))
