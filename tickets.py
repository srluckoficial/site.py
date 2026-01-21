import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import traceback
import json # Necessário para o sistema de dados

# --- CONFIGURAÇÕES ---
ID_CARGO_STAFF = 1452998249735655505 
ID_CANAL_SUPORTE = 1453051465366110282 

# --- COG DE DADOS (O que estava faltando) ---
class SistemaDados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.arquivo = "dados.json"
        try:
            with open(self.arquivo, "r") as f:
                self.dados = json.load(f)
        except:
            self.dados = {"usuarios": {}}

    def salvar(self):
        with open(self.arquivo, "w") as f:
            json.dump(self.dados, f, indent=4)

    def verificar_usuario(self, user_id):
        uid = str(user_id)
        if uid not in self.dados["usuarios"]:
            self.dados["usuarios"][uid] = {"ticket_ativo": False, "ticket_id": None}
            self.salvar()

# --- CLASSE DE COMPONENTES V2 (UI) ---
class TicketLayout(discord.ui.LayoutView):    
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    container_ticket = discord.ui.Container(
        discord.ui.MediaGallery(
            discord.MediaGalleryItem(
                media="https://cdn.discordapp.com/attachments/1388994505386229931/1453073943740289237/BEM_VINDOS_AO_20251223_141222_0000.png?ex=69555a90&is=69540910&hm=6b195e5ddddb5be9aadd2172888ea93809ad3ae15dbb7a511836e3942bfd768f&",
            ),
        ),
        discord.ui.TextDisplay(
            content="## Painel de Atendimento - CdA \n"
                    "Bem-vindo à nossa central de suporte! Este é o local exclusivo para você "
                    "resolver pendências, denunciar irregularidades ou colaborar com o crescimento do servidor."
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.ActionRow(
            discord.ui.Select(
                custom_id="select_ticket_v2",
                placeholder="Escolha uma opção de atendimento...",
                options=[
                    discord.SelectOption(label="Resgatar Sorteios", emoji="🎁", value="resgate"),
                    discord.SelectOption(label="Fazer Denúncia", emoji="🚫", value="denuncia"),
                    discord.SelectOption(label="Dar Sugestão", emoji="💡", value="sugestao"),
                    discord.SelectOption(label="Patrocinar Sorteio", emoji="💎", value="patrocinio"),
                ],
            ),
        ),
        accent_colour=discord.Colour(9390333),
    )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.data or "custom_id" not in interaction.data:
            return True

        if interaction.data.get("custom_id") == "select_ticket_v2":
            try:
                await interaction.response.defer(ephemeral=True)
            except:
                pass 
                
            escolha = interaction.data.get("values")[0]
            await self.processar_ticket(interaction, escolha)
            return False
        return True

    async def processar_ticket(self, interaction: discord.Interaction, escolha_usuario: str):
        try:
            sistema = self.bot.get_cog("SistemaDados")
            if not sistema:
                return await interaction.followup.send("❌ Erro: Cog de Dados não encontrada.", ephemeral=True)

            uid = str(interaction.user.id)
            sistema.verificar_usuario(interaction.user.id)
            
            if sistema.dados["usuarios"][uid].get("ticket_ativo"):
                return await interaction.followup.send("❌ Você já possui um ticket aberto!", ephemeral=True)

            categorias = {
                "resgate": {"prefixo": "🥳 Sorteio", "msg": "**Parabéns por ganhar um Sorteio!** Envie algumas provas:\n- Print do Sorteio."},
                "denuncia": {"prefixo": "🚫 Denúncia", "msg": "**Você está denunciando uma ação ou membro.** Por favor informe:\n- ID do membro que irá denunciar;\n- Prova da denúncia;\n- Relatório de denúncia."},
                "sugestao": {"prefixo": "💡 Sugestão", "msg": "**Você está aqui para fazer uma sugestão**, digite brevemente sua sugestão e aguarde um membro da staff."},
                "patrocinio": {"prefixo": "💎 Patrocínio", "msg": "**Eba!! Mais um patrocinador.** Precisamos de algumas informações:\n- Seu sorteio será de algum set do FTF?\n- Seu sorteio será de gift card, cartão robux ou outros?"}
            }
            
            info = categorias[escolha_usuario]
            novo_nome_topico = f"{info['prefixo']} (@{interaction.user.name})"
            
            canal_alvo = interaction.guild.get_channel(ID_CANAL_SUPORTE)
            if not canal_alvo:
                 return await interaction.followup.send("❌ Canal de suporte não configurado corretamente.", ephemeral=True)

            ticket_id_antigo = sistema.dados["usuarios"][uid].get("ticket_id")
            thread = None

            if ticket_id_antigo:
                thread = interaction.guild.get_thread(ticket_id_antigo)
                if thread:
                    try:
                        await thread.edit(archived=False, locked=False, name=novo_nome_topico)
                    except:
                        thread = None

            if not thread:
                try:
                    thread = await canal_alvo.create_thread(name=novo_nome_topico, type=discord.ChannelType.private_thread, invitable=False)
                except:
                    thread = await canal_alvo.create_thread(name=novo_nome_topico)

            await thread.add_user(interaction.user)
            
            sistema.dados["usuarios"][uid]["ticket_ativo"] = True
            sistema.dados["usuarios"][uid]["ticket_id"] = thread.id
            sistema.salvar()

            cargo_staff = interaction.guild.get_role(ID_CARGO_STAFF)
            mencao = await thread.send(f" 🛎**NOVO CHAMADO:** {interaction.user.mention} | {cargo_staff.mention if cargo_staff else ''}")
            await asyncio.sleep(1)
            try: await mencao.delete() 
            except: pass

            await thread.send(info["msg"])

            view_link = discord.ui.View()
            view_link.add_item(discord.ui.Button(label="Ir para o Ticket", url=thread.jump_url))
            await interaction.followup.send(f"✅ Seu ticket de **{info['prefixo']}** foi preparado!", view=view_link, ephemeral=True)
            
        except Exception:
            print(f"Erro no ticket: {traceback.format_exc()}")

# --- COG DO COMANDO ---
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Removido add_view daqui para evitar erros de loop no setup

    @app_commands.command(name="central_ticket", description="Envia a central de atendimento")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        view = TicketLayout(self.bot)
        await interaction.channel.send(view=view)
        await interaction.response.send_message("✅ Central enviada!", ephemeral=True)

    @app_commands.command(name="fecharticket", description="Arquiva o ticket")
    async def arquivar(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            return await interaction.response.send_message("❌ Use dentro de um ticket!", ephemeral=True)

        sistema = self.bot.get_cog("SistemaDados")
        if not sistema:
            return await interaction.response.send_message("❌ Sistema de dados offline.")

        uid_dono = None
        for uid, d in sistema.dados["usuarios"].items():
            if d.get("ticket_id") == interaction.channel.id:
                uid_dono = uid
                break
        
        if uid_dono:
            sistema.dados["usuarios"][uid_dono]["ticket_ativo"] = False
            sistema.salvar()

        await interaction.response.send_message("Ticket Fechado.")
        await interaction.channel.edit(archived=True, locked=True)

async def setup(bot):
    # É fundamental carregar a Cog de Dados PRIMEIRO
    await bot.add_cog(SistemaDados(bot))
    await bot.add_cog(TicketCog(bot))
    bot.add_view(TicketLayout(bot)) # Persistent view registrada no setup
