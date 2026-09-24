"""Caso de uso de pedido. Gateway sempre simulado e sem cobrança."""
import json
import uuid
from domain import RuleError, normalize, totals, fingerprint
from repository import connect, initialize

class PaymentMock:
    def authorize(self, mode, total):
        return {'approved':'CONFIRMADO','declined':'RECUSADO','timeout':'PENDENTE'}[mode]

class OrderService:
    def __init__(self, path, stock=100, gateway=None):
        self.path, self.gateway = path, gateway or PaymentMock()
        initialize(path, stock)

    def create(self, data, owner='cliente-demo'):
        order = normalize(data)
        digest = fingerprint(order)
        db = connect(self.path)
        try:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM orders WHERE owner=? AND unit=? AND idem=?', (owner,order['unit'],order['key'])).fetchone()
            if old:
                if old['hash'] != digest:
                    raise RuleError('CHAVE_REUTILIZADA','Esta chave já foi usada para outro pedido.',409)
                db.commit()
                return json.loads(old['payload']), True
            for item in order['items']:
                available = db.execute('SELECT qty FROM stock WHERE unit=? AND sku=?',(order['unit'],item['sku'])).fetchone()['qty']
                if available < item['qty']:
                    raise RuleError('SEM_ESTOQUE','Quantidade indisponível nesta unidade.',409)
            subtotal, discount, total, pts = totals(order)
            state = self.gateway.authorize(order['payment'], total)
            if state not in ('CONFIRMADO','RECUSADO','PENDENTE'):
                raise RuleError('GATEWAY_INVALIDO','Resposta inválida do pagamento simulado.',502)
            oid = str(uuid.uuid4())
            result = dict(id=oid, unit=order['unit'], channel=order['channel'], status=state, subtotal=subtotal, discount=discount, total=total, points=pts if state=='CONFIRMADO' else 0,
                          items=order['items'], coupon=order['coupon'], loyalty=order['loyalty'])
            db.execute('INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?)',(oid,owner,order['unit'],order['key'],digest,state,total,result['points'],json.dumps(result)))
            db.execute('INSERT INTO order_requests(order_id,payload) VALUES(?,?)',(oid,json.dumps(order)))
            if state == 'CONFIRMADO':
                for item in order['items']:
                    db.execute('UPDATE stock SET qty=qty-? WHERE unit=? AND sku=?',(item['qty'],order['unit'],item['sku']))
                db.execute('INSERT INTO points VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET balance=balance+excluded.balance',(owner,pts))
            db.execute('INSERT INTO events(order_id,unit,status) VALUES(?,?,?)',(oid,order['unit'],state))
            db.commit()
            return result, False
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def resolve_payment(self, oid, data, owner='cliente-demo'):
        """Confere um pagamento simulado, preservando estoque e pontos na repetição."""
        if not isinstance(data, dict) or set(data) != {'payment'} or data['payment'] not in ('approved', 'declined'):
            raise RuleError('PAGAMENTO_INVALIDO','Informe apenas payment com approved ou declined.')
        state = 'CONFIRMADO' if data['payment'] == 'approved' else 'RECUSADO'
        db = connect(self.path)
        try:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone()
            if row is None:
                raise RuleError('NAO_ENCONTRADO','Pedido não encontrado.',404)
            if row['owner'] != owner:
                raise RuleError('ACESSO_NEGADO','Acesso não permitido a este pedido.',403)
            result = json.loads(row['payload'])
            if row['status'] != 'PENDENTE':
                if row['status'] != state:
                    raise RuleError('PAGAMENTO_JA_CONFERIDO','Este pagamento já foi conferido. Consulte o resultado do pedido.',409)
                db.commit()
                return result, True
            request = db.execute('SELECT payload FROM order_requests WHERE order_id=?',(oid,)).fetchone()
            order = json.loads(request['payload']) if request else None
            if state == 'CONFIRMADO':
                if order is None:
                    raise RuleError('PEDIDO_ANTIGO','Este pedido foi criado em uma versão anterior. Recuse o pagamento pendente e inicie uma nova simulação.',409)
                for item in order['items']:
                    available = db.execute('SELECT qty FROM stock WHERE unit=? AND sku=?',(row['unit'],item['sku'])).fetchone()
                    if available is None or available['qty'] < item['qty']:
                        raise RuleError('SEM_ESTOQUE','O estoque mudou e este pedido continua pendente. Recuse o pagamento e inicie uma nova simulação.',409)
                for item in order['items']:
                    db.execute('UPDATE stock SET qty=qty-? WHERE unit=? AND sku=?',(item['qty'],row['unit'],item['sku']))
                pts = row['total'] // 100 if order['loyalty'] else 0
                db.execute('INSERT INTO points VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET balance=balance+excluded.balance',(owner,pts))
            else:
                pts = 0
            result.update(status=state, points=pts)
            db.execute('UPDATE orders SET status=?,points=?,payload=? WHERE id=?',(state,pts,json.dumps(result),oid))
            db.execute('INSERT INTO events(order_id,unit,status) VALUES(?,?,?)',(oid,row['unit'],state))
            db.commit()
            return result, False
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, oid, actor):
        with connect(self.path) as db:
            row = db.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone()
        if row is None:
            raise RuleError('NAO_ENCONTRADO','Pedido não encontrado.',404)
        authorized = (actor['role']=='customer' and actor['id']==row['owner']) or (actor['role']=='operator' and actor.get('unit')==row['unit'])
        if not authorized:
            raise RuleError('ACESSO_NEGADO','Acesso não permitido a este pedido.',403)
        return json.loads(row['payload'])

    def catalog(self, unit):
        from domain import PRODUCTS, UNITS
        if unit not in UNITS:
            raise RuleError('UNIDADE_INVALIDA','Selecione uma unidade válida.')
        with connect(self.path) as db:
            return [dict(sku=r['sku'],name=PRODUCTS[r['sku']][0],price=PRODUCTS[r['sku']][1],stock=r['qty']) for r in db.execute('SELECT * FROM stock WHERE unit=? ORDER BY sku',(unit,))]
