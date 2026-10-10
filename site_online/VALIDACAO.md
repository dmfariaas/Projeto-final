# Verificação da demonstração online

Data: 10 de outubro de 2026.

Endereço publicado: https://dmfariaas.github.io/raizes-do-nordeste/

Hospedagem: GitHub Pages, pela branch `main` do repositório público [raizes-do-nordeste](https://github.com/dmfariaas/raizes-do-nordeste). Publicação confirmada para o commit `2d173bb4a130ebb470009ad741a1e415154f8551`.

## Resultado

- 20 testes de regras e armazenamento aprovados com Node.js e fake-indexeddb.
- 11 testes de integração da interface aprovados com jsdom.
- Total: 31 testes aprovados, sem falhas. A rodada final durou 7,33 segundos, em Node.js 24.19.0.
- Os testes de interface foram repetidos com a URL `https://dmfariaas.github.io/raizes-do-nordeste/` configurada no DOM simulado, incluindo o caminho da subpasta.
- Publicação concluída com acesso público, sem exigir cadastro ou login.
- `index.html`, `app.js` e `demo-store.js` responderam HTTP 200 a requisições sem sessão autenticada.
- O conteúdo dos três arquivos recebidos pela hospedagem foi comparado byte a byte com o commit publicado: todos coincidiram. Os módulos usam caminhos relativos e o site não depende de um servidor local.

Os testes exercitam cálculo em centavos, desconto, fidelidade, carrinho, pagamentos aprovados/recusados/pendentes, resolução da pendência, reenvio, conflito de chave, concorrência pelo último item do estoque, separação entre unidades, recuperação, validação das entradas, cancelamento e reinicialização.

## Alcance

A integração da interface foi testada em DOM simulado, sem automação visual de um navegador real, pois a ferramenta de navegador estava indisponível nesta sessão. Não foi feito um teste físico em outro computador ou celular. A disponibilidade pública foi confirmada pela hospedagem e por requisições HTTPS sem autenticação.

Os dados pertencem à demonstração de cada navegador. As verificações não avaliam pagamentos reais, autenticação comercial ou sincronização entre aparelhos. As evidências Python/SQLite do trabalho acadêmico original permanecem separadas e não foram substituídas por esta rodada.
