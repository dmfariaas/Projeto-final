# Verificação da demonstração online

Data: 10 de outubro de 2026.

Endereço publicado: https://raizes-do-nordeste-demo.dmfariaas.chatgpt.site

## Resultado

- 20 testes de regras e armazenamento aprovados com Node.js e fake-indexeddb.
- 11 testes de integração da interface aprovados com jsdom.
- Total: 31 testes aprovados, sem falhas; duração da rodada final: 11,44 segundos, em Node.js 24.19.0.
- Publicação concluída com acesso público, sem exigir cadastro ou login.
- `index.html`, `app.js` e `demo-store.js` responderam HTTP 200 a requisições sem sessão autenticada.
- Os módulos JavaScript publicados contêm a mesma implementação testada; a cópia no GitHub apenas normaliza as linhas vazias finais. A hospedagem acrescenta ao HTML um script próprio do Cloudflare; a interface e a importação de `app.js` foram preservadas.

Os testes exercitam cálculo em centavos, desconto, fidelidade, carrinho, pagamentos aprovados/recusados/pendentes, resolução da pendência, reenvio, conflito de chave, concorrência pelo último item do estoque, separação entre unidades, recuperação, validação das entradas, cancelamento e reinicialização.

## Alcance

A integração da interface foi testada em DOM simulado, sem automação visual de um navegador real, pois a ferramenta de navegador estava indisponível nesta sessão. Não foi feito um teste físico em outro computador ou celular. A disponibilidade pública foi confirmada pela hospedagem e por requisições HTTPS sem autenticação.

Os dados pertencem à demonstração de cada navegador. As verificações não avaliam pagamentos reais, autenticação comercial ou sincronização entre aparelhos. As evidências Python/SQLite do trabalho acadêmico original permanecem separadas e não foram substituídas por esta rodada.
