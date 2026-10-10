# Raízes do Nordeste

## [Abrir demonstração online](https://dmfariaas.github.io/raizes-do-nordeste/)

O restaurante pode ser acessado pelo navegador do computador, celular ou tablet. Para usar a versão online, basta abrir o link acima. Não é preciso instalar Python ou manter o computador do autor ligado.

Este projeto acadêmico trata da qualidade de software no atendimento de uma rede fictícia de restaurantes. A questão central é simples: quando um pedido é confirmado, o valor do pagamento, o estoque e os pontos de fidelidade precisam corresponder à mesma compra.

Aqui estão o relatório, a planilha de métricas, as evidências dos testes e as duas versões da demonstração: uma online e outra local, em Python e SQLite. O trabalho estabelece oito requisitos funcionais e oito requisitos de qualidade, com critérios de aceitação e indicação das verificações previstas.

**Diego Monteiro de Farias · RU 4992220**

Análise e Desenvolvimento de Sistemas — Centro Universitário Internacional UNINTER.
Projeto Multidisciplinar — Trilha de Qualidade de Software · 2026.

[Relatório em PDF][entrega] · [Texto do relatório][relatorio] · [Planilha de métricas][planilha]

![Interface do restaurante Raízes do Nordeste, com cardápio e resumo do pedido][previa]

## O protótipo

O protótipo recebe pedidos para as unidades de Recife (`REC`) e João Pessoa (`JPA`), com estoques separados. A mesma tela permite escolher cinco canais de atendimento: aplicativo, web, totem, balcão e retirada.

O fluxo permite:

- Montar um carrinho com baião de dois, tapioca de queijo e suco de cajá, com até dez unidades de cada produto.
- Aplicar o cupom `RAIZES10`, que desconta 10% do subtotal.
- Participar da fidelidade e receber um ponto por real inteiro do total confirmado.
- Simular pagamento aprovado, recusado ou sem resposta, além de resolver uma pendência.
- Reenviar uma solicitação sem duplicar o pedido, a baixa de estoque ou os pontos.
- Recuperar o carrinho e o resultado ao recarregar a mesma aba.

Os pagamentos e as identidades são fictícios. A demonstração não realiza cobranças nem solicita dados de cartão.

## Usar a demonstração online

Abra o [site do restaurante](https://dmfariaas.github.io/raizes-do-nordeste/), escolha a unidade e monte seu pedido. Na etapa de pagamento, selecione o resultado que deseja experimentar.

Pedidos, estoque e pontos ficam no IndexedDB, um banco de dados do próprio navegador. Por isso, a compra feita em um dispositivo não aparece em outro. Limpar os dados do site apaga esses registros. Na navegação privada, eles também podem ser descartados ao encerrar a sessão.

Para começar de novo, abra **Como os dados são usados** e selecione **Reiniciar demonstração**. Isso apaga os dados da demonstração nesse navegador e restaura o estoque inicial.

O guia de [`site_online/`](site_online/README.md) explica a organização do código, os testes e a publicação dessa versão.

## Executar a versão local (Python e SQLite)

A execução local exige **Python 3.11 ou superior** e um navegador. Como o servidor usa a biblioteca padrão do Python, não há pacotes adicionais para instalar com `pip`.

Na raiz do repositório, execute:

```powershell
cd "4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/prototipo"
python api.py --open-browser
```

Acesse **http://127.0.0.1:8765** no computador em que o servidor foi iniciado. Esse é o endereço da execução local. Para compartilhar o restaurante, use o link público no início deste guia. No Windows, `py -3` pode substituir `python`. No Linux e no macOS, use `python3` se esse for o nome disponível. Para encerrar o servidor, pressione **Ctrl+C** no terminal.

No Windows, também é possível abrir o arquivo [`ABRIR_RESTAURANTE_NORDESTINO.cmd`](ABRIR_RESTAURANTE_NORDESTINO.cmd) com dois cliques. Ele verifica o Python, escolhe uma porta livre e abre o navegador.

### Banco de dados e porta

Na execução pelo código-fonte, o banco `prototipo/demo.sqlite3` é criado automaticamente na primeira inicialização e mantém os pedidos entre execuções. O inicializador da raiz guarda seus dados em `%LOCALAPPDATA%\ProjetoQualidade4992220\dados\demo.sqlite3`.

Para usar uma porta livre e começar com outro banco, execute na pasta `prototipo`:

```powershell
python api.py --port 0 --db nova-demonstracao.sqlite3 --open-browser
```

Um nome de banco ainda não utilizado cria uma demonstração com estoque novo. Para recuperar a tela após uma recarga, mantenha a mesma aba e o mesmo endereço, incluindo a porta.

### Exemplo de pedido

Adicione **dois baiões de dois** e **um suco de cajá**, aplique `RAIZES10`, marque a fidelidade e escolha pagamento aprovado. O resultado esperado é:

- Subtotal: **R$ 58,00**.
- Desconto: **R$ 5,80**.
- Total: **R$ 52,20**, com **52 pontos**.

Após a confirmação, recarregue a aba e confira se o resultado foi recuperado. Em seguida, abra novos pedidos para experimentar a recusa e a ausência de resposta do pagamento.

### API local

O servidor atende apenas em `127.0.0.1`.

| Método | Rota | Uso |
| --- | --- | --- |
| `GET` | `/api/health` | Estado do servidor. |
| `GET` | `/api/catalog?unit=REC` | Produtos e estoque de `REC` ou `JPA`. |
| `POST` | `/api/orders` | Criação ou recuperação de um pedido. |
| `GET` | `/api/orders/{id}` | Consulta de um pedido da identidade de demonstração. |
| `POST` | `/api/orders/{id}/payment` | Resolução de pagamento pendente. |

As rotas de pedidos exigem `Authorization: Bearer <token>`. O token é gerado a cada inicialização e enviado automaticamente pela interface. Ele representa uma sessão de demonstração, sem cadastro de usuários.

## Organização do código

As duas interfaces usam HTML, CSS e JavaScript. Os cálculos monetários são feitos em centavos. Na versão online, as regras são executadas no navegador e os registros ficam no IndexedDB. Na versão local, um servidor HTTP em Python atende às solicitações e grava os dados em SQLite.

```text
.
├── README.md
├── site_online/
│   ├── README.md
│   ├── dist/                    # Arquivos do site publicado
│   └── tests/                   # Testes da versão online
├── ABRIR_RESTAURANTE_NORDESTINO.cmd
├── 4992220_Projeto_Qualidade.md
├── 4992220_Metricas_Qualidade.xlsx
├── entrega/
│   └── 4992220_Projeto_Qualidade.PDF
└── 4992220_Projeto_Qualidade_Completo/
    └── Projeto_Qualidade_4992220/
        ├── INICIAR_DEMONSTRACAO.cmd
        ├── LEIA_PRIMEIRO.md
        ├── qa_interface.mjs
        ├── prototipo/
        │   ├── index.html          # Interface e interação
        │   ├── api.py              # Servidor HTTP e rotas
        │   ├── domain.py           # Validação e cálculos
        │   ├── service.py          # Pedidos e pagamento simulado
        │   ├── repository.py       # Persistência SQLite
        │   ├── tests.py            # Testes de regras, API e concorrência
        │   └── run_evidence.py     # Coleta de resultados e ensaio de carga
        ├── evidencias/             # Resultados, logs e capturas
        └── output/                 # Documentos do pacote acadêmico
```

A árvore resume os principais arquivos. Bancos da demonstração, caches e dependências instaladas na máquina ficam fora do versionamento.

Na versão local, o serviço de pedidos usa transações SQLite para coordenar pagamento, estoque e fidelidade. Cada solicitação recebe uma chave de idempotência, que permite reconhecer repetições. Se o mesmo pedido for reenviado, o serviço devolve o resultado já registrado. Se a chave for reutilizada com outro conteúdo, o retorno indica um conflito.

## Testes da versão online

Em **10 de outubro de 2026**, a versão online passou em **31 testes automatizados**: 20 de regras e armazenamento e 11 de integração da interface em DOM simulado. O endereço HTTPS e os arquivos JavaScript também responderam sem login. Consulte o [registro de validação](site_online/VALIDACAO.md) para o alcance dessas verificações.

Para repetir essa verificação, siga as instruções do [guia de `site_online`](site_online/README.md#testes). Os resultados da versão Python, apresentados a seguir, vêm de outra implementação e de outra execução de testes.

## Testes da versão local (Python e SQLite)

### Regras, API e concorrência

Na pasta `prototipo`:

```powershell
python -m unittest -v tests
```

Para executar a suíte e o ensaio de carga de **200 pedidos com dez tarefas concorrentes**:

```powershell
python run_evidence.py
```

O segundo comando atualiza `testes.txt`, `testes.json`, `desempenho.json` e `fontes_sha256.json` na pasta `evidencias`. Os testes usam bancos temporários, separados do banco da demonstração.

### Interface

Com **Node.js 20 ou superior**, npm e Google Chrome instalados, execute na pasta `4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220`:

```powershell
npm install --no-save playwright
node qa_interface.mjs
```

Se o PowerShell bloquear `npm.ps1`, use `npm.cmd install --no-save playwright`.

O script inicia um servidor com banco temporário e executa os testes no Chrome sem abrir uma janela. Os resultados e as capturas são atualizados em `evidencias`. As variáveis `DEMO_PYTHON` e `DEMO_EVIDENCE_DIR` permitem definir outro executável Python e outra pasta de saída.

### Resultados registrados

As evidências acadêmicas de **24 de setembro de 2026**, referentes à versão local em Python e SQLite, apresentam os seguintes resultados:

| Verificação | Resultado | Fonte |
| --- | --- | --- |
| Testes Python | 52 de 52 aprovados | [testes.json][testes] |
| Testes de interface | 18 de 18 aprovados | [interface.json][interface] |
| Ensaio de carga | 200 de 200 pedidos bem-sucedidos | [desempenho.json][desempenho] |
| Tempo de resposta na carga | Média de 58,867 ms e percentil 95 de 208,004 ms | [desempenho.json][desempenho] |

Esses tempos foram obtidos na máquina de teste, com SQLite e pagamento simulado, sem a espera por um serviço externo. Eles variam com o ambiente e não permitem estimar o desempenho em produção. A cobertura de 100% citada no relatório significa que os oito requisitos funcionais têm testes associados. Esse indicador não mede a cobertura de código.

Os arquivos de evidências conservam os resultados daquela execução. Os hashes em `fontes_sha256.json` identificam o código anterior à formatação, portanto não devem ser usados como registro de uma nova medição.

## Documentação

- [Relatório em PDF][entrega]: versão preparada para a entrega acadêmica, com requisitos, plano de qualidade, testes, métricas e análise dos resultados.
- [Relatório em Markdown][relatorio]: texto editável do trabalho.
- [Planilha de métricas][planilha]: fórmulas, resultados individuais dos testes e amostras de carga.
- [Guia da demonstração][guia]: instruções de uso e desenvolvimento do pacote.
- [Evidências][evidencias]: arquivos de resultados e capturas da interface em desktop e mobile.

## Limitações

O projeto tem alcance acadêmico: os pagamentos são simulados, não há autenticação de clientes reais e os cinco canais são opções de uma única interface. Na versão online, os dados pertencem ao navegador, sem sincronização entre dispositivos. Na versão Python, os pedidos ficam no SQLite local e o estado da tela é mantido na sessão da aba.

Os testes de concorrência do pacote acadêmico avaliam o SQLite local. Ainda faltam medições de disponibilidade mensal, satisfação dos usuários e aceite de negócio, além de testes em aparelhos físicos e de estresse prolongado. A planilha identifica como **Não medido** tudo o que ainda não teve coleta.

[entrega]: entrega/4992220_Projeto_Qualidade.PDF
[relatorio]: 4992220_Projeto_Qualidade.md
[planilha]: 4992220_Metricas_Qualidade.xlsx
[guia]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/LEIA_PRIMEIRO.md
[previa]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias/previa_restaurante.png
[evidencias]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias
[testes]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias/testes.json
[interface]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias/interface.json
[desempenho]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias/desempenho.json
