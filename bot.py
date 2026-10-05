import asyncio
from telethon import TelegramClient, events
import logging
import time
import os
from aiohttp import web  # ← Adicionado para o servidor web

# === CONFIGURAÇÕES ===
api_id = int(os.getenv("API_ID", 20255878))
api_hash = os.getenv("API_HASH", '533837f337a7a7754f7d949529f45ae0')
source_group = int(os.getenv("SOURCE_GROUP", -1001915757750))
target_group = int(os.getenv("TARGET_GROUP", -1002603645290))
error_group = int(os.getenv("ERROR_GROUP", -1002670485069))
admin_id = int(os.getenv("ADMIN_ID", 6885313506))

# === CONTROLE DE ESTADO ===
espelhamento_ativo = True
cadastre_link = "https://novo-link.com"

# === LOGS ===
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logging.getLogger('telethon').setLevel(logging.WARNING)

# === CLIENTE TELEGRAM ===
client = TelegramClient('espelho_basico', api_id, api_hash)

# === FILA DE EXCLUSÃO ===
delete_queue = asyncio.Queue()

# === FUNÇÃO PARA NOTIFICAR ERROS ===
async def notify_error(message):
    try:
        await client.send_message(error_group, f"❗ **Erro no Bot** ❗\n\n{message}")
    except Exception as e:
        logging.error(f"Erro ao notificar erro: {e}")

# === TRABALHADOR DE EXCLUSÃO ===
async def delete_worker():
    while True:
        target_group_id, msg_id, delay = await delete_queue.get()
        try:
            await asyncio.sleep(delay)
            await client.delete_messages(target_group_id, msg_id)
            logging.info(f"🗑️ Mensagem {msg_id} apagada após {delay}s.")
        except Exception as e:
            logging.error(f"Erro ao apagar mensagem {msg_id}: {e}")
            await notify_error(f"Erro ao apagar mensagem {msg_id}: {e}")
        finally:
            delete_queue.task_done()

# === PROCESSADOR DE MENSAGENS ===
async def process_message(event):
    if not espelhamento_ativo:
        return

    try:
        tempo_total_inicio = time.perf_counter()

        tempo_recebimento = time.perf_counter()
        conteudo = event.message.message
        if not conteudo:
            return

        conteudo = conteudo.strip()
        texto_limpo = ''.join(conteudo.split())
        tempo_pos_processamento = time.perf_counter()

        if "CADASTRE-SE AQUI" in conteudo:
            conteudo = conteudo.replace(
                "CADASTRE-SE AQUI",
                f"[CADASTRE-SE AQUI]({cadastre_link})"
            )

        tempo_pre_envio = time.perf_counter()

        mensagem = await client.send_message(
            target_group,
            conteudo,
            parse_mode='md',
            link_preview=False
        )

        tempo_pos_envio = time.perf_counter()

        if "ATENÇÃO, POSSÍVEL ENTRADA" in texto_limpo:
            await delete_queue.put((target_group, mensagem.id, 30))
        elif any(p in texto_limpo for p in ["Gale1", "Gale2"]) and "TenhaGerenciamento" in texto_limpo:
            await delete_queue.put((target_group, mensagem.id, 25))
        elif "PADRÕESNÃOENCONTRADOS" in texto_limpo:
            await delete_queue.put((target_group, mensagem.id, 15))
        elif "✨Voltemaistrarde!" in texto_limpo:
            await delete_queue.put((target_group, mensagem.id, 10))

        tempo_total_fim = time.perf_counter()

        logging.info(f"""⏱️ Tempo:
        • Recebimento -> Processamento: {(tempo_pos_processamento - tempo_recebimento):.3f}s
        • Processamento -> Envio: {(tempo_pre_envio - tempo_pos_processamento):.3f}s
        • Envio -> Pós-envio: {(tempo_pos_envio - tempo_pre_envio):.3f}s
        • Tempo total: {(tempo_total_fim - tempo_total_inicio):.3f}s
        """)

    except Exception as e:
        msg = f"Erro ao processar mensagem:\n{str(e)}"
        logging.error(msg)
        await notify_error(msg)

# === HANDLER DE MENSAGENS DO GRUPO ===
@client.on(events.NewMessage(chats=source_group))
async def handler(event):
    asyncio.create_task(process_message(event))

# === COMANDOS PRIVADOS ===
@client.on(events.NewMessage(from_users=admin_id, func=lambda e: e.is_private))
async def command_handler(event):
    global espelhamento_ativo, cadastre_link
    text = event.raw_text.strip().lower()

    if text == "/pausar":
        espelhamento_ativo = False
        await event.respond("⏸️ Sinais pausado com sucesso.")
    elif text == "/retomar":
        espelhamento_ativo = True
        await event.respond("▶️ Sinais retomado com sucesso.")
    elif text.startswith("/link"):
        new_link = text.split(' ', 1)[1] if len(text.split(' ', 1)) > 1 else None
        if new_link:
            cadastre_link = new_link
            await event.respond(f"🔗 Link de cadastro alterado para: {cadastre_link}")
        else:
            await event.respond("⚠️ Por favor, forneça um link após o comando. Exemplo: /link https://novo-link.com")
    elif text == "/status":
        status = "ativo" if espelhamento_ativo else "pausado"
        await event.respond(f"✅ Status do bot: {status}\n🔗 Link de cadastro: {cadastre_link}")
    elif text == "/ajuda":
        await event.respond("""🛠️ **Comandos disponíveis:**\n
/pausar – Pausa o envio de sinais.
/retomar – Retoma o envio de sinais.
/status – Mostra o status atual e o link de cadastro.
/link <URL> – Altera o link de cadastro usado nas mensagens.
/ajuda – Exibe esta lista de comandos.

⚙️ Envie os comandos aqui no chat privado com o bot.""")
    else:
        await event.respond("❓ Comando não reconhecido. Use /ajuda para ver os comandos disponíveis.")

# === SERVIDOR WEB PARA O RENDER DETECTAR ===
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", lambda request: web.Response(text="Bot rodando!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# === EXECUÇÃO ===
async def main():
    await client.start()
    asyncio.create_task(delete_worker())
    asyncio.create_task(start_web_server())  # ← Servidor web iniciado
    logging.info("✅ Bot iniciado e executando.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
