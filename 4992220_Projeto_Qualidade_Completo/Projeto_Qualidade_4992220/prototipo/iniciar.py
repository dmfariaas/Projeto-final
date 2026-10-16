"""Abre a demonstração e mantém o servidor independente do inicializador."""

import argparse
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import webbrowser

ROOT = Path(__file__).resolve().parent


def demo_ready(port, timeout=0.5):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=timeout)
    try:
        connection.request('GET', '/api/health')
        response = connection.getresponse()
        if response.status != 200:
            return False
        body = json.loads(response.read(4097))
        return (
            isinstance(body, dict)
            and body.get('status') == 'ok'
            and body.get('environment') == 'local-demo'
        )
    except (OSError, http.client.HTTPException, ValueError):
        return False
    finally:
        connection.close()


def port_in_use(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.5):
            return True
    except OSError:
        return False


def stop_started_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def start_server(port, database):
    database.parent.mkdir(parents=True, exist_ok=True)
    log_path = database.parent / f'servidor-{port}.log'
    command = [
        sys.executable,
        '-B',
        '-u',
        str(ROOT / 'api.py'),
        '--port',
        str(port),
        '--db',
        str(database),
    ]
    options = (
        {
            'creationflags': subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP
        }
        if os.name == 'nt'
        else {'start_new_session': True}
    )
    with log_path.open('ab') as log:
        log_start = log.tell()
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
            **options,
        )
    deadline = time.monotonic() + 10
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                with log_path.open('rb') as log:
                    log.seek(log_start)
                    detail = log.read(8192).decode('utf-8', errors='replace').strip()
                raise RuntimeError(
                    f'O servidor não iniciou (código {process.returncode}). '
                    f'Consulte o log: {log_path}' + (f'\n{detail}' if detail else '')
                )
            remaining = deadline - time.monotonic()
            if demo_ready(port, timeout=min(0.5, max(remaining, 0.01))):
                return process.pid, log_path
            time.sleep(min(0.1, max(0, deadline - time.monotonic())))
    except KeyboardInterrupt:
        stop_started_process(process)
        raise
    stop_started_process(process)
    raise RuntimeError(
        f'O servidor não respondeu em 10 segundos. Consulte o log: {log_path}'
    )


def main():
    parser = argparse.ArgumentParser(
        description='Inicia ou abre a demonstração local Raízes do Nordeste.'
    )
    parser.add_argument('--port', type=int, default=8765, help='Porta local (8765).')
    parser.add_argument(
        '--db', default=str(ROOT / 'demo.sqlite3'), help='Caminho do banco SQLite.'
    )
    parser.add_argument(
        '--no-browser', action='store_true', help='Iniciar sem abrir o navegador.'
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('A porta deve estar entre 1 e 65535.')

    url = f'http://127.0.0.1:{args.port}'
    try:
        if demo_ready(args.port):
            print('A demonstração já está em execução. Reutilizando o servidor.')
        elif port_in_use(args.port):
            raise RuntimeError(
                f'A porta {args.port} está ocupada por outro serviço ou por uma '
                'demonstração que ainda não respondeu. Aguarde e tente novamente '
                'ou escolha outra porta com --port. O serviço existente foi preservado.'
            )
        else:
            pid, log_path = start_server(
                args.port, Path(args.db).expanduser().resolve()
            )
            print(f'Servidor iniciado. PID: {pid}')
            print(f'Log: {log_path}')
    except (OSError, RuntimeError) as error:
        parser.exit(1, f'Não foi possível abrir a demonstração.\n{error}\n')
    except KeyboardInterrupt:
        parser.exit(1, 'Inicialização cancelada.\n')

    print(f'Demonstração local: {url}')
    print('Fechar este inicializador não encerra o servidor.')
    if not args.no_browser:
        try:
            if not webbrowser.open(url):
                print('Abra o endereço acima no navegador.')
        except webbrowser.Error:
            print('Abra o endereço acima no navegador.')


if __name__ == '__main__':
    main()
