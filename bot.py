from dotenv import load_dotenv
import asyncio
from telethon import TelegramClient, events
import logging
import time
import os
from aiohttp import web

load_dotenv()

# === CONFIGURAÇÕES ===
api_id = int(os.getenv("API_ID") or 0)
api_hash = os.getenv("API_HASH")
source_group = int(os.getenv("SOURCE_GROUP") or 0)
target_group = int(os.getenv("TARGET_GROUP") or 0)
error_group = int(os.getenv("ERROR_GROUP") or 0)
admin_id = int(os.getenv("ADMIN_ID") or 0)

if not api_id or not api_hash or not source_group or not target_group or not error_group or not admin_id:
    raise ValueError("Preencha o arquivo .env com API_ID, API_HASH, SOURCE_GROUP, TARGET_GROUP, ERROR_GROUP e ADMIN_ID.")

# === CONTROLE DE ESTADO ===
espelhamento_ativo = True
cadastre_link = os.getenv("CADASTRE_LINK", "https://novo-link.com")

# === LOGS ===
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logging.getLogger('telethon').setLevel(logging.WARNING)

# === CLIENTE TELEGRAM ===
client = TelegramClient('espelho_basico', api_id, api_hash)
