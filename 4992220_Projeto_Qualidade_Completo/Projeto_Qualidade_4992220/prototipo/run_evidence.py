"""Executa testes reais no computador e guarda evidências reprodutíveis."""
import hashlib
import json
import math
import platform
import statistics
import tempfile
import threading
import time
import unittest
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from repository import initialize
from api import make_server

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidencias'


class Result(unittest.TextTestResult):
    """Uma linha por método, inclusive quando subtestes e limpeza falham."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = []
        self.current = None

    def startTest(self, test):
        self.started = time.perf_counter()
        self.current = test
        self.status = 'APROVADO'
        self.messages = []
        super().startTest(test)

    def note(self, test, status, message=''):
        # Falhas de setUpClass são informadas sem startTest/stopTest.
        if self.current is not test:
            self.rows.append(dict(id=str(test), description=test.shortDescription(),
                                  status=status, duration_ms=0, error=message))
            return
        priority = {'APROVADO': 0, 'IGNORADO': 1, 'FALHA_ESPERADA': 1, 'FALHOU': 2, 'ERRO': 3}
        if priority[status] > priority[self.status]:
            self.status = status
        if message:
            self.messages.append(message)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.note(test, 'FALHOU', str(err[1]) or err[0].__name__)

    def addError(self, test, err):
        super().addError(test, err)
        self.note(test, 'ERRO', str(err[1]) or err[0].__name__)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            status = 'FALHOU' if issubclass(err[0], test.failureException) else 'ERRO'
            self.note(test, status, f'{subtest}: {str(err[1]) or err[0].__name__}')

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.note(getattr(test, 'test_case', test), 'IGNORADO', reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.note(test, 'FALHA_ESPERADA', str(err[1]) or err[0].__name__)

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.note(test, 'FALHOU', 'Teste marcado como falha esperada passou inesperadamente.')

    def stopTest(self, test):
        method = getattr(test, '_testMethodName', str(test))
        parts = method.split('_')
        self.rows.append(dict(id=parts[1] if len(parts) > 1 else method,
                              description=test.shortDescription(), status=self.status,
                              duration_ms=round((time.perf_counter() - self.started) * 1000, 3),
                              error='\n'.join(self.messages)))
        self.current = None
        super().stopTest(test)


def run_tests(output):
    import tests
    started = datetime.now(timezone.utc).isoformat()
    with (output / 'testes.txt').open('w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    report = dict(timestamp_utc=started, python=platform.python_version(), os=platform.system(),
                  machine=platform.machine(), tests=result.rows, total=result.testsRun,
                  passed=sum(x['status'] == 'APROVADO' for x in result.rows),
                  failures=len(result.failures), errors=len(result.errors),
                  skipped=len(result.skipped), unexpected_successes=len(result.unexpectedSuccesses))
    (output / 'testes.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if not result.wasSuccessful():
        raise SystemExit('Falha na suíte. Consulte evidencias/testes.txt')
    return report


def run_benchmark(requests=200, workers=10):
    from tests import payload
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / 'bench.sqlite3'
        initialize(db, stock=max(10000, requests + 5))
        server = make_server(db)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/api/orders'

            def send(index):
                data = payload(unit='REC' if index % 2 == 0 else 'JPA',
                               items=[dict(sku='suco', qty=1)], key=f'benchmark-{index:06d}')
                start = time.perf_counter()
                error = ''
                try:
                    request = Request(url, data=json.dumps(data).encode(),
                                      headers={'Content-Type': 'application/json',
                                               'Authorization': 'Bearer ' + server.demo_token})
                    with urlopen(request, timeout=30) as response:
                        body = json.loads(response.read())
                        ok = response.status == 201 and body['status'] == 'CONFIRMADO'
                        if not ok:
                            error = f"HTTP {response.status}; estado {body.get('status')}"
                except Exception as ex:
                    ok, error = False, f'{type(ex).__name__}: {ex}'
                return dict(index=index, elapsed_ms=round((time.perf_counter() - start) * 1000, 3),
                            ok=ok, error=error)

            for index in range(5):
                send(requests + index)
            begin = time.perf_counter()
            with ThreadPoolExecutor(max_workers=workers) as pool:
                samples = list(pool.map(send, range(requests)))
            elapsed = time.perf_counter() - begin
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    values = sorted(sample['elapsed_ms'] for sample in samples)
    return dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), requests=requests,
                workers=workers, warmup=5, mean_ms=round(statistics.mean(values), 3),
                p95_ms=values[math.ceil(.95 * requests) - 1], max_ms=max(values),
                duration_s=round(elapsed, 3), throughput_rps=round(requests / elapsed, 2),
                success=sum(sample['ok'] for sample in samples),
                method='HTTP localhost, SQLite local, gateway sem latência; p95 por posto mais próximo; warmup excluído',
                samples=samples)


def main(output=OUT):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = run_tests(output)
    bench = run_benchmark()
    (output / 'desempenho.json').write_text(json.dumps(bench, ensure_ascii=False, indent=2), encoding='utf-8')
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted((ROOT / 'prototipo').glob('*')) if path.suffix in ('.py', '.html')}
    (output / 'fontes_sha256.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(json.dumps({'testes': report['total'], 'aprovados': report['passed'],
                      'benchmark': {key: value for key, value in bench.items() if key != 'samples'}},
                     ensure_ascii=False, indent=2))
    if bench['success'] != bench['requests']:
        raise SystemExit('Falha no ensaio de carga. Consulte evidencias/desempenho.json')


if __name__ == '__main__':
    main()
