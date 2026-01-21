import discord
from discord.ext import commands
import asyncio

# 1. Definição da View com LayoutView V2
class PartnerLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None) # Essencial para persistência

    container1 = discord.ui.Container(
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(content="## Bem Vindos ao painel de parceiros "),
        discord.ui.TextDisplay(content="Confira Nossos Requisitos de Parceria:\n- Ter 50 Membros no servidor (Bot não conta);\n- Servidor ativo;\n- Proibido ser servidor NSFW (Prezamos com a segurança de todos)\n- Um membro staff precisa permanecer no nosso servidor, caso contrário a parceria será encerrada; \n- Seu servidor precisa ter um ping de parceria.\n**Por fim, fiquem a vontade para abrir parceria conosco**"),
        discord.ui.ActionRow(
            discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="Seja Parceiro",
                custom_id="btn_be_partner", # ID Fixo
            ),
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(content="Quer receber avisos de novos parceiros? Basta clicar no botão abaixo, para remover basta clicar no botão novamente."),
        discord.ui.ActionRow(
            discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Novos Parceiros",
                custom_id="btn_notify_partner", # ID Fixo
            ),
        ),
        accent_colour=discord.Colour(2067276),
    )

class Parcerias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configurações de IDs
        self.CHANNEL_TICKET_ID = 1453051465366110282
        self.ROLE_STAFF_ID = 1452998249735655505
        self.ROLE_NOTIFY_ID = 1461158465174245571
        
        # Registrar View Persistente
        self.bot.add_view(PartnerLayout())

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id")

        # --- Lógica: Novos Parceiros (Cargo toggle) ---
        if custom_id == "btn_notify_partner":
            role = interaction.guild.get_role(self.ROLE_NOTIFY_ID)
            if not role:
                return await interaction.response.send_message("❌ Cargo de notificações não encontrado.", ephemeral=True)
            
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message("🔔 Você não receberá mais avisos de parcerias.", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("✅ Você agora será notificado sobre novos parceiros!", ephemeral=True)

        # --- Lógica: Seja Parceiro (Ticket em Tópico) ---
        elif custom_id == "btn_be_partner":
            channel = self.bot.get_channel(self.CHANNEL_TICKET_ID)
            if not channel:
                print(f"❌ [ERRO TERMUX] Canal de tickets {self.CHANNEL_TICKET_ID} não encontrado.")
                return await interaction.response.send_message("❌ Erro interno: Canal de parcerias não configurado.", ephemeral=True)

            # --- NOVA TRAVA: Verificação de Ticket Duplicado ---
            # Procuramos nos tópicos ativos e arquivados do canal se já existe um com o nome do usuário
            thread_name = f"Parceria • {interaction.user.name}"
            
            # Verifica nos tópicos ativos
            existing_thread = discord.utils.get(channel.threads, name=thread_name)
            
            if existing_thread and not existing_thread.archived:
                return await interaction.response.send_message(f"⚠️ Você já possui um ticket de parceria aberto! Confira aqui: {existing_thread.mention}", ephemeral=True)

            try:
                # Criar o Tópico com o nome solicitado: Parceria • @nome
                thread = await channel.create_thread(
                    name=thread_name,
                    type=discord.ChannelType.private_thread,
                    auto_archive_duration=1440 
                )

                await thread.add_user(interaction.user)
                
                staff_role = interaction.guild.get_role(self.ROLE_STAFF_ID)
                mention_staff = staff_role.mention if staff_role else "@Staff"
                
                # 1. Envia a marcação e deleta em seguida para notificar sem poluir
                msg_ghost = await thread.send(f"{interaction.user.mention} {mention_staff}")
                await msg_ghost.delete()

                # 2. Envia a mensagem de instrução que fica fixa no tópico
                await thread.send(
                    content=f"👋 **Bem-vindo ao seu ticket de parceria, {interaction.user.mention}!**\n\n"
                            "Por favor, deixe abaixo todas as informações do seu servidor para que nossa equipe possa analisar.\n"
                            "*(Você tem permissão para enviar links e imagens à vontade)*"
                )

                await interaction.response.send_message(f"✅ Seu ticket foi aberto aqui: {thread.mention}", ephemeral=True)
                print(f"✅ [TICKET] Tópico criado: {thread_name}")

            except Exception as e:
                print(f"❌ [ERRO TERMUX] Falha ao criar tópico: {e}")
                await interaction.response.send_message("❌ Não foi possível abrir o ticket. Verifique as permissões do bot.", ephemeral=True)

    @commands.command(name="send_parcerias")
    @commands.has_permissions(administrator=True)
    async def send_partner_panel(self, ctx):
        """Envia o painel de parcerias V2"""
        try:
            view = PartnerLayout()
            await ctx.send(view=view)
            print(f"✅ [SUCESSO] Painel de parcerias enviado no canal: {ctx.channel.name}")
        except Exception as e:
            print(f"❌ [ERRO TERMUX] Erro ao enviar painel: {e}")

async def setup(bot):
    await bot.add_cog(Parcerias(bot))
