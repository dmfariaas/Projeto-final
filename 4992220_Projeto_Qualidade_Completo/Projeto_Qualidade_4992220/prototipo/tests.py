import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from domain import RuleError,normalize,totals,CHANNELS
from repository import connect
from service import OrderService
from api import make_server

def payload(**kwargs):
    data=dict(unit='REC',channel='WEB',items=[{'sku':'baiao','qty':2},{'sku':'suco','qty':1}],coupon='RAIZES10',loyalty=True,payment='approved',key='pedido-0001')
    data.update(kwargs)
    return data

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'test.sqlite3'
        self.svc=OrderService(self.path,stock=10)
    def tearDown(self):
        self.tmp.cleanup()
    def value(self,sql,args=()):
        with connect(self.path) as db:
            return db.execute(sql,args).fetchone()[0]
    def expect(self,code,data):
        with self.assertRaises(RuleError) as ctx:
            self.svc.create(data)
        self.assertEqual(ctx.exception.code,code)

class UnitTests(unittest.TestCase):
    def test_TU01_discount_and_points(self):
        """TU01 | Valores exatos: 5800 - 580 = 5220 centavos; 52 pontos."""
        self.assertEqual(totals(normalize(payload())),(5800,580,5220,52))
    def test_TU02_no_coupon(self):
        """TU02 | Sem cupom e sem fidelidade: total 5800 e zero pontos."""
        self.assertEqual(totals(normalize(payload(coupon='',loyalty=False))),(5800,0,5800,0))
    def test_TU03_quantity_boundaries(self):
        """TU03 | Aceitar 1 e 10; rejeitar 0, -1, 11, 1.5, string e booleano."""
        for qty in (1,10):
            self.assertEqual(normalize(payload(items=[dict(sku='suco',qty=qty)]))['items'][0]['qty'],qty)
        for qty in (0,-1,11,1.5,'2',True):
            with self.subTest(qty=qty),self.assertRaises(RuleError):
                normalize(payload(items=[dict(sku='suco',qty=qty)]))
    def test_TU04_duplicate_product(self):
        """TU04 | Produto repetido deve ser rejeitado antes do cálculo."""
        with self.assertRaises(RuleError):
            normalize(payload(items=[dict(sku='suco',qty=1),dict(sku='suco',qty=2)]))
    def test_TU05_key_validation(self):
        """TU05 | Rejeitar chave vazia, curta, excessiva ou com aspas."""
        for key in ('','abc','a'*81,"pedido-'xxx"):
            with self.subTest(key=key),self.assertRaises(RuleError):normalize(payload(key=key))
    def test_TU06_input_allowlist(self):
        """TU06 | Campos extras e corpo não estruturado são rejeitados."""
        for data in (None,[],payload(cpf='00000000000'),payload(loyalty='sim'),payload(payment='real')):
            with self.subTest(data=data),self.assertRaises(RuleError):normalize(data)

class SystemTests(Base):
    def setUp(self):
        super().setUp()
        self.server=make_server(self.path)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        server=self.server
        class Remote:
            @property
            def gateway(self):return server.order_service.gateway
            @gateway.setter
            def gateway(self,value):server.order_service.gateway=value
            def create(self,data):
                req=Request(f'http://127.0.0.1:{server.server_port}/api/orders',data=json.dumps(data).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+server.demo_token})
                try:
                    with urlopen(req,timeout=5) as response:out=json.loads(response.read())
                except HTTPError as ex:
                    out=json.loads(ex.read());raise RuleError(out['code'],out['message'],ex.code)
                replay=out.pop('replayed')
                return out,replay
            def get(self,oid,actor):return server.order_service.get(oid,actor)
        self.svc=Remote()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();super().tearDown()
    def test_TS01_channels(self):
        """TS01 | Aprovar pedido em APP, WEB, TOTEM, BALCAO e PICKUP."""
        for i,channel in enumerate(CHANNELS):
            with self.subTest(channel=channel):
                result,_=self.svc.create(payload(channel=channel,key=f'canal-{i:04d}'))
                self.assertEqual((result['status'],result['channel'],result['total']),('CONFIRMADO',channel,5220))
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),0)
    def test_TS02_declined(self):
        """TS02 | Recusa não altera estoque nem concede pontos."""
        r,_=self.svc.create(payload(payment='declined'))
        self.assertEqual((r['status'],r['points']),('RECUSADO',0))
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),10)
        self.assertEqual(self.value('SELECT COUNT(*) FROM points'),0)
    def test_TS03_timeout(self):
        """TS03 | Timeout fica pendente; repetição preserva o mesmo pedido."""
        first,_=self.svc.create(payload(payment='timeout'))
        second,replay=self.svc.create(payload(payment='timeout'))
        self.assertEqual(first,second);self.assertTrue(replay)
        self.assertEqual(first['status'],'PENDENTE')
        self.assertEqual(first['points'],0)
        self.assertEqual(self.value('SELECT COUNT(*) FROM points'),0)
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),1)
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),60)
    def test_TS04_replay(self):
        """TS04 | Repetir pedido confirmado gera um pedido, 52 pontos e um evento."""
        first,_=self.svc.create(payload())
        for _ in range(5):self.assertEqual(self.svc.create(payload())[0],first)
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),1)
        self.assertEqual(self.value('SELECT balance FROM points'),52)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),1)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),8)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='suco'"),9)
    def test_TS05_changed_replay(self):
        """TS05 | Mesma chave com conteúdo alterado retorna conflito."""
        self.svc.create(payload())
        self.expect('CHAVE_REUTILIZADA',payload(coupon=''))
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),1)
    def test_TS06_out_of_stock(self):
        """TS06 | Pedido maior que estoque restante falha sem alteração parcial."""
        self.svc.create(payload(items=[dict(sku='baiao',qty=10)]))
        self.expect('SEM_ESTOQUE',payload(key='pedido-0002'))
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='suco'"),10)
    def test_TS07_units(self):
        """TS07 | Compra em Recife preserva estoque da unidade João Pessoa."""
        self.svc.create(payload())
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='JPA' AND sku='baiao'"),10)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),8)
    def test_TS08_without_loyalty(self):
        """TS08 | Compra sem fidelidade confirma com zero pontos."""
        r,_=self.svc.create(payload(loyalty=False))
        self.assertEqual((r['status'],r['points']),('CONFIRMADO',0))
    def test_TS09_invalid_coupon(self):
        """TS09 | Cupom inexistente não cria pedido nem reduz estoque."""
        self.expect('CUPOM_INVALIDO',payload(coupon='DESCONTO999'))
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),0)
    def test_TS10_zero_quantity(self):
        """TS10 | Quantidade zero retorna QUANTIDADE_INVALIDA."""
        self.expect('QUANTIDADE_INVALIDA',payload(items=[dict(sku='suco',qty=0)]))
    def test_TS11_empty_cart(self):
        """TS11 | Carrinho vazio retorna CARRINHO_INVALIDO."""
        self.expect('CARRINHO_INVALIDO',payload(items=[]))
    def test_TS12_invalid_unit_channel(self):
        """TS12 | Unidade ou canal desconhecido é rejeitado."""
        self.expect('UNIDADE_INVALIDA',payload(unit='XYZ'))
        self.expect('CANAL_INVALIDO',payload(channel='SMS'))
    def test_TS13_invalid_product(self):
        """TS13 | Produto inexistente e tentativa de injeção não alteram o banco."""
        self.expect('PRODUTO_INVALIDO',payload(items=[dict(sku="'; DROP TABLE orders;--",qty=1)]))
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),0)
    def test_TS14_persistence(self):
        """TS14 | Nova instância recupera pedido e reconhece sua chave."""
        old,_=self.svc.create(payload())
        new,replay=OrderService(self.path).create(payload())
        self.assertTrue(replay);self.assertEqual(old,new)
    def test_TS15_cross_unit_loyalty(self):
        """TS15 | Fidelidade acumula 104 pontos em duas unidades sem duplicação."""
        self.svc.create(payload())
        self.svc.create(payload(unit='JPA'))
        self.assertEqual(self.value('SELECT balance FROM points'),104)
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),2)
    def test_TS16_gateway_rollback(self):
        """TS16 | Resposta inválida do gateway desfaz a transação integralmente."""
        class BadGateway:
            def authorize(self,*args):return 'INVALIDO'
        self.svc.gateway=BadGateway()
        self.expect('GATEWAY_INVALIDO',payload())
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),0)
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),60)
    def test_TS17_events(self):
        """TS17 | Cada resultado cria um evento sem identificador de cliente ou payload."""
        for i,mode in enumerate(('approved','declined','timeout')):
            self.svc.create(payload(key=f'evento-{i:04d}',payment=mode))
        with connect(self.path) as db:
            rows=[dict(r) for r in db.execute('SELECT * FROM events')]
        self.assertEqual(len(rows),3)
        self.assertTrue(all(set(r)=={'seq','order_id','unit','status','created'} for r in rows))
        self.assertEqual({r['status'] for r in rows},{'CONFIRMADO','RECUSADO','PENDENTE'})
    def test_TS18_get_missing(self):
        """TS18 | Consultar pedido inexistente retorna 404."""
        with self.assertRaises(RuleError) as ctx:self.svc.get('missing',dict(id='cliente-demo',role='customer'))
        self.assertEqual(ctx.exception.status,404)

class SecurityTests(Base):
    def test_SE01_customer_isolation(self):
        """SE01 | Outro cliente não acessa pedido alheio."""
        r,_=self.svc.create(payload(),owner='cliente-A')
        with self.assertRaises(RuleError) as ctx:self.svc.get(r['id'],dict(id='cliente-B',role='customer'))
        self.assertEqual(ctx.exception.status,403)
        self.assertEqual(self.svc.get(r['id'],dict(id='cliente-A',role='customer')),r)
    def test_SE02_operator_isolation(self):
        """SE02 | Operador da unidade incorreta recebe 403; unidade correta consulta."""
        r,_=self.svc.create(payload())
        with self.assertRaises(RuleError) as ctx:self.svc.get(r['id'],dict(id='op-2',role='operator',unit='JPA'))
        self.assertEqual(ctx.exception.status,403)
        self.assertEqual(self.svc.get(r['id'],dict(id='op-1',role='operator',unit='REC')),r)

class ConcurrencyTests(Base):
    def test_CC01_same_key(self):
        """CC01 | 50 tentativas concorrentes com a mesma chave geram um pedido."""
        with ThreadPoolExecutor(max_workers=20) as pool:results=list(pool.map(lambda _:self.svc.create(payload()),range(50)))
        self.assertEqual(len({r[0]['id'] for r in results}),1)
        self.assertEqual(sum(not r[1] for r in results),1)
        self.assertEqual(self.value('SELECT balance FROM points'),52)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),8)
    def test_CC02_last_units(self):
        """CC02 | 50 tentativas disputam dez unidades: dez aprovações e quarenta recusas de estoque."""
        def request(i):
            try:return self.svc.create(payload(key=f'concorrencia-{i}',items=[dict(sku='baiao',qty=1)]))[0]['status']
            except RuleError as ex:return ex.code
        with ThreadPoolExecutor(max_workers=20) as pool:results=list(pool.map(request,range(50)))
        self.assertEqual(results.count('CONFIRMADO'),10)
        self.assertEqual(results.count('SEM_ESTOQUE'),40)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),0)

class PaymentResolutionTests(Base):
    def pending(self, **kwargs):
        return self.svc.create(payload(payment='timeout', **kwargs))[0]

    def test_PR01_approved_once_and_restored_context(self):
        """PR01 | Aprovar pendência reduz estoque e soma pontos uma vez; consulta recupera os itens."""
        pending=self.pending()
        self.assertEqual(pending['items'],payload()['items'])
        self.assertEqual((pending['coupon'],pending['loyalty']),('RAIZES10',True))
        result,replayed=self.svc.resolve_payment(pending['id'],{'payment':'approved'})
        self.assertFalse(replayed)
        self.assertEqual((result['status'],result['total'],result['points']),('CONFIRMADO',5220,52))
        for _ in range(3):
            self.assertEqual(self.svc.resolve_payment(pending['id'],{'payment':'approved'}),(result,True))
        self.assertEqual(self.svc.create(payload(payment='timeout')),(result,True))
        self.assertEqual(self.svc.get(pending['id'],dict(id='cliente-demo',role='customer')),result)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),8)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='suco'"),9)
        self.assertEqual(self.value('SELECT balance FROM points'),52)
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),1)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),2)

    def test_PR02_declined_once(self):
        """PR02 | Recusar pendência e repetir a recusa preserva estoque e pontos."""
        pending=self.pending()
        result,replayed=self.svc.resolve_payment(pending['id'],{'payment':'declined'})
        self.assertFalse(replayed)
        self.assertEqual((result['status'],result['points']),('RECUSADO',0))
        self.assertEqual(self.svc.resolve_payment(pending['id'],{'payment':'declined'}),(result,True))
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),60)
        self.assertEqual(self.value('SELECT COUNT(*) FROM points'),0)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),2)

    def test_PR03_terminal_decision_cannot_change(self):
        """PR03 | Uma decisão terminal não pode ser invertida, inclusive em pedidos sem pendência."""
        for index,(decision,opposite) in enumerate((('approved','declined'),('declined','approved'))):
            with self.subTest(decision=decision):
                terminal,_=self.svc.create(payload(payment=decision,key=f'terminal-{index}'))
                self.assertEqual(self.svc.resolve_payment(terminal['id'],{'payment':decision}),(terminal,True))
                with self.assertRaises(RuleError) as ctx:
                    self.svc.resolve_payment(terminal['id'],{'payment':opposite})
                self.assertEqual((ctx.exception.status,ctx.exception.code),(409,'PAGAMENTO_JA_CONFERIDO'))
                self.assertEqual(self.svc.get(terminal['id'],dict(id='cliente-demo',role='customer')),terminal)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),2)

    def test_PR04_concurrent_approval(self):
        """PR04 | Vinte aprovações simultâneas da mesma pendência têm um único efeito."""
        pending=self.pending()
        with ThreadPoolExecutor(max_workers=10) as pool:
            results=list(pool.map(lambda _:self.svc.resolve_payment(pending['id'],{'payment':'approved'}),range(20)))
        self.assertEqual(sum(not replayed for _,replayed in results),1)
        self.assertTrue(all(result['status']=='CONFIRMADO' for result,_ in results))
        self.assertEqual(self.value('SELECT balance FROM points'),52)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),8)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),2)

    def test_PR05_concurrent_opposite_decisions(self):
        """PR05 | Aprovação e recusa concorrentes encerram a pendência com uma única decisão."""
        pending=self.pending()
        barrier=threading.Barrier(2)
        def decide(mode):
            barrier.wait(timeout=5)
            try:return self.svc.resolve_payment(pending['id'],{'payment':mode})[0]['status']
            except RuleError as ex:return ex.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(decide,('approved','declined')))
        self.assertEqual(results.count('PAGAMENTO_JA_CONFERIDO'),1)
        result=self.svc.get(pending['id'],dict(id='cliente-demo',role='customer'))
        self.assertIn(result['status'],('CONFIRMADO','RECUSADO'))
        approved=result['status']=='CONFIRMADO'
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),57 if approved else 60)
        self.assertEqual(self.value('SELECT COALESCE(SUM(balance),0) FROM points'),52 if approved else 0)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),2)

    def test_PR06_pending_orders_compete_for_stock(self):
        """PR06 | Duas pendências disputam as últimas dez unidades sem venda acima do estoque."""
        orders=[self.pending(key=f'pendente-{index}',items=[dict(sku='baiao',qty=10)]) for index in range(2)]
        def approve(order):
            try:return self.svc.resolve_payment(order['id'],{'payment':'approved'})[0]['status']
            except RuleError as ex:return ex.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(approve,orders))
        self.assertCountEqual(results,['CONFIRMADO','SEM_ESTOQUE'])
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),0)
        self.assertEqual(self.value("SELECT COUNT(*) FROM orders WHERE status='PENDENTE'"),1)
        self.assertEqual(self.value('SELECT balance FROM points'),225)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),3)

    def test_PR07_stock_changes_allow_decline_without_partial_effects(self):
        """PR07 | Falta de estoque mantém pendência sem baixa parcial e permite recusa posterior."""
        pending=self.pending()
        self.svc.create(payload(key='consumir-suco',items=[dict(sku='suco',qty=10)],loyalty=False))
        with self.assertRaises(RuleError) as ctx:
            self.svc.resolve_payment(pending['id'],{'payment':'approved'})
        self.assertEqual((ctx.exception.status,ctx.exception.code),(409,'SEM_ESTOQUE'))
        self.assertEqual(self.svc.get(pending['id'],dict(id='cliente-demo',role='customer'))['status'],'PENDENTE')
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),10)
        self.assertEqual(self.value('SELECT COALESCE(SUM(balance),0) FROM points'),0)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),2)
        self.assertEqual(self.svc.resolve_payment(pending['id'],{'payment':'declined'})[0]['status'],'RECUSADO')
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),3)

    def test_PR08_owner_isolation_and_missing_order(self):
        """PR08 | Somente o proprietário confere a pendência; pedido inexistente retorna 404."""
        pending,_=self.svc.create(payload(payment='timeout'),owner='outro-cliente')
        with self.assertRaises(RuleError) as ctx:
            self.svc.resolve_payment(pending['id'],{'payment':'approved'})
        self.assertEqual((ctx.exception.status,ctx.exception.code),(403,'ACESSO_NEGADO'))
        with self.assertRaises(RuleError) as ctx:
            self.svc.resolve_payment('inexistente',{'payment':'approved'})
        self.assertEqual(ctx.exception.status,404)
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),60)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),1)

    def test_PR09_payment_allowlist(self):
        """PR09 | A conferência aceita apenas o campo payment com approved ou declined."""
        pending=self.pending()
        for data in (None,[],{},'approved',{'payment':'timeout'},{'payment':True},{'payment':[]},
                     {'payment':'approved','owner':'outro-cliente'},{'payment':'declined','total':0}):
            with self.subTest(data=data),self.assertRaises(RuleError) as ctx:
                self.svc.resolve_payment(pending['id'],data)
            self.assertEqual((ctx.exception.status,ctx.exception.code),(422,'PAGAMENTO_INVALIDO'))
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),1)
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),60)

    def test_PR10_legacy_database_migration(self):
        """PR10 | Migração preserva dados; pendência antiga permite recusa e impede aprovação sem itens salvos."""
        self.svc.create(payload())
        pending=self.pending(key='legado-pendente')
        legacy={key:value for key,value in pending.items() if key not in ('items','coupon','loyalty')}
        with connect(self.path) as db:
            db.execute('DROP TABLE order_requests')
            db.execute('UPDATE orders SET payload=? WHERE id=?',(json.dumps(legacy),pending['id']))
        self.svc=OrderService(self.path,stock=999)
        self.assertEqual(self.value('SELECT COUNT(*) FROM order_requests'),0)
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),2)
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),57)
        self.assertEqual(self.value('SELECT balance FROM points'),52)
        with self.assertRaises(RuleError) as ctx:
            self.svc.resolve_payment(pending['id'],{'payment':'approved'})
        self.assertEqual((ctx.exception.status,ctx.exception.code),(409,'PEDIDO_ANTIGO'))
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),2)
        self.assertEqual(self.svc.get(pending['id'],dict(id='cliente-demo',role='customer')),legacy)
        declined,replay=self.svc.resolve_payment(pending['id'],{'payment':'declined'})
        self.assertFalse(replay)
        self.assertEqual(declined['status'],'RECUSADO')
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),57)
        self.assertEqual(self.value('SELECT balance FROM points'),52)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),3)

    def test_PR11_resolution_after_restart_without_loyalty(self):
        """PR11 | Reinício recupera pendência de João Pessoa e aprova sem pontos quando a fidelidade está desmarcada."""
        pending=self.pending(unit='JPA',loyalty=False,coupon='')
        self.svc=OrderService(self.path)
        result,_=self.svc.resolve_payment(pending['id'],{'payment':'approved'})
        self.assertEqual((result['status'],result['total'],result['points']),('CONFIRMADO',5800,0))
        self.assertEqual((result['items'],result['coupon'],result['loyalty']),(pending['items'],'',False))
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='JPA' AND sku='baiao'"),8)
        self.assertEqual(self.value("SELECT qty FROM stock WHERE unit='REC' AND sku='baiao'"),10)
        self.assertEqual(self.value('SELECT balance FROM points'),0)

    def test_PR12_failed_commit_rolls_back_all_effects(self):
        """PR12 | Falha ao registrar a transição desfaz estoque, pontos e estado; nova tentativa pode concluir."""
        pending=self.pending()
        with connect(self.path) as db:
            db.execute("CREATE TRIGGER falha_evento BEFORE INSERT ON events WHEN NEW.status='CONFIRMADO' BEGIN SELECT RAISE(ABORT,'falha simulada'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.svc.resolve_payment(pending['id'],{'payment':'approved'})
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'),60)
        self.assertEqual(self.value('SELECT COUNT(*) FROM points'),0)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'),1)
        self.assertEqual(self.svc.get(pending['id'],dict(id='cliente-demo',role='customer')),pending)
        with connect(self.path) as db:
            db.execute('DROP TRIGGER falha_evento')
        self.assertEqual(self.svc.resolve_payment(pending['id'],{'payment':'approved'})[0]['status'],'CONFIRMADO')

class HttpTests(Base):
    def setUp(self):
        super().setUp()
        self.server=make_server(self.path)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();super().tearDown()
    def req(self,path,data=None,token=True,raw=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+self.server.demo_token
        body=raw if raw is not None else json.dumps(data).encode() if data is not None else None
        try:
            with urlopen(Request(self.url+path,data=body,headers=headers),timeout=5) as r:return r.status,json.loads(r.read()),dict(r.headers)
        except HTTPError as ex:return ex.code,json.loads(ex.read()),dict(ex.headers)
    def test_API01_create_and_get(self):
        """API01 | POST retorna 201; GET recupera os mesmos valores; repetição retorna 200."""
        code,r,_=self.req('/api/orders',payload());self.assertEqual(code,201)
        code2,r2,_=self.req('/api/orders/'+r['id']);self.assertEqual(code2,200);self.assertEqual(r2['total'],5220)
        code3,r3,_=self.req('/api/orders',payload());self.assertEqual(code3,200);self.assertTrue(r3['replayed'])
    def test_API02_no_session(self):
        """API02 | POST sem sessão retorna 401 e não cria pedido."""
        code,r,_=self.req('/api/orders',payload(),token=False);self.assertEqual(code,401)
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),0)
    def test_API03_malformed(self):
        """API03 | JSON malformado retorna 400."""
        self.assertEqual(self.req('/api/orders',raw=b'{bad')[0],400)
    def test_API04_private_fields(self):
        """API04 | CPF e outros campos não previstos são rejeitados com 422."""
        code,r,_=self.req('/api/orders',payload(cpf='00000000000'));self.assertEqual(code,422)
        self.assertEqual(r['code'],'CAMPO_NAO_PERMITIDO')
    def test_API05_size_limit(self):
        """API05 | Corpo acima de 16 KB retorna 413."""
        self.assertEqual(self.req('/api/orders',raw=b'x'*16385)[0],413)
    def test_API06_headers_catalog(self):
        """API06 | Catálogo correto e cabeçalhos no-store, nosniff e DENY."""
        code,r,headers=self.req('/api/catalog?unit=JPA');self.assertEqual(code,200);self.assertEqual(len(r),3)
        self.assertEqual(headers['Cache-Control'],'no-store');self.assertEqual(headers['X-Content-Type-Options'],'nosniff');self.assertEqual(headers['X-Frame-Options'],'DENY')

    def test_API07_payment_resolution_contract(self):
        """API07 | Conferência exige sessão e proprietário, valida corpo e retorna 200 com replay explícito."""
        _,pending,_=self.req('/api/orders',payload(payment='timeout'))
        path='/api/orders/'+pending['id']+'/payment'
        self.assertEqual(self.req(path,{'payment':'approved'},token=False)[0],401)
        self.assertEqual(self.req(path,{'payment':'timeout'})[0],422)
        self.assertEqual(self.req(path,raw=b'{bad')[0],400)
        self.assertEqual(self.req(path,raw=b'x'*16385)[0],413)
        code,result,_=self.req(path,{'payment':'approved'})
        self.assertEqual((code,result['status'],result['replayed']),(200,'CONFIRMADO',False))
        code,result,_=self.req(path,{'payment':'approved'})
        self.assertEqual((code,result['replayed']),(200,True))
        code,result,_=self.req(path,{'payment':'declined'})
        self.assertEqual((code,result['code']),(409,'PAGAMENTO_JA_CONFERIDO'))
        other,_=self.server.order_service.create(payload(payment='timeout',key='outro-dono'),owner='outro-cliente')
        self.assertEqual(self.req('/api/orders/'+other['id']+'/payment',{'payment':'declined'})[0],403)
        self.assertEqual(self.req('/api/orders/inexistente/payment',{'payment':'approved'})[0],404)
        self.assertEqual(self.req(path+'/extra',{'payment':'approved'})[0],404)
        self.assertEqual(self.req(path)[0],404)
        self.assertEqual(self.req('/api/orders/'+pending['id'])[1]['items'],payload()['items'])

    def test_API08_local_failure_returns_503_and_recovers(self):
        """API08 | Banco ou arquivo local indisponível retorna 503 sem detalhes internos e permite recuperação."""
        from unittest.mock import patch
        _,pending,_=self.req('/api/orders',payload(payment='timeout'))
        scenarios=(('catalog','/api/catalog',None,sqlite3.OperationalError('detalhe interno')),
                   ('create','/api/orders',payload(key='apos-falha'),sqlite3.OperationalError('detalhe interno')),
                   ('get','/api/orders/'+pending['id'],None,OSError('detalhe interno')),
                   ('resolve_payment','/api/orders/'+pending['id']+'/payment',{'payment':'approved'},sqlite3.OperationalError('detalhe interno')))
        for method,path,data,error in scenarios:
            with self.subTest(method=method),patch.object(self.server.order_service,method,side_effect=error):
                code,result,_=self.req(path,data)
                self.assertEqual((code,result['code']),(503,'SERVICO_INDISPONIVEL'))
                self.assertNotIn('detalhe interno',json.dumps(result))
        self.assertEqual(self.req('/api/orders/'+pending['id'])[1]['status'],'PENDENTE')
        self.assertEqual(self.req('/api/orders/'+pending['id']+'/payment',{'payment':'approved'})[1]['status'],'CONFIRMADO')
        self.assertEqual(self.req('/api/health')[0],200)

    def test_API09_disconnect_after_commit_keeps_replay(self):
        """API09 | Cliente desconectado após commit não provoca segunda resposta nem duplica efeitos ao repetir."""
        from http.client import IncompleteRead
        from socketserver import _SocketWriter
        from unittest.mock import patch

        handler = self.server.RequestHandlerClass
        original_send_response = handler.send_response
        original_write = _SocketWriter.write
        response_codes = []
        disconnected = threading.Event()

        def record_response(instance, code, message=None):
            response_codes.append(code)
            return original_send_response(instance, code, message)

        def disconnect_on_body(writer, data):
            if data.startswith(b'{') and not disconnected.is_set():
                disconnected.set()
                raise BrokenPipeError('cliente fechou a conexão durante a resposta')
            return original_write(writer, data)

        request = Request(self.url + '/api/orders', data=json.dumps(payload()).encode(),
                          headers={'Content-Type': 'application/json',
                                   'Authorization': 'Bearer ' + self.server.demo_token})
        with patch.object(handler, 'send_response', record_response), \
             patch.object(_SocketWriter, 'write', disconnect_on_body):
            with urlopen(request, timeout=5) as response:
                try:
                    response.read()
                except IncompleteRead:
                    pass

        self.assertTrue(disconnected.is_set())
        self.assertEqual(response_codes, [201])
        code, result, _ = self.req('/api/orders', payload())
        self.assertEqual((code, result['replayed']), (200, True))
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'), 1)
        self.assertEqual(self.value('SELECT COUNT(*) FROM events'), 1)
        self.assertEqual(self.value('SELECT balance FROM points'), 52)
        self.assertEqual(self.value('SELECT SUM(qty) FROM stock'), 57)

    def test_API10_truncated_body_is_not_processed(self):
        """API10 | Corpo menor que Content-Length retorna 400 sem criar pedido, mesmo com JSON válido."""
        import socket
        from http.client import HTTPResponse

        body = json.dumps(payload()).encode()
        headers = (f'POST /api/orders HTTP/1.0\r\n'
                   f'Host: 127.0.0.1\r\n'
                   f'Authorization: Bearer {self.server.demo_token}\r\n'
                   f'Content-Type: application/json\r\n'
                   f'Content-Length: {len(body) + 1}\r\n\r\n').encode()
        with socket.create_connection(self.server.server_address, timeout=5) as client:
            client.sendall(headers + body)
            client.shutdown(socket.SHUT_WR)
            with HTTPResponse(client) as response:
                response.begin()
                result = json.loads(response.read())
                self.assertEqual((response.status, result.get('code')), (400, 'JSON_INVALIDO'))
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'), 0)
        self.assertEqual(self.req('/api/health')[0], 200)

    def test_RG01_non_ascii_authorization(self):
        """RG01 | Credencial não ASCII retorna 401 e preserva a execução do servidor."""
        request=Request(self.url+'/api/orders',data=json.dumps(payload()).encode(),
                        headers={'Content-Type':'application/json','Authorization':'Bearer \u00e9'})
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request,timeout=5)
        with ctx.exception as response:
            self.assertEqual(response.code,401)
            self.assertEqual(json.loads(response.read())['code'],'NAO_AUTORIZADO')
        self.assertEqual(self.value('SELECT COUNT(*) FROM orders'),0)
        self.assertEqual(self.req('/api/health')[0],200)

    def test_RG04_second_server_rejected(self):
        """RG04 | Segunda instância na mesma porta é recusada e a primeira continua saudável."""
        second=None
        try:
            with self.assertRaises(OSError):
                second=make_server(self.path,self.server.server_port)
        finally:
            if second is not None:
                second.server_close()
        code,response,_=self.req('/api/health')
        self.assertEqual(code,200)
        self.assertEqual(response['status'],'ok')


class EvidenceTests(unittest.TestCase):
    def test_RG02_subtest_and_cleanup_reporting(self):
        """RG02 | Falhas em subtestes e na limpeza geram um único resultado por método."""
        import io
        from run_evidence import Result

        class FailedCase(unittest.TestCase):
            def test_example(self):
                for index in range(2):
                    with self.subTest(index=index):
                        self.assertEqual(index,10)
            def tearDown(self):
                raise RuntimeError('falha de limpeza de teste')

        class PassedCase(unittest.TestCase):
            def test_example(self):
                self.assertEqual(2+2,4)

        suite=unittest.TestSuite([FailedCase('test_example'),PassedCase('test_example')])
        result=unittest.TextTestRunner(stream=io.StringIO(),resultclass=Result).run(suite)
        self.assertEqual((result.testsRun,len(result.rows),len(result.failures),len(result.errors)),(2,2,2,1))
        self.assertEqual([row['status'] for row in result.rows],['ERRO','APROVADO'])
        self.assertIn('index=0',result.rows[0]['error'])
        self.assertIn('index=1',result.rows[0]['error'])
        self.assertIn('falha de limpeza de teste',result.rows[0]['error'])
        second=unittest.TextTestRunner(stream=io.StringIO(),resultclass=Result).run(
            unittest.TestSuite([PassedCase('test_example')]))
        self.assertEqual(len(second.rows),1)
        self.assertTrue(second.wasSuccessful())

    def test_RG03_load_failure_preserves_evidence(self):
        """RG03 | Falha de rede no ensaio de carga salva detalhes e encerra com erro."""
        import io
        from contextlib import redirect_stdout
        from unittest.mock import patch
        import run_evidence
        benchmark=run_evidence.run_benchmark
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)
            with patch.object(run_evidence,'run_tests',return_value={'total':0,'passed':0}), \
                 patch.object(run_evidence,'urlopen',side_effect=OSError('rede indisponível no teste')), \
                 patch.object(run_evidence,'run_benchmark',side_effect=lambda:benchmark(requests=2,workers=2)), \
                 redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as ctx:
                run_evidence.main(output)
            self.assertNotEqual(ctx.exception.code,0)
            report=json.loads((output/'desempenho.json').read_text(encoding='utf-8'))
            self.assertEqual((report['requests'],report['success']),(2,0))
            self.assertTrue(all('OSError' in sample['error'] for sample in report['samples']))
            self.assertTrue((output/'fontes_sha256.json').is_file())

if __name__=='__main__':unittest.main(verbosity=2)
