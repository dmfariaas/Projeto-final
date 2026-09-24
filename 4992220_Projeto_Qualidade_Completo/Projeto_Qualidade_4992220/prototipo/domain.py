"""Regras do recorte acadêmico. Valores monetários em centavos."""
import hashlib
import json
import re

CHANNELS = ('APP', 'WEB', 'TOTEM', 'BALCAO', 'PICKUP')
PRODUCTS = {'baiao': ('Baião de dois', 2500), 'tapioca': ('Tapioca de queijo', 1200), 'suco': ('Suco de cajá', 800)}
UNITS = ('REC', 'JPA')

class RuleError(Exception):
    def __init__(self, code, message, status=422):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status

def normalize(data):
    if not isinstance(data, dict):
        raise RuleError('DADOS_INVALIDOS', 'Envie um objeto de pedido.')
    allowed = {'unit', 'channel', 'items', 'coupon', 'loyalty', 'payment', 'key'}
    if set(data) - allowed:
        raise RuleError('CAMPO_NAO_PERMITIDO', 'O pedido contém campos não permitidos.')
    unit, channel = data.get('unit'), data.get('channel')
    if unit not in UNITS:
        raise RuleError('UNIDADE_INVALIDA', 'Selecione uma unidade válida.')
    if channel not in CHANNELS:
        raise RuleError('CANAL_INVALIDO', 'Selecione um canal válido.')
    items = data.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 3:
        raise RuleError('CARRINHO_INVALIDO', 'Inclua entre um e três produtos diferentes.')
    clean, seen = [], set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {'sku', 'qty'}:
            raise RuleError('ITEM_INVALIDO', 'Informe produto e quantidade.')
        sku, qty = item['sku'], item['qty']
        if not isinstance(sku, str) or sku not in PRODUCTS or sku in seen:
            raise RuleError('PRODUTO_INVALIDO', 'Produto desconhecido ou repetido.')
        if type(qty) is not int or not 1 <= qty <= 10:
            raise RuleError('QUANTIDADE_INVALIDA', 'A quantidade deve ser inteira, de 1 a 10.')
        seen.add(sku)
        clean.append({'sku': sku, 'qty': qty})
    coupon = data.get('coupon', '')
    if coupon not in ('', 'RAIZES10'):
        raise RuleError('CUPOM_INVALIDO', 'Cupom inválido. Use RAIZES10 na demonstração.')
    loyalty = data.get('loyalty', False)
    if type(loyalty) is not bool:
        raise RuleError('FIDELIDADE_INVALIDA', 'A opção de fidelidade deve ser verdadeira ou falsa.')
    payment = data.get('payment', 'approved')
    if payment not in ('approved', 'declined', 'timeout'):
        raise RuleError('PAGAMENTO_INVALIDO', 'Resultado simulado de pagamento inválido.')
    key = data.get('key')
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,80}', key):
        raise RuleError('CHAVE_INVALIDA', 'A chave do pedido deve ter entre 8 e 80 caracteres seguros.')
    return dict(unit=unit, channel=channel, items=sorted(clean, key=lambda i: i['sku']), coupon=coupon, loyalty=loyalty, payment=payment, key=key)

def totals(order):
    subtotal = sum(PRODUCTS[x['sku']][1] * x['qty'] for x in order['items'])
    discount = (subtotal * 10 + 50) // 100 if order['coupon'] else 0
    total = subtotal - discount
    return subtotal, discount, total, total // 100 if order['loyalty'] else 0

def fingerprint(order):
    return hashlib.sha256(json.dumps({k:v for k,v in order.items() if k != 'key'}, sort_keys=True).encode()).hexdigest()
