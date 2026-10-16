"""Servidor de demonstração restrito a 127.0.0.1. Não publicar em produção."""
import argparse
import json
import os
import secrets
import socket
import sqlite3
import webbrowser
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from domain import RuleError
from service import OrderService

class LocalHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = os.name != 'nt'
    allow_reuse_port = False

    def server_bind(self):
        if os.name == 'nt':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

def make_server(path, port=0):
    service = OrderService(path)
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def send(self, code, value, mime='application/json; charset=utf-8'):
            raw = (json.dumps(value, ensure_ascii=False).encode()
                   if mime.startswith('application/json') else value.encode())
            try:
                self.send_response(code)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(raw)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('X-Frame-Options', 'DENY')
                self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
                self.end_headers()
                self.wfile.write(raw)
            except ConnectionError:
                # O pedido pode estar salvo. A mesma chave recupera o resultado na nova tentativa.
                self.close_connection = True

        def read_json(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
            except ValueError as error:
                raise RuleError('JSON_INVALIDO', 'JSON inválido.', 400) from error
            if not 0 < size <= 16384:
                raise RuleError('TAMANHO_INVALIDO', 'Corpo vazio ou maior que 16 KB.', 413)

            body = self.rfile.read(size)
            if len(body) != size:
                raise RuleError('JSON_INVALIDO', 'JSON inválido.', 400)
            try:
                return json.loads(body)
            except (ValueError, UnicodeDecodeError) as error:
                raise RuleError('JSON_INVALIDO', 'JSON inválido.', 400) from error

        def error(self, ex):
            self.send(ex.status,dict(code=ex.code,message=ex.message))
        def unavailable(self):
            self.send(503,{'code':'SERVICO_INDISPONIVEL','message':'Não foi possível acessar os dados locais. Tente novamente em instantes.'})
        def authorized(self):
            provided = self.headers.get('Authorization','')
            return secrets.compare_digest(provided.encode('utf-8'),('Bearer '+token).encode('utf-8'))
        def do_GET(self):
            url=urlparse(self.path)
            try:
                if url.path=='/':
                    html=(Path(__file__).parent/'index.html').read_text(encoding='utf-8').replace('__DEMO_TOKEN__',token)
                    return self.send(200,html,'text/html; charset=utf-8')
                if url.path=='/api/health':
                    return self.send(200,{'status':'ok','environment':'local-demo'})
                if url.path=='/api/catalog':
                    return self.send(200,service.catalog(parse_qs(url.query).get('unit',['REC'])[0]))
                parts = url.path.strip('/').split('/')
                if len(parts)==3 and parts[:2]==['api','orders']:
                    if not self.authorized():
                        return self.send(401,{'code':'NAO_AUTORIZADO','message':'Sessão de demonstração inválida.'})
                    return self.send(200,service.get(parts[2],{'id':'cliente-demo','role':'customer'}))
                self.send(404,{'code':'ROTA_INVALIDA','message':'Página não encontrada.'})
            except RuleError as ex:
                self.error(ex)
            except (sqlite3.Error,OSError):
                self.unavailable()
        def do_POST(self):
            path=urlparse(self.path).path
            parts=path.strip('/').split('/')
            is_payment=len(parts)==4 and parts[:2]==['api','orders'] and parts[3]=='payment'
            if path!='/api/orders' and not is_payment:
                return self.send(404,{'code':'ROTA_INVALIDA','message':'Rota não encontrada.'})
            if not self.authorized():
                return self.send(401,{'code':'NAO_AUTORIZADO','message':'Sessão de demonstração inválida.'})
            try:
                try:
                    data = self.read_json()
                except ConnectionError:
                    self.close_connection = True
                    return
                if is_payment:
                    result,replayed=service.resolve_payment(parts[2],data,owner='cliente-demo')
                else:
                    result,replayed=service.create(data)
                self.send(200 if is_payment or replayed else 201,{**result,'replayed':replayed})
            except RuleError as ex:
                self.error(ex)
            except (sqlite3.Error,OSError):
                self.unavailable()
    server=LocalHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True
    server.demo_token=token
    server.order_service=service
    return server

def demo_is_running(port):
    connection = HTTPConnection('127.0.0.1', port, timeout=1)
    try:
        connection.request('GET', '/api/health')
        response = connection.getresponse()
        return response.status == 200 and json.loads(response.read(1024)) == {
            'status': 'ok', 'environment': 'local-demo'
        }
    except (OSError, ValueError, HTTPException):
        return False
    finally:
        connection.close()

def open_demo_browser(url):
    try:
        webbrowser.open(url)
    except webbrowser.Error:
        print('Abra o endereço acima no navegador.', flush=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--db',default=str(Path(__file__).parent/'demo.sqlite3'))
    parser.add_argument('--open-browser',action='store_true',help='Abrir a demonstração no navegador.')
    args=parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('A porta deve estar entre 0 e 65535.')
    try:
        server=make_server(args.db,args.port)
    except OSError:
        if args.open_browser and args.port > 0 and demo_is_running(args.port):
            url=f'http://127.0.0.1:{args.port}'
            print(f'Demonstração já está em execução: {url}',flush=True)
            open_demo_browser(url)
            return
        parser.exit(1,f'Não foi possível abrir a porta {args.port}. Outro programa pode estar usando esse endereço. Use --port 8766 para escolher outra porta.\n')
    except sqlite3.Error:
        parser.exit(1,'Não foi possível abrir o banco local. Verifique a pasta indicada em --db e a permissão de escrita.\n')
    url=f'http://127.0.0.1:{server.server_port}'
    print(f'Demonstração local: {url}',flush=True)
    if args.open_browser:
        open_demo_browser(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__=='__main__':
    main()
