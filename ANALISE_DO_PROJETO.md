# Análise do projeto Raízes do Nordeste

Revisão de 16 de outubro de 2026.

A comparação entre o GitHub e a pasta da Área de Trabalho encontrou melhorias que ainda não estavam publicadas. A versão consolidada incorpora essas alterações e mantém as revisões mais recentes de redação, pontuação e abertura da demonstração.

## Alterações consolidadas

| Situação encontrada | Resultado da revisão |
|---|---|
| A versão publicada registrava 52 testes Python, enquanto a revisão local tinha 54. | Os casos API09 e API10 e suas correções foram incorporados. O relatório e a planilha apresentam 72 testes acadêmicos: 54 Python e 18 no navegador. |
| A conexão podia ser interrompida após salvar a compra. | O servidor encerra a conexão sem tentar enviar uma segunda resposta. A repetição da mesma solicitação recupera o pedido salvo. |
| Um corpo menor que o tamanho declarado poderia chegar ao processamento. | O corpo incompleto é rejeitado antes de criar o pedido. |
| Havia melhorias locais na organização das transações e na inicialização. | As operações de estoque, pontos e confirmação foram organizadas em funções próprias. O iniciador aguarda o servidor ficar pronto e permite fechar sua janela sem encerrar o serviço. |
| Os documentos de setembro e as revisões de outubro estavam em cópias diferentes. | PDF, Markdown, planilha, código, iniciadores e ZIP foram reunidos em uma entrega coerente. |

## Verificações realizadas

| Verificação | Resultado |
|---|---|
| Regras, API, concorrência e persistência em Python | 54 testes aprovados. |
| Interface local no Chrome com Playwright | 18 cenários aprovados após a formatação do HTML. |
| Demonstração online | 31 testes aprovados: 20 de regras e armazenamento e 11 de interface com DOM simulado. |
| Instalação das ferramentas de interface | `npm ci` reproduziu as dependências do arquivo de versões. |
| Formatação da interface e da automação | `npm run format:check` aprovado. |
| Documento final | Na revisão documental de 26/10/2026, passou a 46 páginas e 81 entradas de sumário, com a declaração de uso de IA ao final. Permanecem 16 quadros e 5 figuras. Margens, numeração e páginas renderizadas conferidas. |
| Publicação online | Página, JavaScript da interface e armazenamento responderam HTTP 200. Seus conteúdos coincidem com a versão do repositório público. |

Os testes atuais foram executados separadamente dos registros acadêmicos. O relatório mantém as medições de 28 de setembro de 2026: 200 pedidos bem-sucedidos, média de 61,121 ms e p95 de 149,676 ms. Esses tempos descrevem aquela execução local. Os hashes de setembro identificam a versão histórica, enquanto `evidencias/consolidacao_2026-10-16.json` identifica as fontes consolidadas.

## Acesso ao restaurante

O endereço para compartilhar é [https://dmfariaas.github.io/raizes-do-nordeste/](https://dmfariaas.github.io/raizes-do-nordeste/). Ele funciona sem depender do computador do autor estar ligado.

O endereço `http://127.0.0.1:8765/` atende à demonstração local. Para usá-lo, é necessário iniciar o servidor naquele computador. O arquivo `ABRIR_RESTAURANTE_NORDESTINO.cmd` usa a porta 8765 por padrão e reutiliza uma demonstração já aberta. Se outro serviço ocupar essa porta, ele informa o conflito e preserva o processo existente.

## Parecer

Os fluxos avaliados estão adequados à demonstração acadêmica com pagamentos simulados. Os testes verificam cálculos, cupom, fidelidade, estoque separado por unidade, prevenção de duplicação, resolução de pendências e recuperação da interface.

A versão online armazena dados no próprio navegador. Por isso, pedidos de um aparelho não aparecem em outro. A disponibilidade mensal, a avaliação com participantes, os aparelhos físicos e o estresse prolongado continuam como atividades planejadas no trabalho. A aprovação dos testes descritos não substitui essas avaliações.

As cópias antigas da Área de Trabalho foram preservadas. Para baixar o conjunto consolidado, use a branch `main` deste repositório e seu pacote ZIP atualizado.
