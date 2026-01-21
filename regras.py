import discord
from discord.ext import commands
import json

# ID do canal permitido
CANAL_PERMITIDO_ID = 1449803169923076187

class Components(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Criamos o botão manualmente para inseri-lo na ActionRow
        self.btn_regras = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Regras do Servidor",
            custom_id="btn_regras_servidor",
        )
        # Atribuímos a função de clique ao botão
        self.btn_regras.callback = self.callback_regras

        self.container1 = discord.ui.Container(
            discord.ui.MediaGallery(
                discord.MediaGalleryItem(
                    media="https://cdn.discordapp.com/attachments/1388994505386229931/1453073937738240000/BEM_VINDOS_AO_20251223_141158_0000.png?ex=694c200f&is=694ace8f&hm=73f6751d6738ce082593b6f6e85b6901e57d2db24bff99ac37c27715da55351e&",
                ),
            ),
            discord.ui.TextDisplay(content="## Servidor Central da Amizade"),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(content="**Ficamos muito felizes em ter você aqui para fortalecer nossa comunidade focada em Amizade.**\nEste é o lugar ideal para você relaxar, conversar e encontrar novos parceiros de jogo. Para ajudar você a se situar, aqui está um resumo do que temos por aqui:\n> Lord e Gartic: O espaço perfeito para testar suas habilidades de desenho e se divertir com os bots.\n> Canais FTF: Área dedicada exclusivamente ao Flee The Facility, com canais de texto e Calls para você coordenar as partidas com a galera.\n> Bate-papo: O coração do servidor, onde o pessoal se reúne para conversar sobre tudo.\n> Imagens: Um canal para você compartilhar fotos, memes e artes com a comunidade.\n> Mostruário: Use o bot para exibir seu visual do Roblox ou conferir o estilo dos outros membros.\n> Níveis: Quanto mais você interage, mais XP ganha e sobe no nosso ranking, lá também você encontra alguns benefícios.\n> Sorteios: Fique de olho aqui para participar de eventos e ganhar prêmios.\n> Comandos: O lugar certo para interagir com nossos bots sem poluir o chat principal."),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(content="-# Para mantermos um ambiente saudável e divertido para todos, pedimos que:\n-# Siga as Regras da Comunidade.\n-# Respeite as Diretrizes do Discord: O cumprimento dos termos oficiais é obrigatório.\n**Dica: Sinta-se à vontade para entrar em uma call ou puxar assunto no chat. A casa é sua**"),
            discord.ui.ActionRow(self.btn_regras), # Botão inserido aqui
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            accent_colour=discord.Colour(6590671),
        )
        # Adiciona o container à view
        self.add_item(self.container1)

    # Função que o botão executa (Não mudei nada no texto)
    async def callback_regras(self, interaction: discord.Interaction):
        regras_texto = (
            "<:Um:1453076617315483831> **Respeito Mútuo**\nTrate todos os membros com educação e cordialidade. Não toleramos desrespeito, discursos de ódio, preconceito ou qualquer tipo de bullying.\n"
            "<:Dois:1453076647778713845> **Proibido Spam ou Flood**\nEvite o envio de mensagens repetitivas, excesso de emojis, menções desnecessárias (@everyone) ou poluir os canais com conteúdo sem sentido.\n"
            "<:Tres:1453076666841567452> **Conteúdo Apropriado (SFW)**\nÉ estritamente proibido o compartilhamento de conteúdo NSFW (pornografia, violência explícita, gore) ou links maliciosos. Mantenha o ambiente seguro para todos.\n"
            "<:Quatro:1453076683769774231> **Divulgação e Autopromoção**\nNão é permitida a divulgação de outros servidores, redes sociais ou lojas sem a autorização prévia da administração.\n"
            "<:Cinco:1453076701096575036> **Vendas e Negociações**\nPara a segurança de todos, proibimos vendas, anúncios comerciais e trocas cruzadas (cross-trading) de itens de jogos.\n"
            "<:Six:1453076717941035018> **Mantenha a Positividade**\nEvite discussões sobre temas polêmicos que gerem conflitos desnecessários. Nosso foco principal é a amizade e diversão!\n"
            "<:Seven:1453076733329936425> **Decisões da Moderação**\nA equipe de moderação está aqui para ajudar. As decisões dos moderadores devem ser respeitadas. Caso tenha alguma dúvida, utilize o suporte.\n"
            "<:Oito:1453076747800019097> **Privacidade e Segurança**\nNão compartilhe dados pessoais (seus ou de terceiros). Além destas regras, é obrigatório seguir os Termos de Serviço e as Diretrizes da Comunidade do Discord."
        )
        
        view_regras = discord.ui.LayoutView()
        view_regras.add_item(discord.ui.Container(
            discord.ui.TextDisplay(content=regras_texto),
            accent_colour=discord.Colour(6590671)
        ))
        
        await interaction.response.send_message(view=view_regras, ephemeral=True)

class Regras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(Components())

    @commands.command(name='regras')
    async def regras(self, ctx: commands.Context) -> None:
        await ctx.message.delete()
        
        if ctx.channel.id != CANAL_PERMITIDO_ID:
            return

        view = Components()
        await ctx.send(view=view)

async def setup(bot):
    await bot.add_cog(Regras(bot))
