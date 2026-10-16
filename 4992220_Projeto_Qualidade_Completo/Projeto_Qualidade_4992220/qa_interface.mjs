import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import os from 'node:os';
import { spawn, spawnSync } from 'node:child_process';
import { once } from 'node:events';
const root = path.dirname(fileURLToPath(import.meta.url));
const out = process.env.DEMO_EVIDENCE_DIR
  ? path.resolve(process.env.DEMO_EVIDENCE_DIR)
  : path.join(root, 'evidencias');
let browser,
  page,
  server,
  tempDir,
  url,
  runtimeError = '';
const rows = [],
  errors = [];
await fs.mkdir(out, { recursive: true });
async function isolatedServer() {
  const candidates = process.env.DEMO_PYTHON
    ? [[process.env.DEMO_PYTHON]]
    : process.platform === 'win32'
      ? [['py', '-3'], ['python']]
      : [['python3'], ['python']];
  const command = candidates.find(
    ([exe, ...args]) =>
      spawnSync(
        exe,
        [...args, '-c', 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'],
        { windowsHide: true, timeout: 10000 },
      ).status === 0,
  );
  if (!command)
    throw Error('Python 3.11 ou superior não encontrado. Instale-o ou informe DEMO_PYTHON.');
  tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'qualidade-ui-'));
  const [exe, ...args] = command;
  server = spawn(
    exe,
    [
      ...args,
      path.join(root, 'prototipo', 'api.py'),
      '--port',
      '0',
      '--db',
      path.join(tempDir, 'teste.sqlite3'),
    ],
    {
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    },
  );
  return await new Promise((resolve, reject) => {
    let stdout = '',
      stderr = '';
    const timer = setTimeout(
      () => finish(Error('A demonstração não iniciou em 15 segundos.')),
      15000,
    );
    function finish(error, value) {
      clearTimeout(timer);
      server.stdout.off('data', onData);
      server.off('error', onError);
      server.off('exit', onExit);
      error ? reject(error) : resolve(value);
    }
    function onData(data) {
      stdout += data;
      const match = stdout.match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) finish(null, match[0]);
    }
    function onError(error) {
      finish(error);
    }
    function onExit() {
      finish(Error('Falha ao iniciar a demonstração: ' + stderr.trim()));
    }
    server.stdout.on('data', onData);
    server.stderr.on('data', (data) => {
      stderr += data;
    });
    server.once('error', onError);
    server.once('exit', onExit);
  });
}
async function fresh() {
  await page.evaluate(() => {
    window.name = 'raizes-ui-fresh';
  });
  await page.goto(url);
  await ready();
}
async function ready() {
  await page.getByRole('button', { name: 'Adicionar Baião de dois', exact: true }).waitFor();
  await page.waitForFunction(() => !document.querySelector('#unit').disabled);
}
async function catalog(unit = 'REC') {
  return await (await page.request.get(url + '/api/catalog?unit=' + unit)).json();
}
function stockDelta(before, after, sku) {
  return before.find((p) => p.sku === sku).stock - after.find((p) => p.sku === sku).stock;
}
async function quantity(name) {
  return Number(await page.getByLabel('Quantidade de ' + name, { exact: true }).innerText());
}
async function add() {
  await page.getByRole('button', { name: 'Adicionar Baião de dois', exact: true }).click();
  await page.getByRole('button', { name: 'Adicionar Baião de dois', exact: true }).click();
  await page.getByRole('button', { name: 'Adicionar Suco de cajá', exact: true }).click();
}
async function scenario(id, description, fn) {
  const start = Date.now();
  try {
    await fn();
    rows.push({ id, description, status: 'APROVADO', duration_ms: Date.now() - start });
  } catch (error) {
    rows.push({
      id,
      description,
      status: 'FALHOU',
      duration_ms: Date.now() - start,
      error: error.message,
    });
    throw error;
  }
}
try {
  url = await isolatedServer();
  browser = await chromium.launch({ headless: true, channel: 'chrome' });
  page = await browser.newPage({
    viewport: { width: 1366, height: 1000 },
    deviceScaleFactor: 2,
    locale: 'pt-BR',
  });
  // Limpa antes de iniciar a aplicação, sem apagar o estado das recargas de cada cenário.
  await page.addInitScript(() => {
    if (window.name === 'raizes-ui-fresh') {
      sessionStorage.clear();
      window.name = '';
    }
  });
  page.on('pageerror', (err) => errors.push(err.message));
  await scenario(
    'UI01',
    'Compra com desconto, fidelidade e confirmação preservada após falha do catálogo',
    async () => {
      await fresh();
      await add();
      await page.getByLabel('Cupom', { exact: true }).fill('RAIZES10');
      await page.locator('#loyalty').check();
      assert.match(await page.locator('#total').innerText(), /52,20/);
      await page.screenshot({ path: path.join(out, 'tela_desktop.png'), fullPage: true });
      await page.locator('.intro').screenshot({ path: path.join(out, 'identidade_visual.png') });
      await page.locator('header').scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(out, 'previa_restaurante.png') });
      await page.getByRole('button', { name: 'Confirmar pedido simulado' }).click();
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      assert.match(await page.locator('#result').innerText(), /52 pontos/);
      await page.screenshot({ path: path.join(out, 'pedido_confirmado.png'), fullPage: true });
      await page.locator('#result').screenshot({ path: path.join(out, 'detalhe_confirmacao.png') });
      await fresh();
      await add();
      const before = await (await page.request.get(url + '/api/catalog?unit=REC')).json();
      await page.route('**/api/catalog?**', (route) => route.abort('failed'), { times: 1 });
      const posted = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
      await page.getByRole('button', { name: 'Confirmar pedido simulado' }).click();
      const response = await posted,
        order = await response.json();
      assert.equal(response.status(), 201);
      assert.equal(order.status, 'CONFIRMADO');
      await page
        .getByText(
          'Não foi possível atualizar o estoque exibido. O resultado deste pedido está registrado acima.',
          { exact: true },
        )
        .waitFor();
      assert.equal(
        await page.getByRole('heading', { name: 'Pedido confirmado' }).isVisible(),
        true,
      );
      assert.ok((await page.locator('#result').innerText()).includes(order.id));
      assert.equal(await page.locator('#submit').isDisabled(), true);
      assert.equal(await page.locator('#new').isVisible(), true);
      const after = await (await page.request.get(url + '/api/catalog?unit=REC')).json();
      assert.equal(
        before.find((p) => p.sku === 'baiao').stock - after.find((p) => p.sku === 'baiao').stock,
        2,
      );
      assert.equal(
        before.find((p) => p.sku === 'suco').stock - after.find((p) => p.sku === 'suco').stock,
        1,
      );
    },
  );
  await scenario('UI02', 'Carrinho vazio e cupom inválido exibem mensagens', async () => {
    await fresh();
    await page.getByRole('button', { name: 'Confirmar pedido simulado' }).click();
    await page.getByRole('heading', { name: 'Carrinho vazio' }).waitFor();
    await add();
    await page.getByLabel('Cupom', { exact: true }).fill('INVALIDO');
    await page.getByRole('button', { name: 'Confirmar pedido simulado' }).click();
    await page
      .getByText('Cupom inválido. Use RAIZES10 na demonstração.', { exact: true })
      .waitFor();
  });
  await scenario('UI03', 'Recusa de pagamento exibida no fluxo', async () => {
    await fresh();
    await add();
    await page.locator('#payment').selectOption('declined');
    await page.getByRole('button', { name: 'Confirmar pedido simulado' }).click();
    await page.getByRole('heading', { name: 'Pagamento recusado' }).waitFor();
    await page.screenshot({ path: path.join(out, 'pagamento_recusado.png'), fullPage: true });
  });
  await scenario(
    'UI04',
    'Pagamento sem resposta apresenta pendência e opções de conferência simulada',
    async () => {
      await fresh();
      await add();
      await page.locator('#payment').selectOption('timeout');
      await page.getByRole('button', { name: 'Confirmar pedido simulado' }).click();
      await page.getByRole('heading', { name: 'Pagamento pendente' }).waitFor();
      assert.equal(await page.locator('#submit').isDisabled(), true);
      assert.equal(await page.locator('#new').isVisible(), false);
      assert.equal(await page.locator('#resolve-approved').isVisible(), true);
      assert.equal(await page.locator('#resolve-declined').isVisible(), true);
      await page.screenshot({ path: path.join(out, 'pagamento_pendente.png'), fullPage: true });
    },
  );
  await scenario(
    'UI05',
    'Larguras 360, 390 e 768 sem rolagem horizontal e controles de quantidade com 44 px',
    async () => {
      for (const width of [360, 390, 768]) {
        await page.setViewportSize({ width, height: 900 });
        await fresh();
        assert.equal(
          await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
          true,
        );
        const box = await page
          .getByRole('button', { name: 'Adicionar Baião de dois', exact: true })
          .boundingBox();
        assert.ok(box.width >= 44 && box.height >= 44);
        if (width === 390) {
          await add();
          await page.getByLabel('Cupom', { exact: true }).fill('RAIZES10');
          await page.screenshot({ path: path.join(out, 'tela_mobile.png'), fullPage: true });
          await page.locator('.box').screenshot({ path: path.join(out, 'resumo_mobile.png') });
        }
      }
    },
  );
  await scenario(
    'UI06',
    'Aviso de privacidade visível e fidelidade opcional desmarcada',
    async () => {
      await page.setViewportSize({ width: 1366, height: 1000 });
      await fresh();
      assert.equal(await page.locator('#loyalty').isChecked(), false);
      await page.locator('#privacy summary').click();
      await page
        .getByText('Esta demonstração utiliza um identificador fictício.', { exact: false })
        .waitFor();
      assert.equal(await page.locator('input[type=email],input[type=tel]').count(), 0);
      await page.screenshot({ path: path.join(out, 'privacidade.png'), fullPage: true });
      await page.locator('#privacy').screenshot({ path: path.join(out, 'aviso_privacidade.png') });
    },
  );
  await scenario(
    'UI07',
    'Controles ficam bloqueados durante o envio e até iniciar novo pedido',
    async () => {
      await fresh();
      await add();
      let release;
      const gate = new Promise((resolve) => {
        release = resolve;
      });
      await page.route('**/api/orders', async (route) => {
        await gate;
        await route.continue();
      });
      try {
        await page.locator('#submit').click();
        await page.waitForFunction(() => document.querySelector('#unit').disabled);
        for (const selector of [
          '#unit',
          '#channel',
          '#coupon',
          '#payment',
          '#loyalty',
          '.step button',
        ])
          assert.equal(await page.locator(selector).first().isDisabled(), true);
      } finally {
        release();
      }
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      assert.equal(await page.locator('#unit').isDisabled(), true);
      await page.locator('#new').click();
      await page.waitForFunction(() => !document.querySelector('#unit').disabled);
      assert.equal(await page.locator('#submit').isEnabled(), true);
      await page.unroute('**/api/orders');
    },
  );
  await scenario(
    'UI08',
    'Resposta perdida permite repetir o mesmo pedido sem nova baixa de estoque',
    async () => {
      await fresh();
      await add();
      const before = await (await page.request.get(url + '/api/catalog?unit=REC')).json();
      let sentBody;
      await page.route(
        '**/api/orders',
        async (route) => {
          sentBody = route.request().postData();
          await route.fetch();
          await route.abort('failed');
        },
        { times: 1 },
      );
      await page.locator('#submit').click();
      await page.getByRole('heading', { name: 'Conexão interrompida' }).waitFor();
      assert.equal(await page.locator('#unit').isDisabled(), true);
      assert.equal(await page.locator('#submit').isEnabled(), true);
      const retry = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
      await page.locator('#submit').click();
      const response = await retry;
      assert.equal(response.request().postData(), sentBody);
      assert.equal((await response.json()).replayed, true);
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      const after = await (await page.request.get(url + '/api/catalog?unit=REC')).json();
      assert.equal(
        before.find((p) => p.sku === 'baiao').stock - after.find((p) => p.sku === 'baiao').stock,
        2,
      );
      assert.equal(
        before.find((p) => p.sku === 'suco').stock - after.find((p) => p.sku === 'suco').stock,
        1,
      );
    },
  );
  await scenario(
    'UI09',
    'Rascunho mantém unidade, canal, produtos, cupom, fidelidade e pagamento ao recarregar',
    async () => {
      await fresh();
      await page.locator('#unit').selectOption('JPA');
      await ready();
      await page.locator('#channel').selectOption('PICKUP');
      await add();
      await page.locator('#coupon').fill('RAIZES10');
      await page.locator('#loyalty').check();
      await page.locator('#payment').selectOption('declined');
      await page.reload();
      await ready();
      assert.equal(await page.locator('#unit').inputValue(), 'JPA');
      assert.equal(await page.locator('#channel').inputValue(), 'PICKUP');
      assert.equal(await quantity('Baião de dois'), 2);
      assert.equal(await quantity('Suco de cajá'), 1);
      assert.equal(await page.locator('#coupon').inputValue(), 'RAIZES10');
      assert.equal(await page.locator('#loyalty').isChecked(), true);
      assert.equal(await page.locator('#payment').inputValue(), 'declined');
      assert.match(await page.locator('#total').innerText(), /52,20/);
    },
  );
  await scenario(
    'UI10',
    'Confirmação reaparece ao recarregar e novo pedido libera os controles',
    async () => {
      await fresh();
      await add();
      const posted = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
      await page.locator('#submit').click();
      const order = await (await posted).json();
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      await page.reload();
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      assert.ok((await page.locator('#result').innerText()).includes(order.id));
      assert.equal(await page.locator('#submit').isDisabled(), true);
      await page.locator('#new').click();
      await ready();
      assert.equal(await quantity('Baião de dois'), 0);
      assert.equal(await page.locator('#submit').isEnabled(), true);
      await page.reload();
      await ready();
      assert.equal(await quantity('Baião de dois'), 0);
      assert.equal(await page.getByRole('heading', { name: 'Pedido confirmado' }).count(), 0);
    },
  );
  await scenario(
    'UI11',
    'Pendência sobrevive à recarga e pode ser aprovada ou recusada sem duplicar estoque e pontos',
    async () => {
      for (const mode of ['approved', 'declined']) {
        await fresh();
        await add();
        await page.locator('#coupon').fill('RAIZES10');
        await page.locator('#loyalty').check();
        await page.locator('#payment').selectOption('timeout');
        const before = await catalog();
        const posted = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
        await page.locator('#submit').click();
        const pending = await (await posted).json();
        await page.getByRole('heading', { name: 'Pagamento pendente' }).waitFor();
        assert.equal(pending.status, 'PENDENTE');
        assert.equal(pending.points, 0);
        assert.equal(stockDelta(before, await catalog(), 'baiao'), 0);
        await page.reload();
        await page.getByRole('heading', { name: 'Pagamento pendente' }).waitFor();
        assert.equal(await page.locator('#new').isVisible(), false);
        const reconciled = page.waitForResponse((response) =>
          response.url().endsWith('/api/orders/' + pending.id + '/payment'),
        );
        await page.locator('#resolve-' + mode).click();
        const response = await reconciled,
          result = await response.json();
        assert.equal(response.ok(), true);
        assert.equal(result.id, pending.id);
        assert.equal(result.status, mode === 'approved' ? 'CONFIRMADO' : 'RECUSADO');
        assert.equal(result.points, mode === 'approved' ? 52 : 0);
        await page
          .getByRole('heading', {
            name: mode === 'approved' ? 'Pedido confirmado' : 'Pagamento recusado',
          })
          .waitFor();
        const after = await catalog();
        assert.equal(stockDelta(before, after, 'baiao'), mode === 'approved' ? 2 : 0);
        assert.equal(stockDelta(before, after, 'suco'), mode === 'approved' ? 1 : 0);
        assert.equal(await page.locator('#new').isVisible(), true);
        assert.equal(await page.locator('#resolve-approved').isVisible(), false);
        await page.reload();
        await page
          .getByRole('heading', {
            name: mode === 'approved' ? 'Pedido confirmado' : 'Pagamento recusado',
          })
          .waitFor();
        assert.equal(stockDelta(after, await catalog(), 'baiao'), 0);
      }
    },
  );
  await scenario(
    'UI12',
    'Resposta perdida e recarga preservam o corpo e a chave para recuperar a mesma compra',
    async () => {
      await fresh();
      await add();
      const before = await catalog();
      let originalBody;
      await page.route(
        '**/api/orders',
        async (route) => {
          originalBody = route.request().postData();
          await route.fetch();
          await route.abort('failed');
        },
        { times: 1 },
      );
      await page.locator('#submit').click();
      await page.getByRole('heading', { name: 'Conexão interrompida' }).waitFor();
      await page.reload();
      await page.waitForFunction(
        () => document.querySelector('#submit') && !document.querySelector('#submit').disabled,
      );
      assert.equal(await page.locator('#unit').isDisabled(), true);
      const retry = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
      await page.locator('#submit').click();
      const response = await retry,
        result = await response.json();
      assert.equal(response.request().postData(), originalBody);
      assert.equal(result.replayed, true);
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      const after = await catalog();
      assert.equal(stockDelta(before, after, 'baiao'), 2);
      assert.equal(stockDelta(before, after, 'suco'), 1);
    },
  );
  await scenario(
    'UI13',
    'Falhas de catálogo impedem compra com dados antigos e permitem nova tentativa',
    async () => {
      await fresh();
      await page.route('**/api/catalog?**', (route) => route.abort('failed'), { times: 1 });
      await page.reload();
      await page.getByRole('heading', { name: 'Cardápio indisponível' }).waitFor();
      assert.equal(await page.locator('#submit').isDisabled(), true);
      assert.equal(await page.locator('#menu .food').count(), 0);
      await page.locator('#refresh-catalog').click();
      await ready();
      await add();
      await page.route('**/api/catalog?unit=JPA', (route) => route.abort('failed'), { times: 1 });
      await page.locator('#unit').selectOption('JPA');
      await page.getByRole('heading', { name: 'Cardápio indisponível' }).waitFor();
      assert.equal(await page.locator('#menu .food').count(), 0);
      assert.equal(await page.locator('#submit').isDisabled(), true);
      await page.locator('#refresh-catalog').click();
      await ready();
      assert.equal(await page.locator('#unit').inputValue(), 'JPA');
      assert.equal(await quantity('Baião de dois'), 0);
      assert.match(await page.locator('#total').innerText(), /0,00/);
    },
  );
  await scenario(
    'UI14',
    'Quantidade respeita estoque e limite de dez, com botões desabilitados nos limites',
    async () => {
      await fresh();
      await page.route(
        '**/api/catalog?**',
        async (route) => {
          const response = await route.fetch();
          const products = await response.json();
          for (const p of products) p.stock = { baiao: 2, tapioca: 0, suco: 12 }[p.sku];
          await route.fulfill({ response, json: products });
        },
        { times: 1 },
      );
      await page.reload();
      await ready();
      const more = page.getByRole('button', { name: 'Adicionar Baião de dois', exact: true }),
        less = page.getByRole('button', { name: 'Remover Baião de dois', exact: true });
      assert.equal(await less.isDisabled(), true);
      await more.click();
      await more.click();
      assert.equal(await quantity('Baião de dois'), 2);
      assert.equal(await more.isDisabled(), true);
      await less.click();
      assert.equal(await more.isEnabled(), true);
      await less.click();
      assert.equal(await less.isDisabled(), true);
      assert.equal(
        await page
          .getByRole('button', { name: 'Adicionar Tapioca de queijo', exact: true })
          .isDisabled(),
        true,
      );
      const juice = page.getByRole('button', { name: 'Adicionar Suco de cajá', exact: true });
      for (let i = 0; i < 10; i++) await juice.click();
      assert.equal(await quantity('Suco de cajá'), 10);
      assert.equal(await juice.isDisabled(), true);
    },
  );
  await scenario(
    'UI15',
    'Envio sem resposta termina em oito segundos e repete a compra sem duplicação',
    async () => {
      await fresh();
      await add();
      const before = await catalog();
      let originalBody, release;
      const gate = new Promise((resolve) => {
        release = resolve;
      });
      await page.route(
        '**/api/orders',
        async (route) => {
          originalBody = route.request().postData();
          await route.fetch();
          await gate;
          await route.abort('failed').catch(() => {});
        },
        { times: 1 },
      );
      try {
        const started = Date.now();
        await page.locator('#submit').click();
        await page
          .getByRole('heading', { name: 'Conexão interrompida' })
          .waitFor({ timeout: 13000 });
        assert.ok(
          Date.now() - started < 13000,
          'O envio precisa liberar a tentativa após o limite de espera.',
        );
        assert.equal(await page.locator('#submit').isEnabled(), true);
        assert.equal(await page.locator('#unit').isDisabled(), true);
      } finally {
        release();
      }
      const retry = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
      await page.locator('#submit').click();
      const response = await retry,
        result = await response.json();
      assert.equal(response.request().postData(), originalBody);
      assert.equal(result.replayed, true);
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      const after = await catalog();
      assert.equal(stockDelta(before, after, 'baiao'), 2);
      assert.equal(stockDelta(before, after, 'suco'), 1);
    },
  );
  await scenario(
    'UI16',
    'Sessão expirada pode ser atualizada preservando a tentativa de compra',
    async () => {
      await fresh();
      await add();
      const before = await catalog();
      let originalBody;
      await page.route(
        '**/api/orders',
        async (route) => {
          originalBody = route.request().postData();
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({
              code: 'SESSAO_EXPIRADA',
              message: 'Sessão expirada. Atualize a página.',
            }),
          });
        },
        { times: 1 },
      );
      await page.locator('#submit').click();
      await page.locator('#refresh-session').waitFor({ state: 'visible' });
      await page.locator('#refresh-session').click();
      await page.waitForFunction(
        () => document.querySelector('#submit') && !document.querySelector('#submit').disabled,
      );
      const posted = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
      await page.locator('#submit').click();
      const response = await posted,
        result = await response.json();
      assert.equal(response.request().postData(), originalBody);
      assert.equal(result.status, 'CONFIRMADO');
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      const after = await catalog();
      assert.equal(stockDelta(before, after, 'baiao'), 2);
      assert.equal(stockDelta(before, after, 'suco'), 1);
    },
  );
  await scenario(
    'UI17',
    'Recarregar durante o envio recupera o mesmo pedido sem uma nova compra',
    async () => {
      await fresh();
      await add();
      const before = await catalog();
      let originalBody, release, committed;
      const gate = new Promise((resolve) => {
          release = resolve;
        }),
        saved = new Promise((resolve) => {
          committed = resolve;
        });
      await page.route(
        '**/api/orders',
        async (route) => {
          originalBody = route.request().postData();
          try {
            await route.fetch();
            committed();
            await gate;
            await route.abort('failed').catch(() => {});
          } catch (error) {
            committed(error);
          }
        },
        { times: 1 },
      );
      try {
        await page.locator('#submit').click();
        const failure = await saved;
        if (failure) throw failure;
        assert.equal(await page.locator('#submit').isDisabled(), true);
        await page.reload();
      } finally {
        release();
      }
      await page.getByRole('heading', { name: 'Pedido em conferência' }).waitFor();
      await page.waitForFunction(() => !document.querySelector('#submit').disabled);
      const retry = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
      await page.locator('#submit').click();
      const response = await retry,
        result = await response.json();
      assert.equal(response.request().postData(), originalBody);
      assert.equal(result.replayed, true);
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      const after = await catalog();
      assert.equal(stockDelta(before, after, 'baiao'), 2);
      assert.equal(stockDelta(before, after, 'suco'), 1);
    },
  );
  await scenario(
    'UI18',
    'Resposta perdida na conferência bloqueia a opção oposta e recarga recupera a aprovação',
    async () => {
      await fresh();
      await add();
      await page.locator('#loyalty').check();
      await page.locator('#payment').selectOption('timeout');
      const before = await catalog();
      const posted = page.waitForResponse((response) => response.url().endsWith('/api/orders'));
      await page.locator('#submit').click();
      const pending = await (await posted).json();
      await page.getByRole('heading', { name: 'Pagamento pendente' }).waitFor();
      await page.route(
        '**/api/orders/' + pending.id + '/payment',
        async (route) => {
          await route.fetch();
          await route.abort('failed');
        },
        { times: 1 },
      );
      await page.locator('#resolve-approved').click();
      await page
        .getByText(
          'A conferência não respondeu. Repita a mesma opção para consultar o resultado, sem duplicar estoque ou pontos.',
          { exact: true },
        )
        .waitFor();
      assert.equal(await page.locator('#resolve-declined').isDisabled(), true);
      assert.equal(await page.locator('#resolve-approved').isEnabled(), true);
      await page.reload();
      await page.getByRole('heading', { name: 'Pedido confirmado' }).waitFor();
      assert.ok((await page.locator('#result').innerText()).includes(pending.id));
      assert.match(await page.locator('#result').innerText(), /58 pontos/);
      assert.equal(await page.locator('#new').isVisible(), true);
      const after = await catalog();
      assert.equal(stockDelta(before, after, 'baiao'), 2);
      assert.equal(stockDelta(before, after, 'suco'), 1);
    },
  );
  assert.deepEqual(errors, []);
} catch (error) {
  runtimeError = error.message;
  process.exitCode = 1;
  console.error('Falha na verificação: ' + error.message);
} finally {
  await fs.writeFile(
    path.join(out, 'interface.json'),
    JSON.stringify(
      {
        timestamp_utc: new Date().toISOString(),
        engine: browser ? browser.version() : 'não iniciado',
        total: rows.length,
        passed: rows.filter((r) => r.status === 'APROVADO').length,
        tests: rows,
        page_errors: errors,
        runtime_error: runtimeError,
        environment: 'Servidor e banco temporários, isolados da demonstração.',
        limitation:
          'Google Chrome desktop com redimensionamento; não substitui UAT nem teste em aparelho físico.',
      },
      null,
      2,
    ),
  );
  if (browser) await browser.close();
  if (server && server.exitCode === null) {
    const stopped = once(server, 'exit');
    server.kill();
    await stopped;
  }
  if (tempDir)
    await fs.rm(tempDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  console.log(
    JSON.stringify({
      total: rows.length,
      passed: rows.filter((r) => r.status === 'APROVADO').length,
      errors,
      runtime_error: runtimeError,
    }),
  );
}
