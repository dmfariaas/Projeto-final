import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { beforeEach, test } from 'node:test';
import { demoRequest, resetDemo } from '../dist/demo-store.js';

const databaseName = 'raizes-nordeste-online-v1';
let sequence = 0;

function order(changes = {}) {
  return {
    unit: 'REC', channel: 'WEB', items: [{ sku: 'baiao', qty: 2 }, { sku: 'suco', qty: 1 }],
    coupon: 'RAIZES10', loyalty: true, payment: 'approved',
    key: `test-order-${++sequence}`, ...changes,
  };
}

function post(url, data, request = demoRequest) {
  return request(url, { method: 'POST', body: JSON.stringify(data) });
}

async function create(changes = {}, request = demoRequest) {
  return post('/api/orders', order(changes), request);
}

async function catalog(unit = 'REC', request = demoRequest) {
  const result = await request(`/api/catalog?unit=${unit}`);
  assert.equal(result.response.status, 200);
  return Object.fromEntries(result.data.map(item => [item.sku, item]));
}

async function inspectState(change) {
  const database = await new Promise((resolve, reject) => {
    const request = indexedDB.open(databaseName);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  try {
    return await new Promise((resolve, reject) => {
      const transaction = database.transaction('demo', change ? 'readwrite' : 'readonly');
      const store = transaction.objectStore('demo');
      const request = store.get('state');
      let state;
      request.onsuccess = () => {
        state = request.result;
        if (change) {
          change(state);
          store.put(state, 'state');
        }
      };
      transaction.oncomplete = () => resolve(state);
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error ?? new Error('Transaction aborted'));
    });
  } finally {
    database.close();
  }
}

beforeEach(async () => { await resetDemo(); });

test('two baiões and one juice apply coupon, persist receipt, stock and 52 points', async () => {
  const result = await create();
  assert.equal(result.response.status, 201);
  assert.equal(result.response.ok, true);
  assert.equal(result.data.status, 'CONFIRMADO');
  assert.equal(result.data.subtotal, 5800);
  assert.equal(result.data.discount, 580);
  assert.equal(result.data.total, 5220);
  assert.equal(result.data.points, 52);
  assert.equal(result.data.replayed, false);
  const inventory = await catalog();
  assert.equal(inventory.baiao.stock, 98);
  assert.equal(inventory.suco.stock, 99);
  const stored = await demoRequest(`/api/orders/${result.data.id}`);
  assert.equal(stored.response.status, 200);
  assert.equal(stored.data.id, result.data.id);
  assert.equal(stored.data.total, 5220);
  assert.equal((await inspectState()).points, 52);
});

test('declined payment records an outcome without consuming stock or crediting points', async () => {
  const result = await create({ payment: 'declined' });
  assert.equal(result.response.status, 201);
  assert.equal(result.data.status, 'RECUSADO');
  assert.equal(result.data.points, 0);
  assert.equal((await catalog()).baiao.stock, 100);
  assert.equal((await inspectState()).points, 0);
});

test('pending payment can be approved exactly once, including a repeated confirmation', async () => {
  const pending = await create({ payment: 'timeout' });
  assert.equal(pending.data.status, 'PENDENTE');
  assert.equal(pending.data.points, 0);
  assert.equal((await catalog()).baiao.stock, 100);
  const path = `/api/orders/${pending.data.id}/payment`;
  const results = await Promise.all([post(path, { payment: 'approved' }), post(path, { payment: 'approved' })]);
  assert.ok(results.every(result => result.response.status === 200));
  assert.ok(results.every(result => result.data.status === 'CONFIRMADO'));
  assert.deepEqual(results.map(result => result.data.replayed).sort(), [false, true]);
  assert.equal((await catalog()).baiao.stock, 98);
  assert.equal((await inspectState()).points, 52);
  const contradictory = await post(path, { payment: 'declined' });
  assert.equal(contradictory.response.status, 409);
  assert.equal(contradictory.data.code, 'PAGAMENTO_JA_CONFERIDO');
});

test('pending payment can be declined without changing stock and points', async () => {
  const pending = await create({ payment: 'timeout' });
  const path = `/api/orders/${pending.data.id}/payment`;
  const result = await post(path, { payment: 'declined' });
  assert.equal(result.response.status, 200);
  assert.equal(result.data.status, 'RECUSADO');
  assert.equal(result.data.points, 0);
  assert.equal((await catalog()).baiao.stock, 100);
  assert.equal((await inspectState()).points, 0);
  assert.equal((await post(path, { payment: 'declined' })).data.replayed, true);
  assert.equal((await post(path, { payment: 'approved' })).response.status, 409);
});

test('concurrent delivery of the same order creates one receipt and one stock movement', async () => {
  const payload = order();
  const results = await Promise.all([post('/api/orders', payload), post('/api/orders', payload)]);
  assert.deepEqual(results.map(result => result.response.status).sort(), [200, 201]);
  assert.equal(results[0].data.id, results[1].data.id);
  assert.deepEqual(results.map(result => result.data.replayed).sort(), [false, true]);
  assert.equal((await catalog()).baiao.stock, 98);
  const state = await inspectState();
  assert.equal(state.points, 52);
  assert.equal(Object.keys(state.orders).length, 1);
});

test('reusing a key for a changed order conflicts and leaves the first order intact', async () => {
  const payload = order();
  const first = await post('/api/orders', payload);
  const second = await post('/api/orders', { ...payload, coupon: '' });
  assert.equal(second.response.status, 409);
  assert.equal(second.data.code, 'CHAVE_REUTILIZADA');
  assert.equal((await demoRequest(`/api/orders/${first.data.id}`)).data.total, 5220);
  assert.equal((await catalog()).baiao.stock, 98);
  assert.equal((await inspectState()).points, 52);
});

test('item order is normalized so an equivalent retry retrieves the same receipt', async () => {
  const payload = order();
  const first = await post('/api/orders', payload);
  const second = await post('/api/orders', { ...payload, items: [...payload.items].reverse() });
  assert.equal(second.response.status, 200);
  assert.equal(second.data.replayed, true);
  assert.equal(second.data.id, first.data.id);
});

test('two competing orders cannot both buy the last unit', async () => {
  await inspectState(state => { state.stock.REC.baiao = 1; });
  const changes = { items: [{ sku: 'baiao', qty: 1 }], coupon: '' };
  const results = await Promise.all([create(changes), create(changes)]);
  assert.deepEqual(results.map(result => result.response.status).sort(), [201, 409]);
  assert.equal(results.find(result => result.response.status === 409).data.code, 'SEM_ESTOQUE');
  assert.equal((await catalog()).baiao.stock, 0);
  assert.equal((await inspectState()).points, 25);
  assert.equal(Object.keys((await inspectState()).orders).length, 1);
});

test('pending approval rechecks stock and stays pending when another order bought the last unit', async () => {
  await inspectState(state => { state.stock.REC.baiao = 1; });
  const changes = { items: [{ sku: 'baiao', qty: 1 }], coupon: '' };
  const pending = await create({ ...changes, payment: 'timeout' });
  await create(changes);
  const result = await post(`/api/orders/${pending.data.id}/payment`, { payment: 'approved' });
  assert.equal(result.response.status, 409);
  assert.equal(result.data.code, 'SEM_ESTOQUE');
  assert.equal((await demoRequest(`/api/orders/${pending.data.id}`)).data.status, 'PENDENTE');
  assert.equal((await catalog()).baiao.stock, 0);
  assert.equal((await inspectState()).points, 25);
  assert.equal((await post(`/api/orders/${pending.data.id}/payment`, { payment: 'declined' })).data.status, 'RECUSADO');
});

test('stock and idempotency keys are scoped to the selected unit', async () => {
  const payload = order();
  const recife = await post('/api/orders', payload);
  const joaoPessoa = await post('/api/orders', { ...payload, unit: 'JPA', items: [{ sku: 'suco', qty: 3 }] });
  assert.equal(recife.response.status, 201);
  assert.equal(joaoPessoa.response.status, 201);
  assert.notEqual(recife.data.id, joaoPessoa.data.id);
  assert.equal((await catalog('REC')).baiao.stock, 98);
  assert.equal((await catalog('REC')).suco.stock, 99);
  assert.equal((await catalog('JPA')).baiao.stock, 100);
  assert.equal((await catalog('JPA')).suco.stock, 97);
});

test('each documented channel can complete an order', async () => {
  for (const channel of ['APP', 'WEB', 'TOTEM', 'BALCAO', 'PICKUP']) {
    const result = await create({ channel });
    assert.equal(result.response.status, 201, channel);
    assert.equal(result.data.channel, channel);
  }
});

test('loyalty can be disabled without changing the price', async () => {
  const result = await create({ loyalty: false });
  assert.equal(result.data.total, 5220);
  assert.equal(result.data.points, 0);
  assert.equal((await inspectState()).points, 0);
});

test('invalid quantities never create an order or change inventory', async () => {
  for (const qty of [0, -1, 11, 1.5, '2', true, null]) {
    const result = await create({ items: [{ sku: 'baiao', qty }] });
    assert.equal(result.response.status, 422, JSON.stringify(qty));
    assert.equal(result.data.code, 'QUANTIDADE_INVALIDA');
  }
  assert.equal((await catalog()).baiao.stock, 100);
  assert.equal(Object.keys((await inspectState()).orders).length, 0);
});

test('unknown coupon, unit, product, payment and extra fields are rejected', async () => {
  const cases = [
    [{ coupon: 'PROMO100' }, 'CUPOM_INVALIDO'],
    [{ unit: 'LIS' }, 'UNIDADE_INVALIDA'],
    [{ channel: 'EMAIL' }, 'CANAL_INVALIDO'],
    [{ items: [] }, 'CARRINHO_INVALIDO'],
    [{ items: [{ sku: 'pizza', qty: 1 }] }, 'PRODUTO_INVALIDO'],
    [{ items: [{ sku: 'suco', qty: 1 }, { sku: 'suco', qty: 2 }] }, 'PRODUTO_INVALIDO'],
    [{ payment: 'real' }, 'PAGAMENTO_INVALIDO'],
    [{ loyalty: 'true' }, 'FIDELIDADE_INVALIDA'],
    [{ key: 'short' }, 'CHAVE_INVALIDA'],
    [{ key: '<script>123</script>' }, 'CHAVE_INVALIDA'],
    [{ key: 'valid-key-123\n' }, 'CHAVE_INVALIDA'],
    [{ total: 1 }, 'CAMPO_NAO_PERMITIDO'],
  ];
  for (const [changes, expected] of cases) {
    const result = await create(changes);
    assert.equal(result.response.status, 422, expected);
    assert.equal(result.data.code, expected);
  }
  assert.equal(Object.keys((await inspectState()).orders).length, 0);
});

test('malformed JSON, missing orders and invalid payment confirmations return controlled errors', async () => {
  const invalid = await demoRequest('/api/orders', { method: 'POST', body: '{broken' });
  assert.equal(invalid.response.status, 400);
  assert.equal(invalid.data.code, 'JSON_INVALIDO');
  assert.equal((await demoRequest('/api/orders/does-not-exist')).response.status, 404);
  const pending = await create({ payment: 'timeout' });
  for (const body of [{ payment: 'timeout' }, { payment: 'approved', total: 1 }, null, []]) {
    const result = await post(`/api/orders/${pending.data.id}/payment`, body);
    assert.equal(result.response.status, 422);
    assert.equal(result.data.code, 'PAGAMENTO_INVALIDO');
  }
  assert.equal((await catalog()).baiao.stock, 100);
});

test('a fresh module instance recovers persisted orders and prevents a duplicate after reload', async () => {
  const payload = order();
  const first = await post('/api/orders', payload);
  const fresh = await import(`../dist/demo-store.js?recovery=${Date.now()}`);
  const stored = await fresh.demoRequest(`/api/orders/${first.data.id}`);
  assert.equal(stored.response.status, 200);
  assert.equal(stored.data.id, first.data.id);
  const replay = await post('/api/orders', payload, fresh.demoRequest);
  assert.equal(replay.response.status, 200);
  assert.equal(replay.data.replayed, true);
  assert.equal(replay.data.id, first.data.id);
  assert.equal((await catalog('REC', fresh.demoRequest)).baiao.stock, 98);
  assert.equal((await inspectState()).points, 52);
});

test('separate module instances serialize purchases of the same last unit', async () => {
  await inspectState(state => { state.stock.REC.baiao = 1; });
  const fresh = await import(`../dist/demo-store.js?parallel=${Date.now()}`);
  const changes = { items: [{ sku: 'baiao', qty: 1 }], coupon: '' };
  const results = await Promise.all([create(changes), create(changes, fresh.demoRequest)]);
  assert.deepEqual(results.map(result => result.response.status).sort(), [201, 409]);
  assert.equal((await catalog()).baiao.stock, 0);
  assert.equal((await inspectState()).points, 25);
});

test('reset restores both units and removes receipts and loyalty points', async () => {
  const receipt = await create();
  await create({ unit: 'JPA' });
  await resetDemo();
  for (const unit of ['REC', 'JPA']) {
    assert.ok(Object.values(await catalog(unit)).every(item => item.stock === 100));
  }
  assert.equal((await demoRequest(`/api/orders/${receipt.data.id}`)).response.status, 404);
  assert.equal((await inspectState()).points, 0);
});

test('an already cancelled request cannot create an order', async () => {
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(demoRequest('/api/orders', {
    method: 'POST', body: JSON.stringify(order()), signal: controller.signal,
  }), { name: 'AbortError' });
  assert.equal((await catalog()).baiao.stock, 100);
  assert.equal(Object.keys((await inspectState()).orders).length, 0);
});

test('cancellation while a write is queued rolls back the complete order', async () => {
  const controller = new AbortController();
  const pending = demoRequest('/api/orders', {
    method: 'POST', body: JSON.stringify(order()), signal: controller.signal,
  });
  // Let the request open its transaction, then cancel before its asynchronous read completes.
  await Promise.resolve();
  controller.abort();
  await assert.rejects(pending, { name: 'AbortError' });
  assert.equal((await catalog()).baiao.stock, 100);
  const state = await inspectState();
  assert.equal(state.points, 0);
  assert.equal(Object.keys(state.orders).length, 0);
});
