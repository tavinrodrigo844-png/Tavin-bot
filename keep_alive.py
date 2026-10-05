from aiohttp import web
import threading

async def handle(request):
    return web.Response(text="Bot está vivo!")

def run_app():
    app = web.Application()
    app.router.add_get('/', handle)
    web.run_app(app, port=8080)

def keep_alive():
    thread = threading.Thread(target=run_app)
    thread.start()
