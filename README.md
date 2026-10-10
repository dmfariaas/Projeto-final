# Raízes do Nordeste

## [Abrir demonstração online](https://dmfariaas.github.io/raizes-do-nordeste/)

Acesse o restaurante pelo navegador do computador, celular ou tablet. A versão online não precisa de Python instalado nem depende de o computador do autor estar ligado.

Projeto acadêmico de qualidade de software para o fluxo de pedidos de uma rede fictícia de restaurantes. O foco é manter a confirmação do pedido coerente com o valor pago, a baixa de estoque e os pontos de fidelidade.

O repositório reúne o relatório, a planilha de métricas, as evidências dos testes, a demonstração online e o protótipo local em Python e SQLite. O trabalho define oito requisitos funcionais e oito requisitos de qualidade, com critérios de aceitação e testes associados.

**Diego Monteiro de Farias · RU 4992220**

Análise e Desenvolvimento de Sistemas — Centro Universitário Internacional UNINTER.
Projeto Multidisciplinar — Trilha de Qualidade de Software · 2026.

[Relatório em PDF][entrega] · [Texto do relatório][relatorio] · [Planilha de métricas][planilha]

![Interface do restaurante Raízes do Nordeste, com cardápio e resumo do pedido][previa]

## O protótipo

A demonstração acompanha pedidos nas unidades de Recife (`REC`) e João Pessoa (`JPA`), cada uma com seu estoque. Aplicativo, web, totem, balcão e retirada aparecem como opções de canal na mesma interface.

O fluxo permite:

- Montar um carrinho com baião de dois, tapioca de queijo e suco de cajá, com até dez unidades de cada produto.
- Aplicar o cupom `RAIZES10`, que desconta 10% do subtotal.
- Participar da fidelidade e receber um ponto por real inteiro do total confirmado.
- Simular pagamento aprovado, recusado ou sem resposta, além de resolver uma pendência.
- Reenviar uma solicitação sem duplicar o pedido, a baixa de estoque ou os pontos.
- Recuperar o carrinho e o resultado ao recarregar a mesma aba.

Os pagamentos e as identidades são fictícios. A demonstração não realiza cobranças nem solicita dados de cartão.

## Usar a demonstração online

Abra o [site do restaurante](https://dmfariaas.github.io/raizes-do-nordeste/), escolha a unidade e monte seu pedido. Os pagamentos são fictícios: nenhuma cobrança é realizada e não são pedidos dados de cartão.

Os pedidos, o estoque e os pontos da demonstração ficam no IndexedDB, o banco de dados do próprio navegador. Cada navegador e dispositivo tem seus próprios dados, sem sincronização. Limpar os dados do site também remove essas informações; no modo de navegação privada, elas podem ser descartadas ao fechar a sessão.

Para começar de novo, abra **Como os dados são usados** e selecione **Reiniciar demonstração**. Isso apaga os dados da demonstração nesse navegador e restaura o estoque inicial.

O código e as instruções de desenvolvimento dessa versão estão em [`site_online/`](site_online/README.md).

## Executar a versão local (Python e SQLite)

É necessário ter **Python 3.11 ou superior** e um navegador. O servidor usa apenas a biblioteca padrão do Python, sem dependências para instalar com `pip`.

Na raiz do repositório, execute:

```powershell
cd "4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/prototipo"
python api.py --open-browser
```

O servidor abre em **http://127.0.0.1:8765**. Esse endereço funciona apenas no computador em que o servidor foi iniciado; ele não é o link público do restaurante. No Windows, `py -3` pode substituir `python`; no Linux e no macOS, use `python3` se esse for o nome disponível. Para encerrar, pressione **Ctrl+C** no terminal.

No Windows, também é possível abrir o arquivo [`ABRIR_RESTAURANTE_NORDESTINO.cmd`](ABRIR_RESTAURANTE_NORDESTINO.cmd) com dois cliques. Ele verifica o Python, escolhe uma porta livre e abre o navegador.

### Banco de dados e porta

Na execução pelo código-fonte, o banco `prototipo/demo.sqlite3` é criado automaticamente na primeira inicialização e mantém os pedidos entre execuções. O inicializador da raiz guarda seus dados em `%LOCALAPPDATA%\ProjetoQualidade4992220\dados\demo.sqlite3`.

Para usar uma porta livre e começar com outro banco, execute na pasta `prototipo`:

```powershell
python api.py --port 0 --db nova-demonstracao.sqlite3 --open-browser
```

Use um nome de banco que ainda não exista para obter um estoque novo. A recuperação da tela depende da mesma aba e do mesmo endereço, incluindo a porta.

### Exemplo de pedido

Adicione **dois baiões de dois** e **um suco de cajá**, aplique `RAIZES10`, marque a fidelidade e escolha pagamento aprovado. O resultado esperado é:

- Subtotal: **R$ 58,00**.
- Desconto: **R$ 5,80**.
- Total: **R$ 52,20**, com **52 pontos**.

Depois da confirmação, recarregue a aba para conferir a recuperação do resultado. Em um novo pedido, experimente a recusa e a ausência de resposta do pagamento.

### API local

O servidor atende apenas em `127.0.0.1`.

| Método | Rota | Uso |
| --- | --- | --- |
| `GET` | `/api/health` | Estado do servidor. |
| `GET` | `/api/catalog?unit=REC` | Produtos e estoque de `REC` ou `JPA`. |
| `POST` | `/api/orders` | Criação ou recuperação de um pedido. |
| `GET` | `/api/orders/{id}` | Consulta de um pedido da identidade de demonstração. |
| `POST` | `/api/orders/{id}/payment` | Resolução de pagamento pendente. |

As rotas de pedidos exigem `Authorization: Bearer <token>`. O token é gerado a cada inicialização e enviado automaticamente pela interface. Ele representa uma sessão de demonstração; não há cadastro de usuários.

## Organização do código

As duas versões usam HTML, CSS e JavaScript na interface e calculam os valores monetários em centavos. A versão online executa as regras de demonstração no navegador, com persistência em IndexedDB. A versão local usa um servidor HTTP em Python e persistência em SQLite.

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
        ├── package.json
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

A árvore mostra os principais arquivos. O banco da demonstração, os caches e as dependências instaladas localmente não fazem parte do versionamento.

Na versão local, o serviço de pedidos coordena pagamento, estoque e fidelidade em transações SQLite. Uma chave de idempotência identifica cada solicitação: o reenvio recupera o resultado existente; a mesma chave com conteúdo diferente gera um conflito.

## Testes da versão online

Em **10 de outubro de 2026**, a versão online passou em **31 testes automatizados**: 20 de regras e armazenamento e 11 de integração da interface em DOM simulado. O endereço HTTPS e os arquivos JavaScript também responderam sem login. Consulte o [registro de validação](site_online/VALIDACAO.md) para o alcance dessas verificações.

As instruções para executar os testes das regras e da interface online estão no [guia de `site_online`](site_online/README.md#testes). Essa verificação é independente das evidências acadêmicas da versão Python descritas abaixo.

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
npm ci
npm test
```

Se o PowerShell bloquear `npm.ps1`, use `npm.cmd ci` e `npm.cmd test`.

O script inicia um servidor com banco temporário e executa os testes no Chrome sem abrir uma janela. Os resultados e as capturas são atualizados em `evidencias`. As variáveis `DEMO_PYTHON` e `DEMO_EVIDENCE_DIR` permitem definir outro executável Python e outra pasta de saída.

### Resultados registrados

As evidências acadêmicas de **24 de setembro de 2026**, referentes à versão local em Python e SQLite, apresentam os seguintes resultados:

| Verificação | Resultado | Fonte |
| --- | --- | --- |
| Testes Python | 52 de 52 aprovados | [testes.json][testes] |
| Testes de interface | 18 de 18 aprovados | [interface.json][interface] |
| Ensaio de carga | 200 de 200 pedidos bem-sucedidos | [desempenho.json][desempenho] |
| Tempo de resposta na carga | Média de 58,867 ms; percentil 95 de 208,004 ms | [desempenho.json][desempenho] |

Os tempos foram medidos localmente, com SQLite e pagamento simulado sem latência externa. Eles variam conforme o ambiente e não representam desempenho em produção. A cobertura de 100% citada no relatório se refere aos oito requisitos funcionais com testes associados, não à cobertura de código.

As evidências dessa execução foram preservadas durante a preparação do repositório. Os hashes em `fontes_sha256.json` correspondem ao código anterior à formatação; essa revisão não substitui a medição acadêmica registrada.

## Documentação

- [Relatório em PDF][entrega]: versão preparada para a entrega acadêmica, com requisitos, plano de qualidade, testes, métricas e análise dos resultados.
- [Relatório em Markdown][relatorio]: texto editável do trabalho.
- [Planilha de métricas][planilha]: fórmulas, resultados individuais dos testes e amostras de carga.
- [Guia da demonstração][guia]: instruções de uso e desenvolvimento do pacote.
- [Evidências][evidencias]: arquivos de resultados e capturas da interface em desktop e mobile.

## Limitações

As duas versões foram desenvolvidas para demonstração acadêmica. Não integram um provedor de pagamento, não possuem autenticação de usuários reais e representam os cinco canais em uma única interface. Na versão online, os dados ficam no navegador e não são sincronizados entre dispositivos. Na versão Python, os pedidos ficam no banco SQLite local e o estado da tela fica na sessão da aba.

Os testes de concorrência registrados no pacote acadêmico cobrem o uso de SQLite local; seus resultados não medem a versão online. Disponibilidade mensal, satisfação dos usuários, aceite de negócio, testes em aparelhos físicos e estresse prolongado ainda dependem de avaliação. As métricas sem coleta permanecem identificadas como **Não medido** na planilha.

[entrega]: entrega/4992220_Projeto_Qualidade.PDF
[relatorio]: 4992220_Projeto_Qualidade.md
[planilha]: 4992220_Metricas_Qualidade.xlsx
[guia]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/LEIA_PRIMEIRO.md
[previa]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias/previa_restaurante.png
[evidencias]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias
[testes]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias/testes.json
[interface]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias/interface.json
[desempenho]: 4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/evidencias/desempenho.json
