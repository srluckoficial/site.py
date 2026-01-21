import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import io, aiohttp, os, traceback, json

class PerfilVisual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GUILDA_ID = 1449803169193394178
        self.ID_CARGO_ATIVO = 1449816739683631338
        self.ID_CARGO_SUPER_ATIVO = 1449811251990368338
        self.arquivo_json = "dados.json"
        self.diretorio_principal = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.font_black_path = os.path.join(self.diretorio_principal, "Roboto-Black.ttf")
        self.font_bold_path = os.path.join(self.diretorio_principal, "Roboto-Bold.ttf")

    def carregar_dados(self):
        if os.path.exists(self.arquivo_json):
            with open(self.arquivo_json, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def salvar_dados(self, dados):
        with open(self.arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or message.guild.id != self.GUILDA_ID:
            return
        
        dados = self.carregar_dados()
        gid, uid = str(self.GUILDA_ID), str(message.author.id)
        
        if gid not in dados: dados[gid] = {"usuarios": {}}
        if uid not in dados[gid]["usuarios"]:
            dados[gid]["usuarios"][uid] = {"msgs_hoje": 0, "msgs_mensal": 0}
        
        dados[gid]["usuarios"][uid]["msgs_hoje"] += 1
        dados[gid]["usuarios"][uid]["msgs_mensal"] += 1
        
        # --- LÓGICA DE CARGOS E AVISOS ---
        msgs_hoje = dados[gid]["usuarios"][uid]["msgs_hoje"]
        
        # Meta 100
        if msgs_hoje == 100:
            cargo = message.guild.get_role(self.ID_CARGO_ATIVO)
            if cargo and cargo not in message.author.roles:
                await message.author.add_roles(cargo)
                await message.channel.send(f"🎉 {message.author.mention} atingiu **100 mensagens** hoje e agora é um **Membro Ativo**!")

        # Meta 1000
        elif msgs_hoje == 1000:
            cargo = message.guild.get_role(self.ID_CARGO_SUPER_ATIVO)
            if cargo and cargo not in message.author.roles:
                await message.author.add_roles(cargo)
                await message.channel.send(f"🚀 {message.author.mention} atingiu **1000 mensagens** hoje! Você é um **Membro Super Ativo**!")

        self.salvar_dados(dados)

    @app_commands.command(name="perfil", description="Ver seu perfil")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        await interaction.response.defer()
        try:
            alvo = membro or interaction.user
            dados = self.carregar_dados()
            u_data = dados.get(str(self.GUILDA_ID), {}).get("usuarios", {}).get(str(alvo.id), {"msgs_hoje": 0, "msgs_mensal": 0})
            
            msgs_hoje = u_data["msgs_hoje"]
            msgs_mensal = u_data["msgs_mensal"]

            fundo = "perfil3.png" if msgs_hoje >= 1000 else "perfil2.png" if msgs_hoje >= 100 else "perfil.png"
            tipo = "Membro Super Ativo" if msgs_hoje >= 1000 else "Membro Ativo" if msgs_hoje >= 100 else "Membro Inscrito"
            
            img = Image.open(os.path.join(self.diretorio_principal, fundo)).convert("RGBA")
            draw = ImageDraw.Draw(img)
            f_n = ImageFont.truetype(self.font_black_path, 34)
            f_l = ImageFont.truetype(self.font_black_path, 26)
            f_v = ImageFont.truetype(self.font_bold_path, 22)

            async with aiohttp.ClientSession() as session:
                async with session.get(alvo.display_avatar.url) as resp:
                    if resp.status == 200:
                        av_b = await resp.read()
                        av = Image.open(io.BytesIO(av_b)).resize((154, 154)).convert("RGBA")
                        mask = Image.new('L', (154, 154), 0)
                        ImageDraw.Draw(mask).ellipse((0, 0, 154, 154), fill=255)
                        img.paste(av, (179, 68), mask)

            draw.text((256, 260), f"@{alvo.name}", font=f_n, fill="white", anchor="mm")
            y_off = 320
            stats = [("Mensagens Hoje", msgs_hoje), ("Mensagens Mês", msgs_mensal), ("Tipo de Membro", tipo)]
            for label, val in stats:
                draw.text((150, y_off), label, font=f_l, fill="#1a1a1a")
                draw.text((150, y_off + 35), str(val), font=f_v, fill="#333333")
                y_off += 90

            with io.BytesIO() as out:
                img.save(out, format="PNG")
                out.seek(0)
                await interaction.followup.send(file=discord.File(fp=out, filename="perfil.png"))
        except Exception:
            print(f"❌ ERRO CRÍTICO NO PERFIL:\n{traceback.format_exc()}")
            await interaction.followup.send("❌ Erro ao gerar perfil.")

async def setup(bot):
    await bot.add_cog(PerfilVisual(bot))
