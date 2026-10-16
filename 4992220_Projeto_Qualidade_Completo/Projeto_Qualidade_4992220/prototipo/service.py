"""Caso de uso de pedido. Gateway sempre simulado e sem cobrança."""
import json
import uuid

from domain import PRODUCTS, UNITS, RuleError, fingerprint, normalize, totals
from repository import connect, initialize, transaction


class PaymentMock:
    def authorize(self, mode, total):
        return {'approved': 'CONFIRMADO', 'declined': 'RECUSADO', 'timeout': 'PENDENTE'}[mode]


def _require_stock(connection, order, message):
    for item in order['items']:
        available = connection.execute(
            'SELECT qty FROM stock WHERE unit=? AND sku=?',
            (order['unit'], item['sku']),
        ).fetchone()
        if available is None or available['qty'] < item['qty']:
            raise RuleError('SEM_ESTOQUE', message, 409)


def _apply_confirmation(connection, order, owner, points):
    """Usa a transação do pedido para manter estoque e pontos juntos."""
    for item in order['items']:
        connection.execute(
            'UPDATE stock SET qty=qty-? WHERE unit=? AND sku=?',
            (item['qty'], order['unit'], item['sku']),
        )
    connection.execute(
        'INSERT INTO points VALUES(?,?) '
        'ON CONFLICT(owner) DO UPDATE SET balance=balance+excluded.balance',
        (owner, points),
    )


class OrderService:
    def __init__(self, path, stock=100, gateway=None):
        self.path = path
        self.gateway = gateway or PaymentMock()
        initialize(path, stock)

    def create(self, data, owner='cliente-demo'):
        order = normalize(data)
        digest = fingerprint(order)
        with transaction(self.path) as connection:
            existing = connection.execute(
                'SELECT * FROM orders WHERE owner=? AND unit=? AND idem=?',
                (owner, order['unit'], order['key']),
            ).fetchone()
            if existing:
                if existing['hash'] != digest:
                    raise RuleError('CHAVE_REUTILIZADA', 'Esta chave já foi usada para outro pedido.', 409)
                return json.loads(existing['payload']), True

            _require_stock(connection, order, 'Quantidade indisponível nesta unidade.')
            subtotal, discount, total, points = totals(order)
            state = self.gateway.authorize(order['payment'], total)
            if state not in ('CONFIRMADO', 'RECUSADO', 'PENDENTE'):
                raise RuleError('GATEWAY_INVALIDO', 'Resposta inválida do pagamento simulado.', 502)

            order_id = str(uuid.uuid4())
            result = dict(
                id=order_id, unit=order['unit'], channel=order['channel'], status=state,
                subtotal=subtotal, discount=discount, total=total,
                points=points if state == 'CONFIRMADO' else 0,
                items=order['items'], coupon=order['coupon'], loyalty=order['loyalty'],
            )
            connection.execute(
                'INSERT INTO orders(id,owner,unit,idem,hash,status,total,points,payload) '
                'VALUES(?,?,?,?,?,?,?,?,?)',
                (order_id, owner, order['unit'], order['key'], digest, state, total,
                 result['points'], json.dumps(result)),
            )
            connection.execute(
                'INSERT INTO order_requests(order_id,payload) VALUES(?,?)',
                (order_id, json.dumps(order)),
            )
            if state == 'CONFIRMADO':
                _apply_confirmation(connection, order, owner, points)
            connection.execute(
                'INSERT INTO events(order_id,unit,status) VALUES(?,?,?)',
                (order_id, order['unit'], state),
            )
            return result, False

    def resolve_payment(self, oid, data, owner='cliente-demo'):
        """Confere um pagamento simulado, preservando estoque e pontos na repetição."""
        if (not isinstance(data, dict) or set(data) != {'payment'}
                or data['payment'] not in ('approved', 'declined')):
            raise RuleError('PAGAMENTO_INVALIDO', 'Informe apenas payment com approved ou declined.')
        state = 'CONFIRMADO' if data['payment'] == 'approved' else 'RECUSADO'
        with transaction(self.path) as connection:
            row = connection.execute('SELECT * FROM orders WHERE id=?', (oid,)).fetchone()
            if row is None:
                raise RuleError('NAO_ENCONTRADO', 'Pedido não encontrado.', 404)
            if row['owner'] != owner:
                raise RuleError('ACESSO_NEGADO', 'Acesso não permitido a este pedido.', 403)
            result = json.loads(row['payload'])
            if row['status'] != 'PENDENTE':
                if row['status'] != state:
                    raise RuleError(
                        'PAGAMENTO_JA_CONFERIDO',
                        'Este pagamento já foi conferido. Consulte o resultado do pedido.', 409,
                    )
                return result, True

            saved_request = connection.execute(
                'SELECT payload FROM order_requests WHERE order_id=?', (oid,),
            ).fetchone()
            order = json.loads(saved_request['payload']) if saved_request else None
            points = 0
            if state == 'CONFIRMADO':
                if order is None:
                    raise RuleError(
                        'PEDIDO_ANTIGO',
                        'Este pedido foi criado em uma versão anterior. Recuse o pagamento pendente '
                        'e inicie uma nova simulação.', 409,
                    )
                # Pendências não reservam estoque. Outra compra pode ter consumido os itens.
                _require_stock(
                    connection, order,
                    'O estoque mudou e este pedido continua pendente. Recuse o pagamento '
                    'e inicie uma nova simulação.',
                )
                points = row['total'] // 100 if order['loyalty'] else 0
                _apply_confirmation(connection, order, owner, points)

            result.update(status=state, points=points)
            connection.execute(
                'UPDATE orders SET status=?,points=?,payload=? WHERE id=?',
                (state, points, json.dumps(result), oid),
            )
            connection.execute(
                'INSERT INTO events(order_id,unit,status) VALUES(?,?,?)',
                (oid, row['unit'], state),
            )
            return result, False

    def get(self, oid, actor):
        with connect(self.path) as connection:
            row = connection.execute('SELECT * FROM orders WHERE id=?', (oid,)).fetchone()
        if row is None:
            raise RuleError('NAO_ENCONTRADO', 'Pedido não encontrado.', 404)
        authorized = (
            actor['role'] == 'customer' and actor['id'] == row['owner']
        ) or (
            actor['role'] == 'operator' and actor.get('unit') == row['unit']
        )
        if not authorized:
            raise RuleError('ACESSO_NEGADO', 'Acesso não permitido a este pedido.', 403)
        return json.loads(row['payload'])

    def catalog(self, unit):
        if unit not in UNITS:
            raise RuleError('UNIDADE_INVALIDA', 'Selecione uma unidade válida.')
        with connect(self.path) as connection:
            rows = connection.execute('SELECT * FROM stock WHERE unit=? ORDER BY sku', (unit,))
            return [
                dict(sku=row['sku'], name=PRODUCTS[row['sku']][0],
                     price=PRODUCTS[row['sku']][1], stock=row['qty'])
                for row in rows
            ]
