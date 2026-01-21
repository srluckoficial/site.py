import discord
from discord.ext import tasks, commands
from discord import app_commands
import aiohttp
import json
import os
import traceback
import re
import urllib.parse
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone, timedelta

# --- CLASSE DA INTERAÇÃO DO BOTÃO (CONTAINER V2) ---
class PainelView(discord.ui.LayoutView):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.gerar_painel()

    def gerar_painel(self):
        self.clear_items()
        res = self.cog.calcular_probabilidade_v4()
        emoji_p, nivel = self.cog.definir_status_br(res['total'])
        
        indev_ts = self.cog.games_config[174252938]["last_ts"]
        ftf_ts = self.cog.games_config[372226183]["last_ts"]
        
        indev_str = f"<t:{indev_ts}:F>" if indev_ts > 0 else "Carregando..."
        ftf_str = f"<t:{ftf_ts}:F>" if ftf_ts > 0 else "Carregando..."

        status_windy = self.cog.windy_status
        link_post = self.cog.windy_last_post 
        
        LINK_IMAGEM_FTF = "https://cdn.discordapp.com/attachments/1388994505386229931/1462827544221843478/noFilter-10.png?ex=696f9bd0&is=696e4a50&hm=e4457de72b505bd4d34a842c889a01305a834101c240576de7e206d69b39f509&"
        LINK_IMAGEM_INDEV = "https://cdn.discordapp.com/attachments/1388994505386229931/1461764712407633961/noFilter_4.webp"

        btn_detalhes = discord.ui.Button(label="Ver Detalhes", style=discord.ButtonStyle.secondary, custom_id="btn_spy_detalhes")
        btn_detalhes.callback = self.callback_detalhes

        btn_traduzir = discord.ui.Button(label="Ver Postagem", style=discord.ButtonStyle.primary, custom_id="btn_spy_traducao")
        btn_traduzir.callback = self.callback_postagem

        container = discord.ui.Container(
            discord.ui.TextDisplay(content="## FTF Jennie Spy"),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(content="**Últimas atualizações:**"),
            discord.ui.Section(
                discord.ui.TextDisplay(content=f"<:emoji_28:1461547419979485216> Flee The Facility:\n{ftf_str}"),
                accessory=discord.ui.Thumbnail(media=LINK_IMAGEM_FTF),
            ),
            discord.ui.Section(
                discord.ui.TextDisplay(content=f"<:indev:1461547394557673574> FTF [In Dev]:\n{indev_str}"),
                accessory=discord.ui.Thumbnail(media=LINK_IMAGEM_INDEV),
            ),
            discord.ui.TextDisplay(content="**DevForum:**"),
            discord.ui.TextDisplay(content=f"Status MrWindy: {status_windy}"),
            discord.ui.TextDisplay(content=f"Última postagem: {link_post}"),
            discord.ui.ActionRow(btn_traduzir), 
            discord.ui.TextDisplay(content="**Probabilidade de atualizar:**"),
            discord.ui.TextDisplay(content=f"{emoji_p} {nivel}"),
            discord.ui.TextDisplay(content=f"Total: {res['total']}/100"),
            discord.ui.ActionRow(btn_detalhes), 
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(content="-# Direitos de contêiner: FTF Tracker"),
            accent_colour=discord.Colour(10181046),
        )
        self.add_item(container)

    async def callback_detalhes(self, interaction: discord.Interaction):
        try:
            res = self.cog.calcular_probabilidade_v4()
            prob_atual = res['total']
            emoji, nivel = self.cog.definir_status_br(prob_atual)
            cor_hex = self.cog.obter_cor_nivel(prob_atual)
            
            caminho_grafico = "grafico.png" 
            if not os.path.exists(caminho_grafico):
                return await interaction.response.send_message("Arquivo grafico.png não encontrado!", ephemeral=True)

            with Image.open(caminho_grafico) as img:
                img = img.convert("RGBA")
                draw = ImageDraw.Draw(img)
                r, g, b = (cor_hex >> 16) & 0xff, (cor_hex >> 8) & 0xff, cor_hex & 0xff
                cor_rgb, cor_cinza = (r, g, b, 255), (169, 169, 169, 255)
                centro_x, centro_y, raio = 640, 360, 220
                caixa = [centro_x - raio, centro_y - raio, centro_x + raio, centro_y + raio]
                draw.ellipse(caixa, fill=cor_cinza)
                prob_desenho = min(prob_atual, 100)
                if prob_desenho > 0:
                    draw.pieslice(caixa, start=-90, end=-90 + (prob_desenho/100*360), fill=cor_rgb)

                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                file = discord.File(fp=buffer, filename="status_grafico.png")

            desc_linhas = [
                f"### Detalhes do Cálculo:",
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                f"- O horário é entre 21h00 - 06h00: **{'Sim (+10)' if res['horario_bonus'] > 0 else 'Não'}**",
                f"- Vezes que o MrWindy entrou no DevForum entre ontem e hoje: **{res['windy_n']} (+{res['windy_pts']})**",
                f"- Vezes que o FTF In Dev atualizou entre ontem e hoje: **{res['indev_n']} (+{res['indev_pts']})**",
                f"- Dias de Atraso: **{res['dias_atraso']}**",
                f"- Outras lógicas: **{res['pts_outras']}**"
            ]
            if res['dividido']: desc_linhas.append("- Divisor Aplicado (÷8): **Sim**")
            desc_linhas.append(f"\n-# Cálculo Final: {res['total']}%")

            embed = discord.Embed(title=f"{emoji} Status Detalhado: {nivel}", color=cor_hex)
            embed.description = "\n".join(desc_linhas)
            embed.set_image(url="attachment://status_grafico.png")
            await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
        except Exception: traceback.print_exc()

    async def callback_postagem(self, interaction: discord.Interaction):
        embed = discord.Embed(title="POSTAGEM (Traduzida):", color=0x2b2d31)
        embed.description = self.cog.windy_translated[:4000]
        await interaction.response.send_message(embed=embed, ephemeral=True)

class FTFManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.arquivo_dados = "dados_spy.json"
        self.arquivo_status = "painel_msg.json"
        self.canal_id_painel = 1461546376763674934   
        self.canal_id_avisos = 1461569854275588248   
        self.canal_id_notificacoes = 1450450761132675143 
        self.role_ping_id = 1461678494516908227
        
        self.dados = self.carregar_dados()
        self.games_config = {
            174252938: {"nome": "FTF [In Dev]", "place_id": 455327877, "last_update": None, "last_ts": 0, "emoji": "<:indev:1461547394557673574>", "role_id": 1450678582501445743},
            372226183: {"nome": "Flee The Facility", "place_id": 893973440, "last_update": None, "last_ts": 0, "emoji": "<:emoji_28:1461547419979485216>", "role_id": 1450678677825261759}
        }
        
        self.last_ftf_icon = self.dados.get("last_ftf_icon", "")
        self.windy_status, self.windy_last_post, self.windy_translated = "Buscando...", "Carregando...", "Aguardando..."
        self.ultimo_nivel_conhecido = None 
        self.primeira_execucao = True
        self.loop_principal.start()

    def carregar_dados(self):
        padrao = {"indev_log": [], "windy_entradas": 0, "indev_count_since_main": 0, "atraso_manual": -1, "last_ftf_icon": ""}
        if os.path.exists(self.arquivo_dados):
            try:
                with open(self.arquivo_dados, "r") as f:
                    d = json.load(f); [d.setdefault(k, v) for k, v in padrao.items()]; return d
            except: pass
        return padrao

    def salvar_dados(self):
        self.dados["last_ftf_icon"] = self.last_ftf_icon
        with open(self.arquivo_dados, "w") as f: json.dump(self.dados, f, indent=4)

    @app_commands.command(name="spy_set", description="Ajusta manualmente os contadores.")
    @app_commands.choices(categoria=[
        app_commands.Choice(name="MrWindy (Entradas)", value="windy"),
        app_commands.Choice(name="In Dev (Updates)", value="indev"),
        app_commands.Choice(name="Dias de Atraso", value="atraso")
    ])
    async def spy_set(self, interaction: discord.Interaction, categoria: str, quantidade: int):
        if categoria == "windy": self.dados["windy_entradas"] = quantidade
        elif categoria == "indev": self.dados["indev_count_since_main"] = quantidade
        elif categoria == "atraso": self.dados["atraso_manual"] = quantidade
        self.salvar_dados()
        await self.verificar_mudanca_probabilidade()
        await interaction.response.send_message(f"✅ **{categoria.upper()}** definido para **{quantidade}**.", ephemeral=True)

    @app_commands.command(name="test_updates", description="Testa todas as Embeds de atualização (Ícone, FTF e In Dev).")
    async def test_updates(self, interaction: discord.Interaction):
        # Busca thumbnails individuais para o teste
        async with aiohttp.ClientSession() as session:
            thumb_main = "https://via.placeholder.com/512"
            thumb_indev = "https://via.placeholder.com/512"
            
            async with session.get(f"https://thumbnails.roproxy.com/v1/places/gameicons?placeIds=893973440&size=512x512&format=Png") as r1:
                if r1.status == 200: thumb_main = (await r1.json())["data"][0]["imageUrl"]
            async with session.get(f"https://thumbnails.roproxy.com/v1/places/gameicons?placeIds=455327877&size=512x512&format=Png") as r2:
                if r2.status == 200: thumb_indev = (await r2.json())["data"][0]["imageUrl"]

        role_ftf = self.games_config[372226183]["role_id"]
        role_indev = self.games_config[174252938]["role_id"]
        
        embed_icon = discord.Embed(title=f"{self.games_config[372226183]['emoji']} Flee The Facility", description="O Ícone do jogo foi alterado", color=0xFF0000)
        embed_icon.set_thumbnail(url=thumb_main)
        
        embed_ftf = discord.Embed(title=f"{self.games_config[372226183]['emoji']} Flee The Facility", description="Nova atualização no Flee The Facility.", color=0xFF0000)
        embed_ftf.set_thumbnail(url=thumb_main)

        vezes = self.dados.get("indev_count_since_main", 0)
        embed_indev = discord.Embed(title=f"{self.games_config[174252938]['emoji']} Flee The Facility [InDev]", description=f"Nova atualização no jogo.\n-# Desde da última atualização do FTF, o jogo atualizou {vezes} vezes.", color=0xFF0000)
        embed_indev.set_thumbnail(url=thumb_indev)

        await interaction.response.send_message("⚙️ Simulando envios de atualização...", ephemeral=True)
        await interaction.channel.send(content=f"<@&{role_ftf}>", embed=embed_icon)
        await interaction.channel.send(content=f"<@&{role_ftf}>", embed=embed_ftf)
        await interaction.channel.send(content=f"<@&{role_indev}>", embed=embed_indev)

    def obter_cor_nivel(self, prob):
        table = {80: 0x800080, 61: 0x0000FF, 50: 0x00FF00, 40: 0xFFFF00, 30: 0xFFA500, 10: 0x8B4513}
        for k, v in table.items():
            if prob >= k: return v
        return 0xFF0000

    def definir_status_br(self, prob):
        table = {80: ("🟣", "Extremamente Alta"), 61: ("🔵", "Muito Alta"), 50: ("🟢", "Alta"), 40: ("🟡", "Moderada"), 30: ("🟠", "Baixa"), 10: ("🟤", "Muito Baixa")}
        for k, v in table.items():
            if prob >= k: return v
        return "🔴", "Extremamente Baixa"

    def calcular_probabilidade_v4(self):
        tz = timezone(timedelta(hours=-3))
        agora = datetime.now(tz)
        ftf_ts = self.games_config[372226183]["last_ts"]
        w_n, i_n = self.dados.get("windy_entradas", 0), self.dados.get("indev_count_since_main", 0)
        w_pts, i_pts = round(w_n * 1.4, 2), round(i_n * 4.0, 2)
        
        d_atraso = self.dados["atraso_manual"] if self.dados["atraso_manual"] != -1 else int((datetime.now(timezone.utc).timestamp() - ftf_ts) / 86400) if ftf_ts > 0 else 0
        h_bonus = 10 if (agora.hour >= 21 or agora.hour < 6) else 0
        
        soma_parcial = w_pts + i_pts + h_bonus
        
        pts_o = 10
        if 30 <= soma_parcial <= 80:
            if w_n > 7 or (i_n > 10 and d_atraso >= 3):
                pts_o = -30
        elif soma_parcial > 80:
            pts_o = -10
            
        val = soma_parcial + pts_o
        
        is_div = False
        if val < 20:
            val = val / 8
            is_div = True
            
        return {"total": min(max(round(val, 2), 0), 100.0), "horario_bonus": h_bonus, "windy_n": w_n, "windy_pts": w_pts, "indev_n": i_n, "indev_pts": i_pts, "dias_atraso": d_atraso, "pts_outras": pts_o, "dividido": is_div}

    async def enviar_embed_automatica(self, session, jogo_id, config):
        """Envia as embeds idênticas ao test_updates com thumbnails específicas por jogo."""
        canal = self.bot.get_channel(self.canal_id_notificacoes)
        if not canal: return
        
        role_id = config["role_id"]
        place_id = config["place_id"]
        
        # Busca a thumbnail específica do Place ID que acabou de atualizar
        icon_url = "https://via.placeholder.com/512"
        async with session.get(f"https://thumbnails.roproxy.com/v1/places/gameicons?placeIds={place_id}&size=512x512&format=Png") as r:
            if r.status == 200:
                icon_url = (await r.json())["data"][0]["imageUrl"]
        
        if jogo_id == 174252938: # In Dev
            vezes = self.dados.get("indev_count_since_main", 0)
            embed = discord.Embed(title=f"{config['emoji']} Flee The Facility [InDev]", description=f"Nova atualização no jogo.\n-# Desde da última atualização do FTF, o jogo atualizou {vezes} vezes.", color=0xFF0000)
        else: # Main Game
            embed = discord.Embed(title=f"{config['emoji']} Flee The Facility", description="Nova atualização no Flee The Facility.", color=0xFF0000)
        
        embed.set_thumbnail(url=icon_url)
        await canal.send(content=f"<@&{role_id}>", embed=embed)

    async def verificar_mudanca_probabilidade(self):
        res = self.calcular_probabilidade_v4()
        emoji, nivel = self.definir_status_br(res['total'])
        if self.primeira_execucao: self.ultimo_nivel_conhecido = nivel; self.primeira_execucao = False; return
        if nivel != self.ultimo_nivel_conhecido:
            canal = self.bot.get_channel(self.canal_id_avisos)
            if canal: await canal.send(content=f"<@&{self.role_ping_id}>", embed=discord.Embed(title="<:probabilidade:1461824287672631469> Mudança na Probabilidade", description=f"A probabilidade de atualizar foi alterada para {emoji} **{nivel}**.", color=0xFF0000))
            self.ultimo_nivel_conhecido = nivel

    async def obter_dados_roblox(self, session):
        try:
            # --- MONITORAMENTO ÍCONE ---
            async with session.get(f"https://thumbnails.roproxy.com/v1/places/gameicons?placeIds=893973440&size=512x512&format=Png") as r:
                if r.status == 200:
                    curr = (await r.json())["data"][0]["imageUrl"]
                    if self.last_ftf_icon and curr != self.last_ftf_icon:
                        canal = self.bot.get_channel(self.canal_id_notificacoes)
                        if canal: 
                            role = self.games_config[372226183]["role_id"]
                            emb = discord.Embed(title=f"{self.games_config[372226183]['emoji']} Flee The Facility", description="O Ícone do jogo foi alterado", color=0xFF0000)
                            emb.set_thumbnail(url=curr)
                            await canal.send(content=f"<@&{role}>", embed=emb)
                        self.last_ftf_icon = curr; self.salvar_dados()
                    elif not self.last_ftf_icon:
                        self.last_ftf_icon = curr; self.salvar_dados()

            # --- MONITORAMENTO SCRIPT ---
            u_ids = ",".join(str(uid) for uid in self.games_config.keys())
            async with session.get(f"https://games.roproxy.com/v1/games?universeIds={u_ids}") as resp:
                if resp.status == 200:
                    for jogo in (await resp.json()).get('data', []):
                        uid, upd = jogo['id'], jogo['updated']
                        ts = int(datetime.fromisoformat(upd.replace('Z', '+00:00')).timestamp())
                        conf = self.games_config[uid]
                        
                        if conf["last_update"] and (upd != conf["last_update"] and ts > conf["last_ts"]):
                            if uid == 174252938: 
                                self.dados["indev_count_since_main"] += 1
                            else: 
                                self.dados.update({"windy_entradas": 0, "indev_count_since_main": 0, "atraso_manual": -1})
                            
                            conf.update({"last_update": upd, "last_ts": ts})
                            self.salvar_dados()
                            # DISPARO REAL DA ATUALIZAÇÃO COM SESSION PARA BUSCAR THUMB
                            await self.enviar_embed_automatica(session, uid, conf)
                        elif not conf["last_update"]: 
                            conf.update({"last_update": upd, "last_ts": ts})

            # --- DEVFORUM ---
            async with session.get("https://devforum.roblox.com/t/flee-the-facility-change-log-011926/4271242.json") as resp:
                if resp.status == 200:
                    latest = (await resp.json())['post_stream']['posts'][-1]
                    diff = (datetime.now(timezone.utc) - datetime.fromisoformat(latest['created_at'].replace('Z', '+00:00'))).total_seconds()
                    status = "Online." if diff < 1800 else "Offline."
                    if self.windy_status == "Offline." and status == "Online.": self.dados["windy_entradas"] += 1; self.salvar_dados()
                    self.windy_status, self.windy_last_post = status, f"[Ver no DevForum #{latest['post_number']}](https://devforum.roblox.com/t/4183219/{latest['post_number']})"
                    try:
                        async with session.get(f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=pt&dt=t&q={urllib.parse.quote(re.sub(r'<[^>]+>', '', latest['cooked']))}") as rt:
                            if rt.status == 200: self.windy_translated = "".join([f[0] for f in (await rt.json())[0]])
                    except: pass
        except Exception: traceback.print_exc()

    @tasks.loop(seconds=1)
    async def loop_principal(self):
        async with aiohttp.ClientSession() as session: await self.obter_dados_roblox(session)
        await self.verificar_mudanca_probabilidade()
        canal = self.bot.get_channel(self.canal_id_painel)
        if canal:
            mid = None
            if os.path.exists(self.arquivo_status): 
                with open(self.arquivo_status, "r") as f:
                    mid = json.load(f).get("msg_id")
            view = PainelView(self)
            try:
                msg = await canal.fetch_message(mid); await msg.edit(view=view)
            except:
                nmsg = await canal.send(view=view)
                with open(self.arquivo_status, "w") as f:
                    json.dump({"msg_id": nmsg.id}, f)

    @loop_principal.before_loop
    async def before_loop(self): await self.bot.wait_until_ready()

async def setup(bot): await bot.add_cog(FTFManager(bot))
