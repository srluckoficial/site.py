import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import traceback
import json
import threading
from flask import Flask, render_template_string, request, redirect, session

# --- CONFIGURAÇÃO DE ACESSO ---
USER_DASH = "admin"      # Altere seu usuário aqui
PASS_DASH = "jennie123"  # Altere sua senha aqui

# --- CONFIGURAÇÃO DA DASHBOARD (FLASK) ---
app = Flask(__name__)
app.secret_key = 'jennie_secret_key_pro'
bot_instance = None

DASH_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Jennie Bot Dash</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    <meta property="og:title" content="Jennie Oficial - Dashboard">
    <meta property="og:description" content="Painel de controle oficial para gerenciar os comandos da Jennie.">
    
    <meta property="og:image" content="https://cdn.discordapp.com/attachments/1388994505386229931/1463370051775107153/fundo.jpg?ex=69719510&is=69704390&hm=35ca3b1017ddc6e14d7d7b941c8e9d54777c64588cfc4bb6804701d48519b927&">
    
    <meta property="og:url" content="https://jennieoficial.serveo.net">
    <meta name="theme-color" content="#f1a7c1">
    <meta name="twitter:card" content="summary_large_image">

    <style>
        body { background: #36393f; color: white; font-family: 'Segoe UI', sans-serif; padding: 10px; }
        .container { max-width: 600px; margin: auto; background: #2f3136; padding: 25px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        h1 { color: #5865f2; text-align: center; margin-bottom: 20px; }
        
        #searchBar { 
            width: 100%; padding: 12px; margin-bottom: 20px; border-radius: 5px; border: none; 
            background: #40444b; color: white; box-sizing: border-box; font-size: 16px;
        }

        .cmd-row { 
            display: flex; justify-content: space-between; align-items: center; 
            background: #40444b; padding: 15px; margin-bottom: 8px; border-radius: 8px; 
            transition: 0.2s;
        }
        .cmd-row:hover { background: #4f545c; }
        
        .btn-save { 
            background: #43b581; color: white; border: none; width: 100%; 
            padding: 16px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 18px; margin-top: 20px;
        }
        
        .login-box { text-align: center; padding: 20px; }
        .login-input { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; }
        
        input[type="checkbox"] { transform: scale(1.5); cursor: pointer; }
    </style>
</head>

<body>
    <div class="container">
        {% if not logged_in %}
            <div class="login-box">
                <h1>Painel Jennie</h1>
                <form action="/login" method="post">
                    <input type="text" name="user" class="login-input" placeholder="Usuário" required>
                    <input type="password" name="pass" class="login-input" placeholder="Senha" required>
                    <button type="submit" class="btn-save">ENTRAR</button>
                </form>
            </div>
        {% else %}
            <h1>Jennie Commands</h1>
            <input type="text" id="searchBar" onkeyup="filterCommands()" placeholder="🔎 Buscar comando...">
            
            <form action="/update" method="post" id="cmdForm">
                <div id="commandList">
                    {% for comando in comandos %}
                    <div class="cmd-row">
                        <span><strong>/{{ comando.name }}</strong></span>
                        <input type="checkbox" name="{{ comando.name }}" {{ 'checked' if config.get(comando.name, True) }}>
                    </div>
                    {% endfor %}
                </div>
                <button type="submit" class="btn-save">SALVAR ALTERAÇÕES</button>
            </form>
            <p style="text-align:center;"><a href="/logout" style="color:#f04747; text-decoration:none; font-size:12px;">Sair do Painel</a></p>
        {% endif %}
    </div>

    <script>
    function filterCommands() {
        let input = document.getElementById('searchBar').value.toLowerCase();
        let rows = document.getElementsByClassName('cmd-row');
        for (let i = 0; i < rows.length; i++) {
            let name = rows[i].getElementsByTagName('span')[0].innerText.toLowerCase();
            rows[i].style.display = name.includes(input) ? "flex" : "none";
        }
    }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string(DASH_HTML, logged_in=False)
    
    if not os.path.exists('config_bot.json'):
        with open('config_bot.json', 'w') as f: json.dump({}, f)
    
    with open('config_bot.json', 'r') as f:
        config = json.load(f)
    
    cmds = bot_instance.tree.get_commands() if bot_instance else []
    return render_template_string(DASH_HTML, logged_in=True, comandos=cmds, config=config)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('user') == USER_DASH and request.form.get('pass') == PASS_DASH:
        session['logged_in'] = True
    return redirect('/')

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect('/')

@app.route('/update', methods=['POST'])
def update():
    if not session.get('logged_in'): return redirect('/')
    new_config = {}
    if bot_instance:
        for cmd in bot_instance.tree.get_commands():
            new_config[cmd.name] = cmd.name in request.form
    with open('config_bot.json', 'w') as f:
        json.dump(new_config, f, indent=4)
    return redirect('/')

def run_flask(bot):
    global bot_instance
    bot_instance = bot
    app.run(host='0.0.0.0', port=5000)

# --- CLASSE DO BOT ---

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True          
        intents.message_content = True  
        intents.presences = True 
        super().__init__(command_prefix="*", intents=intents, help_command=None)

    async def setup_hook(self):
        print("--- Iniciando carregamento das Cogs ---")
        if not os.path.exists('./cogs'): os.makedirs('./cogs')
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Carregado: {filename}')
                except Exception:
                    traceback.print_exc()

        async def check_dash(interaction: discord.Interaction) -> bool:
            if not os.path.exists('config_bot.json'): return True
            try:
                with open('config_bot.json', 'r') as f:
                    config = json.load(f)
                if not config.get(interaction.command.name, True):
                    await interaction.response.send_message("❌ Este comando está desativado pela Dashboard.", ephemeral=True)
                    return False
                return True
            except: return True

        self.tree.interaction_check = check_dash
        await self.tree.sync()
        print("🚀 Comandos sincronizados!")

    async def on_ready(self):
        print(f'---\n✨ Bot online como: {self.user}\n🟢 Status: Operacional\n---')

async def main():
    bot = MyBot()
    async with bot:
        threading.Thread(target=run_flask, args=(bot,), daemon=True).start()
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot desligado.")
