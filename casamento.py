import discord
from discord.app_commands import Command
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import datetime
import asyncio

class Casamento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.arq_casamentos = "dados_casamentos.json"
        # O sistema agora usa apenas um arquivo para tudo do casamento
        self.dados = self.carregar_casamentos()
        self.verificar_divorcios.start()

    def carregar_casamentos(self):
        if os.path.exists(self.arq_casamentos):
            with open(self.arq_casamentos, "r") as f:
                d = json.load(f)
                # Garante que a nova variável de pontos exista no JSON
                if "pontos_casamento" not in d:
                    d["pontos_casamento"] = {}
                return d
        return {"casais": [], "pontos_casamento": {}}

    def salvar_casamentos(self):
        with open(self.arq_casamentos, "w") as f:
            json.dump(self.dados, f, indent=4)

    def get_pontos(self, user_id):
        # Busca na nova variável dentro do dicionário self.dados
        return self.dados.get("pontos_casamento", {}).get(str(user_id), 0)

    def ajustar_pontos(self, user_id, qtd):
        uid = str(user_id)
        if "pontos_casamento" not in self.dados:
            self.dados["pontos_casamento"] = {}
        
        atual = self.dados["pontos_casamento"].get(uid, 0)
        self.dados["pontos_casamento"][uid] = atual + qtd
        self.salvar_casamentos()

    # --- COMANDO PARA ADM DAR PONTOS DE CASAMENTO ---
    @app_commands.command(name="casamento_setar_pontos", description="Dá pontos de casamento para um usuário (ADM)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setar_pontos(self, interaction: discord.Interaction, usuario: discord.Member, quantidade: int):
        self.ajustar_pontos(usuario.id, quantidade)
        await interaction.response.send_message(f"✅ Definido {quantidade} pontos de casamento para {usuario.mention}.", ephemeral=True)

    @app_commands.command(name="limpar", description="Limpa mensagens do chat")
    async def limpar(self, interaction: discord.Interaction, quantidade: int):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Você não tem permissão.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=quantidade)
        await interaction.followup.send(f"✅ Foram limpas {len(deleted)} mensagens.")

    @app_commands.command(name="casar", description="Peça alguém em casamento (Custo: 500 pontos cada)")
    async def casar(self, interaction: discord.Interaction, conjuge: discord.Member):
        if conjuge.id == interaction.user.id:
            return await interaction.response.send_message("❌ Você não pode casar consigo mesmo!", ephemeral=True)
        
        for casal in self.dados["casais"]:
            if interaction.user.id in casal["membros"] or conjuge.id in casal["membros"]:
                return await interaction.response.send_message("❌ Um de vocês já está casado!", ephemeral=True)

        # Agora ele checa a nova variável pontos_casamento
        if self.get_pontos(interaction.user.id) < 500 or self.get_pontos(conjuge.id) < 500:
            return await interaction.response.send_message(f"❌ Ambos precisam de 500 pontos de casamento!\nSeu saldo: {self.get_pontos(interaction.user.id)}", ephemeral=True)

        embed = discord.Embed(
            title="💍 Pedido de Casamento",
            description=f"{conjuge.mention}, você aceita se casar com {interaction.user.mention}?\n\n**Custo:** 500 pontos de cada.",
            color=0xff69b4
        )
        
        view = discord.ui.View(timeout=60)
        btn = discord.ui.Button(label="Aceitar", style=discord.ButtonStyle.success)
        
        async def callback(it: discord.Interaction):
            if it.user.id != conjuge.id: 
                return await it.response.send_message("❌ Apenas a pessoa pedida pode aceitar!", ephemeral=True)
            
            await it.response.defer()
            self.ajustar_pontos(interaction.user.id, -500)
            self.ajustar_pontos(conjuge.id, -500)
            
            self.dados["casais"].append({
                "membros": [interaction.user.id, conjuge.id],
                "nivel": 2, "xp": 0, "cartinhas_mes": 0,
                "data": datetime.datetime.now().isoformat()
            })
            self.salvar_casamentos()
            await it.followup.send(f"❤️ {interaction.user.mention} e {conjuge.mention} estão casados!")
            view.stop()

        btn.callback = callback
        view.add_item(btn)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="divorciar", description="Termina o casamento (Multa: 200 pontos)")
    async def divorciar(self, interaction: discord.Interaction):
        casal = next((c for c in self.dados["casais"] if interaction.user.id in c["membros"]), None)
        if not casal:
            return await interaction.response.send_message("❌ Você não está casado.", ephemeral=True)

        if self.get_pontos(interaction.user.id) < 200:
            return await interaction.response.send_message("❌ Saldo insuficiente para a multa (200).", ephemeral=True)

        id_x = interaction.user.id
        id_y = casal["membros"][0] if casal["membros"][1] == id_x else casal["membros"][1]
        
        self.ajustar_pontos(id_x, -200)
        self.ajustar_pontos(id_y, 200)
        self.dados["casais"].remove(casal)
        self.salvar_casamentos()
        await interaction.response.send_message(f"💔 <@{id_x}> se separou de <@{id_y}>.")

    @app_commands.command(name="cartinha", description="Envie uma cartinha (200 pontos)")
    async def cartinha(self, interaction: discord.Interaction, mensagem: str):
        await interaction.response.defer(ephemeral=True)
        casal = next((c for c in self.dados["casais"] if interaction.user.id in c["membros"]), None)
        if not casal: return await interaction.followup.send("❌ Não casado.")
        if self.get_pontos(interaction.user.id) < 200: return await interaction.followup.send("❌ Você precisa de 200 pontos de casamento.")

        alvo_id = casal["membros"][0] if casal["membros"][1] == interaction.user.id else casal["membros"][1]
        alvo = self.bot.get_user(alvo_id) or await self.bot.fetch_user(alvo_id)

        try:
            emb = discord.Embed(title="💌 Cartinha de Amor", description=mensagem, color=0xff0000)
            await alvo.send(embed=emb)
        except:
            return await interaction.followup.send("❌ DM fechada do parceiro!")

        self.ajustar_pontos(interaction.user.id, -200)
        xp = 200 if casal["cartinhas_mes"] == 0 else 10
        casal["xp"] += xp
        casal["cartinhas_mes"] += 1
        if casal["xp"] >= 1000:
            casal["nivel"] += 1
            casal["xp"] -= 1000
        self.salvar_casamentos()
        await interaction.followup.send(f"✅ Enviada! +{xp} XP.")

    @app_commands.command(name="casamento_perfil", description="Ver seus pontos e status de casamento")
    async def perfil(self, interaction: discord.Interaction):
        pontos = self.get_pontos(interaction.user.id)
        casal = next((c for c in self.dados["casais"] if interaction.user.id in c["membros"]), None)
        status = "Casado" if casal else "Solteiro"
        
        emb = discord.Embed(title=f"👤 Perfil de {interaction.user.name}", color=0xff69b4)
        emb.add_field(name="Saldo Casamento", value=f"💰 {pontos} pontos")
        emb.add_field(name="Estado Civil", value=status)
        if casal:
            emb.add_field(name="Nível", value=casal["nivel"], inline=True)
            emb.add_field(name="XP", value=f"{casal['xp']}/1000", inline=True)
        
        await interaction.response.send_message(embed=emb)

    @tasks.loop(hours=24)
    async def verificar_divorcios(self):
        if datetime.datetime.now().day == 1:
            canal = self.bot.get_channel(1450279143630442661)
            para_remover = []
            for c in self.dados["casais"]:
                if c["cartinhas_mes"] < 2:
                    para_remover.append(c)
                    if canal: 
                        try: await canal.send(f"💔 O casamento entre <@{c['membros'][0]}> e <@{c['membros'][1]}> acabou por falta de engajamento.")
                        except: pass
                else: c["cartinhas_mes"] = 0
            for r in para_remover: self.dados["casais"].remove(r)
            self.salvar_casamentos()

async def setup(bot):
    await bot.add_cog(Casamento(bot))
