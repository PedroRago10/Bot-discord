import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import asyncio

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix='!', intents=intents)

# IDs dos canais
channel_ids = {
    'register_channel': 1139579486782886008,
    'non_payment_channel': 1139580250267865168,
    'payment_log_channel': 1130596980230463578,
    'commands_bot_channel': 1140741670598606949,
}

# Variável global para armazenar o valor da meta
meta_value = 0

@tasks.loop(minutes=1)
async def check_non_payments():
    global lista_membros

    print(f"Verificando pagamentos não realizados...")
    now = datetime.now(timezone.utc)
    if now.weekday() == 1 and now.time() == datetime.strptime("00:01", "%H:%M").time():
        payment_log_channel = bot.get_channel(channel_ids['payment_log_channel'])
        mentioned_submitters = []  # Lista de membros que trouxeram pagamentos

        async for message in payment_log_channel.history(limit=None):
            if "Quem trouxe" in message.content:
                mentioned_submitters.append(message.mentions[0])  # Considera apenas o primeiro membro mencionado

        unregistered_members = [member for member in lista_membros if member != bot.user and member not in mentioned_submitters]
        
        if unregistered_members:
            unregistered_list = '\n'.join(member.mention for member in unregistered_members)
            non_payment_channel = bot.get_channel(channel_ids['non_payment_channel'])
            await non_payment_channel.send(f"Os seguintes membros não registraram o farm semanal:\n{unregistered_list}")

# Função para formatar as informações do pagamento
def format_payment_info(submitter, receiver, value):
    return f"Quem trouxe: {submitter}\nQuem Recebeu: {receiver}\nValor: {value}"

# Comando para definir a meta semanal
@bot.command(name='meta')
async def set_meta(ctx, value: float):
    if ctx.channel.id != channel_ids['commands_bot_channel']:
        await ctx.send("Esse comando só pode ser usado no canal de registro de pagamentos.")
        return
    
    global meta_value
    if value <= 0:
        await ctx.send("O valor da meta deve ser maior que zero.")
        return
    
    meta_value = value
    await ctx.send(f"Meta semanal definida como: {meta_value}")
    
# Comando para registrar pagamento (para teste)
@bot.command(name='farm')
async def farm_register(ctx):
    if ctx.channel.id != channel_ids['register_channel']:
        await ctx.send("Esse comando só pode ser usado no canal de registro de pagamentos.")
        return

    # Pergunta o nome de quem realizou o pagamento
    submitter_message = await ctx.send("Por favor, digite o nome de usuário que **realizou** o pagamento:")
    submitter_reponse = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=60)
    submitter = submitter_reponse.content
    await submitter_message.delete()
    await submitter_reponse.delete()
    
    # Pergunta o nome de quem recebeu o pagamento
    receiver_message = await ctx.send("Por favor, digite o nome de usuário de quem **recebeu** o pagamento:")
    receiver_response = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=60)
    receiver = receiver_response.content
    await receiver_message.delete()
    await receiver_response.delete()
    
    # Pergunta o valor do pagamento
    value_message = await ctx.send("Por favor, digite o valor do pagamento:")
    value_response = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=60)
    value = float(value_response.content)
    await value_message.delete()
    await value_response.delete()

    # Verifica se o valor pago é igual ou superior à meta
    if value < meta_value:
        await ctx.send("Valor inferior ao estabelecido para meta semanal de farm.")
        return
    
    payment_info = format_payment_info(submitter, receiver, value)
    
    payment_log_channel = bot.get_channel(channel_ids['payment_log_channel'])
    await payment_log_channel.send(payment_info)
    
    confirmation_message = await ctx.send(f"Seu pagamento, {submitter}, foi registrado com sucesso!")

    # Agora, vamos esperar um pouco antes de apagar a mensagem de confirmação
    await asyncio.sleep(10)  # Espera por 10 segundos
    await confirmation_message.delete()

# Evento de inicialização do bot
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    # Preenche a lista de membros do servidor
    guild = bot.get_guild(1128281997337448498)  # Substitua pelo ID do seu servidor
    lista_membros.extend(guild.members)

    # Inicia a tarefa de verificação de pagamentos não realizados
    check_non_payments.start()

bot.run('SEU_TOKEN_AQUI')
