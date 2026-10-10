import 'fake-indexeddb/auto';
import assert from 'node:assert/strict';
import { afterEach, beforeEach, test } from 'node:test';
import { readFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { setImmediate as nextTurn } from 'node:timers/promises';
import { JSDOM } from 'jsdom';
import { demoRequest, resetDemo } from '../dist/demo-store.js';

const html = await readFile(new URL('../dist/index.html', import.meta.url), 'utf8');
const sessionKey = 'raizes-online-session-v1';
let dom;
let pageNumber = 0;
const $ = id => document.getElementById(id);

async function until(condition) {
  const deadline = Date.now() + 3000;
  while (!condition()) {
    if (Date.now() >= deadline) throw new Error('A interface não terminou a atualização no tempo esperado.');
    await nextTurn();
  }
}

async function idle() {
  await until(() => !$('refresh-catalog').disabled && !$('refresh-session').disabled);
}

async function openPage(savedSession) {
  dom?.window.close();
  dom = new JSDOM(html, { url: 'https://restaurant.example/' });
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  globalThis.location = dom.window.location;
  globalThis.sessionStorage = dom.window.sessionStorage;
  globalThis.confirm = () => true;
  if (savedSession !== undefined) sessionStorage.setItem(sessionKey, savedSession);
  await import(`../dist/app.js?page-test=${++pageNumber}`);
  await idle();
}

function select(id, value) {
  $(id).value = value;
  $(id).dispatchEvent(new dom.window.Event('change', { bubbles: true }));
}

function add(sku, quantity = 1) {
  const button = document.querySelector(`[data-action="plus"][data-sku="${sku}"]`);
  for (let i = 0; i < quantity; i++) button.click();
}

function coupon(value) {
  $('coupon').value = value;
  $('coupon').dispatchEvent(new dom.window.Event('input', { bubbles: true }));
}

async function click(id) {
  $(id).click();
  await idle();
}

function saved() { return JSON.parse(sessionStorage.getItem(sessionKey)); }

async function stock(unit = 'REC', sku = 'baiao') {
  return (await demoRequest(`/api/catalog?unit=${unit}`)).data.find(product => product.sku === sku).stock;
}

beforeEach(async () => {
  await resetDemo();
  await openPage();
});
afterEach(() => { dom?.window.close(); });

test('page loads its three menu products with quantity controls and a working cart', async () => {
  assert.equal(document.querySelectorAll('#menu article').length, 3);
  assert.equal(document.querySelectorAll('[data-action="plus"]').length, 3);
  assert.match($('items').textContent, /vazio/);
  add('baiao', 2);
  add('suco');
  assert.match($('subtotal').textContent, /58,00/);
  coupon('  raizes10  ');
  assert.match($('discount').textContent, /5,80/);
  assert.match($('total').textContent, /52,20/);
  assert.match($('items').textContent, /2 × Baião de dois/);
  assert.equal(saved().counts.baiao, 2);
  document.querySelector('[data-action="minus"][data-sku="baiao"]').click();
  assert.match($('total').textContent, /29,70/);
});

test('empty cart and invalid coupon give useful errors without locking the form', async () => {
  await click('submit');
  assert.equal($('result').querySelector('h3').textContent, 'Carrinho vazio');
  add('baiao');
  coupon('ERRADO');
  await click('submit');
  assert.match($('result').textContent, /Cupom inválido/);
  assert.equal($('coupon').disabled, false);
  assert.equal($('submit').disabled, false);
  assert.equal(await stock(), 100);
  coupon('RAIZES10');
  await click('submit');
  assert.equal($('result').querySelector('h3').textContent, 'Pedido confirmado');
});

test('approved checkout displays receipt, changes inventory once and starts another order', async () => {
  add('baiao', 2);
  add('suco');
  coupon('RAIZES10');
  $('loyalty').checked = true;
  $('loyalty').dispatchEvent(new dom.window.Event('change'));
  $('submit').click();
  $('submit').click();
  await idle();
  assert.equal($('result').querySelector('h3').textContent, 'Pedido confirmado');
  assert.match($('result').textContent, /52,20.*52 pontos/);
  assert.equal($('submit').disabled, true);
  assert.equal($('new').hidden, false);
  assert.equal(await stock(), 98);
  assert.equal(await stock('REC', 'suco'), 99);
  const firstId = saved().lastOrder.id;
  await click('new');
  assert.match($('items').textContent, /vazio/);
  assert.equal($('submit').disabled, false);
  add('tapioca');
  await click('submit');
  assert.notEqual(saved().lastOrder.id, firstId);
});

test('declined checkout shows the outcome and permits a new order without consuming stock', async () => {
  add('baiao');
  select('payment', 'declined');
  await click('submit');
  assert.equal($('result').querySelector('h3').textContent, 'Pagamento recusado');
  assert.equal(await stock(), 100);
  assert.equal(saved().lastOrder.points, 0);
  assert.equal($('payment-actions').hidden, true);
  assert.equal($('new').hidden, false);
});

test('pending checkout exposes both resolution options and approves through the visible button', async () => {
  add('baiao');
  select('payment', 'timeout');
  await click('submit');
  assert.equal($('result').querySelector('h3').textContent, 'Pagamento pendente');
  assert.equal($('payment-actions').hidden, false);
  assert.equal($('new').hidden, true);
  assert.equal(await stock(), 100);
  await click('resolve-approved');
  assert.equal($('result').querySelector('h3').textContent, 'Pedido confirmado');
  assert.equal($('payment-actions').hidden, true);
  assert.equal(await stock(), 99);
});

test('pending checkout declines through the visible button and preserves inventory', async () => {
  add('baiao');
  select('payment', 'timeout');
  await click('submit');
  await click('resolve-declined');
  assert.equal($('result').querySelector('h3').textContent, 'Pagamento recusado');
  assert.equal($('payment-actions').hidden, true);
  assert.equal(await stock(), 100);
});

test('reopening the page restores cart details before checkout', async () => {
  add('baiao', 2);
  coupon('RAIZES10');
  select('channel', 'PICKUP');
  await openPage(sessionStorage.getItem(sessionKey));
  assert.match($('items').textContent, /2 × Baião de dois/);
  assert.match($('total').textContent, /45,00/);
  assert.equal($('channel').value, 'PICKUP');
  assert.equal($('submit').disabled, false);
});

test('reopening a confirmed order restores the receipt without making another purchase', async () => {
  add('baiao', 2);
  await click('submit');
  const receiptId = saved().lastOrder.id;
  await openPage(sessionStorage.getItem(sessionKey));
  assert.equal(saved().lastOrder.id, receiptId);
  assert.equal($('result').querySelector('h3').textContent, 'Pedido confirmado');
  assert.equal($('submit').disabled, true);
  assert.equal(await stock(), 98);
});

test('changing unit refreshes its inventory and clears the current cart', async () => {
  add('baiao', 2);
  await click('submit');
  await click('new');
  add('suco');
  select('unit', 'JPA');
  await idle();
  assert.match($('items').textContent, /vazio/);
  assert.match(document.querySelector('#menu article').textContent, /100 disponíveis/);
  assert.equal(await stock('REC'), 98);
  add('baiao');
  await click('submit');
  assert.equal(saved().lastOrder.unit, 'JPA');
  assert.equal(await stock('REC'), 98);
  assert.equal(await stock('JPA'), 99);
});

test('reset asks for confirmation and restores the demo when accepted', async () => {
  add('baiao', 2);
  coupon('RAIZES10');
  await click('submit');
  let confirmations = 0;
  globalThis.confirm = () => { confirmations++; return false; };
  await click('reset-demo');
  assert.equal(await stock(), 98);
  assert.equal($('result').querySelector('h3').textContent, 'Pedido confirmado');
  globalThis.confirm = () => { confirmations++; return true; };
  await click('reset-demo');
  assert.equal(confirmations, 2);
  assert.equal(await stock(), 100);
  assert.match($('items').textContent, /vazio/);
  assert.equal($('coupon').value, '');
  assert.equal(saved().lastOrder, null);
  assert.equal($('submit').disabled, false);
});

test('a separate browser storage starts independently from this browser purchases', async () => {
  add('baiao', 2);
  await click('submit');
  const output = execFileSync(process.execPath, ['--input-type=module', '-e', `
    import 'fake-indexeddb/auto';
    import { demoRequest } from './dist/demo-store.js';
    const result = await demoRequest('/api/catalog?unit=REC');
    console.log(JSON.stringify(result.data));
  `], { cwd: new URL('..', import.meta.url), encoding: 'utf8' });
  const separateInventory = JSON.parse(output);
  assert.equal(separateInventory.find(product => product.sku === 'baiao').stock, 100);
  assert.equal(await stock(), 98);
});
