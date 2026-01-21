import discord
from discord.ext import commands, tasks
import itertools

class StatusRotativo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Aqui definimos o texto e o emoji (opcional)
        self.status_ciclo = itertools.cycle([
            {"texto": "Como vai as coisas amiguinho! ✨", "emoji": "💎"},
            {"texto": "Monitorando MrWindy...🔍", "emoji": "🔍"},
            {"texto": "Flee the Facility Updates 😍", "emoji": "📝"},
            {"texto": "Precisa de ajuda? abra um ticket. 💡", "emoji": "💡"}
        ])
        self.mudar_status.start()

    def cog_unload(self):
        self.mudar_status.cancel()

    @tasks.loop(seconds=120)
    async def mudar_status(self):
        item = next(self.status_ciclo)
        
        # O segredo está aqui: ActivityType.custom
        # O 'name' é o texto que aparece, e o 'state' também deve ser o mesmo texto em alguns casos
        await self.bot.change_presence(
            status=discord.Status.online, 
            activity=discord.CustomActivity(name=item["texto"], emoji=item["emoji"])
        )

    @mudar_status.before_loop
    async def before_mudar_status(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(StatusRotativo(bot))
