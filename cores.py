import discord
from discord import app_commands
from discord.ext import commands

# --- MENU DE SELEÇÃO (DROPDOWN) ---
class ColorDropdown(discord.ui.Select):
    def __init__(self, custom_id, placeholder, options, required_role_id=None):
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options
        )
        self.required_role_id = required_role_id

    async def callback(self, interaction: discord.Interaction):
        # Lista de IDs de todos os cargos de cores para limpeza
        todas_cores = [
            1451051779461615629, 1451051781173022823, 1451051782838030337, 
            1451051786646327356, 1451051784977121373, 1451051760482517043, 
            1451051767646392431, 1451051765276606484, 1451051763795759325, 
            1451051762143330394, 1451051777855066112, 1451051771421134921, 
            1451051775342936134, 1451051769181245451, 1451051773019164799
        ]

        # 1. Responde imediatamente para evitar erro de timeout (Interação não respondeu)
        await interaction.response.defer(ephemeral=True)

        escolhida_id = int(self.values[0])
        role_nova = interaction.guild.get_role(escolhida_id)

        if not role_nova:
            return await interaction.followup.send("❌ Erro: Cargo não encontrado no servidor.", ephemeral=True)

        # --- LOGICA TOGGLE (SE JÁ TIVER A COR, REMOVE) ---
        if role_nova in interaction.user.roles:
            await interaction.user.remove_roles(role_nova)
            return await interaction.followup.send(f"⚠️ Você já estava usando a cor {role_nova.mention}, por isso ela foi **removida**.", ephemeral=True)

        # 2. Verifica se o membro tem o cargo de requisito (Bons Amigos / Melhores Amigos)
        if self.required_role_id:
            role_req = interaction.guild.get_role(self.required_role_id)
            if role_req not in interaction.user.roles:
                return await interaction.followup.send(
                    f"❌ Você precisa do cargo {role_req.mention} para usar estas cores!", 
                    ephemeral=True
                )

        try:
            # 3. Limpeza: Remove qualquer outra cor da lista que o usuário já tenha
            roles_remover = [interaction.guild.get_role(rid) for rid in todas_cores if interaction.guild.get_role(rid)]
            roles_atuais = [r for r in roles_remover if r in interaction.user.roles]
            
            if roles_atuais:
                await interaction.user.remove_roles(*roles_atuais)

            # 4. Adiciona a nova cor selecionada
            await interaction.user.add_roles(role_nova)
            await interaction.followup.send(f"✅ Cor {role_nova.mention} aplicada com sucesso!", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao processar os cargos: {e}", ephemeral=True)

# --- VIEW QUE ORGANIZA OS MENUS ---
class ColorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout None para o menu não parar de funcionar

        # Menu 1: Cores Normais
        self.add_item(ColorDropdown("m_mortas", "💀 Cores Disponíveis", [
            discord.SelectOption(label="Cinza Azulado", value="1451051779461615629"),
            discord.SelectOption(label="Rosa Desbotado", value="1451051781173022823"),
            discord.SelectOption(label="Bege Areia", value="1451051782838030337"),
            discord.SelectOption(label="Roxo Acinzentado", value="1451051786646327356"),
            discord.SelectOption(label="Verde Olivia", value="1451051784977121373"),
        ]))

        # Menu 2: Cores para Bons Amigos
        self.add_item(ColorDropdown("m_escuras", "🌑 Cores p/ Bons Amigos", [
            discord.SelectOption(label="Azul Noturno", value="1451051760482517043"),
            discord.SelectOption(label="Roxo Drácula", value="1451051767646392431"),
            discord.SelectOption(label="Verde Floresta", value="1451051765276606484"),
            discord.SelectOption(label="Vinho Profundo", value="1451051763795759325"),
            discord.SelectOption(label="Cinza Grafite", value="1451051762143330394"),
        ], required_role_id=1449814259210129490))

        # Menu 3: Cores para Melhores Amigos
        self.add_item(ColorDropdown("m_claras", "✨ Cores p/ Melhores Amigos", [
            discord.SelectOption(label="Lavanda", value="1451051777855066112"),
            discord.SelectOption(label="Rosa Pastel", value="1451051771421134921"),
            discord.SelectOption(label="Amarelo Creme", value="1451051775342936134"),
            discord.SelectOption(label="Azul Céu Suave", value="1451051769181245451"),
            discord.SelectOption(label="Verde Menta", value="1451051773019164799"),
        ], required_role_id=1449811969111490761))

# --- COG DO DISCORD ---
class ColorPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cores", description="Envia o painel de seleção de cores")
    @app_commands.default_permissions(administrator=True)
    async def enviar_painel_cores(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎨 Central de Cores",
            description=(
                "**Cores Públicas**\n"
                "<@&1451051779461615629> | <@&1451051781173022823> | <@&1451051782838030337>\n"
                "<@&1451051786646327356> | <@&1451051784977121373>\n\n"
                "**Exclusivas para Bons Amigos**\n"
                "<@&1451051760482517043> | <@&1451051767646392431> | <@&1451051765276606484>\n"
                "<@&1451051763795759325> | <@&1451051762143330394>\n\n"
                "**Exclusivas para Melhores Amigos**\n"
                "<@&1451051777855066112> | <@&1451051771421134921> | <@&1451051775342936134>\n"
                "<@&1451051769181245451> | <@&1451051773019164799>\n\n"
                "💡 *Clique novamente na mesma cor para removê-la.*"
            ),
            color=0x2b2d31
        )
        
        # Envia a mensagem no canal e a View (menus)
        await interaction.channel.send(embed=embed, view=ColorView())
        # Responde ao comando slash de forma privada
        await interaction.response.send_message("✅ Painel de cores enviado com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ColorPanel(bot))
