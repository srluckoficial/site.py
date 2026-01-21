import discord
from discord.ext import tasks, commands
import aiohttp
import datetime
import traceback

class UserSpy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.username = "Samuel_Amarelinho"
        self.user_url = f"https://devforum.roblox.com/u/{self.username}/summary.json"
        # ID do canal atualizado conforme solicitado
        self.canal_notificacao_id = 1453001402296041574 
        self.last_seen_known = None
        self.is_online = False
        self.monitor_user.start()

    def cog_unload(self):
        self.monitor_user.cancel()

    async def fetch_user_data(self, session):
        # Headers necessários para evitar bloqueio da API do Discourse (DevForum)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        try:
            async with session.get(self.user_url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            traceback.print_exc()
            return None

    @tasks.loop(seconds=3)
    async def monitor_user(self):
        async with aiohttp.ClientSession() as session:
            data = await self.fetch_user_data(session)
            if not data:
                return

            user_info = data.get('user', {})
            last_seen_str = user_info.get('last_seen_at')
            
            if not last_seen_str:
                return

            # Converter tempo da API (ISO 8601)
            last_seen_dt = datetime.datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
            agora = datetime.datetime.now(datetime.timezone.utc)
            diff = (agora - last_seen_dt).total_seconds()

            # Define se está online (visto nos últimos 5 minutos / 300 segundos)
            status_atual = diff < 300 
            
            # Lógica de Notificação de Mudança de Status
            if status_atual != self.is_online:
                self.is_online = status_atual
                canal = self.bot.get_channel(self.canal_notificacao_id)
                if canal:
                    # Verde para Online, Vermelho para Offline
                    cor = 0x00FF00 if self.is_online else 0xFF0000
                    status_txt = "Ficou ONLINE" if self.is_online else "Ficou OFFLINE"
                    
                    embed = discord.Embed(
                        title=f"Monitoramento: {self.username}",
                        description=f"O usuário **{self.username}** {status_txt} no DevForum.",
                        color=cor,
                        timestamp=datetime.datetime.now()
                    )
                    embed.add_field(name="Visto pela última vez", value=f"<t:{int(last_seen_dt.timestamp())}:R>")
                    # Usando a URL de avatar padrão baseada no nome de usuário do Discourse
                    avatar_url = f"https://devforum.roblox.com/letter_avatar_proxy/v4/letter/s/f0a315/128.png"
                    embed.set_thumbnail(url=avatar_url)
                    
                    await canal.send(embed=embed)

    @monitor_user.before_loop
    async def before_monitor(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(UserSpy(bot))
