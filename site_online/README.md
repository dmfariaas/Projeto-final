# Raízes do Nordeste — demonstração online

[Abrir o restaurante](https://dmfariaas.github.io/raizes-do-nordeste/)

Esta versão permite apresentar o restaurante em computadores, celulares e tablets com um navegador atual. Os arquivos estáticos ficam hospedados na web; o visitante não precisa instalar Python nem manter o computador do autor ligado.

## O que pode ser demonstrado

- Escolha das unidades de Recife e João Pessoa e dos cinco canais de atendimento.
- Carrinho, conferência de valores, cupom `RAIZES10` e fidelidade.
- Pagamento aprovado, recusado ou pendente, com resolução da pendência.
- Reenvio de uma solicitação sem duplicar o pedido, a baixa de estoque ou os pontos.
- Recuperação da demonstração ao recarregar a página.

Os pagamentos são fictícios, sem cobrança e sem coleta de dados de cartão.

## Dados da demonstração

Pedidos, estoque e pontos ficam em IndexedDB, no navegador de quem está usando o site. Esses dados não são sincronizados entre navegadores ou dispositivos. Limpar os dados do site remove a demonstração; a navegação privada também pode descartar os dados ao encerrar a sessão.

Para apagar os dados da demonstração e restaurar o estoque inicial, abra **Como os dados são usados** e selecione **Reiniciar demonstração**.

A execução das regras no navegador é adequada a esta apresentação acadêmica. Não há servidor de pedidos, contas de usuários ou integração com uma operadora de pagamentos nesta versão. O protótipo Python e SQLite permanece no [pacote acadêmico](../4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/).

## Arquivos

| Caminho | Responsabilidade |
| --- | --- |
| `dist/index.html` | Estrutura, aparência e conteúdo da página. |
| `dist/app.js` | Interação da interface, carrinho e apresentação dos resultados. |
| `dist/demo-store.js` | Regras de pedidos, pagamento simulado e persistência em IndexedDB. |
| `tests/` | Testes automatizados das regras e da interface. |
| `package.json` e `package-lock.json` | Comando de testes e dependências de desenvolvimento. |

`dist/` contém os arquivos servidos pelo site. Não há etapa de compilação: alterações nesses arquivos constituem a versão a publicar. Os testes usam Node.js; o site publicado usa apenas os recursos do navegador.

## Testes

Com **Node.js 20 ou superior** e npm instalados, execute nesta pasta:

```powershell
npm ci
npm test
```

Se o PowerShell bloquear `npm.ps1`, use `npm.cmd ci` e `npm.cmd test`.

Os testes utilizam `fake-indexeddb` para verificar as regras com um banco em memória e `jsdom` para exercitar a interface em um DOM de teste. Isso permite conferir cálculos, estoque, recuperação e tratamento dos estados de pagamento sem dados reais. A verificação no endereço publicado complementa esses testes.

As evidências Python/SQLite da pasta acadêmica pertencem à implementação local. Seus resultados de carga e concorrência não são métricas desta versão online.

## Publicação

O endereço acima está hospedado no GitHub Pages. O repositório público [raizes-do-nordeste](https://github.com/dmfariaas/raizes-do-nordeste) contém os arquivos da demonstração. A documentação acadêmica continua neste repositório privado.

Para atualizar o site, execute os testes, copie `index.html`, `app.js` e `demo-store.js` de `dist/` para a raiz do repositório público e envie a alteração para a branch `main`. Preserve o arquivo `.nojekyll`. O GitHub Pages publica essa branch automaticamente; uma alteração apenas neste repositório acadêmico não atualiza o endereço público.

Publique o conteúdo de `dist/` em uma hospedagem estática com HTTPS, preservando os nomes dos arquivos. O endereço público deve servir `index.html`, `app.js` e `demo-store.js` no mesmo diretório. O uso de HTTPS permite os recursos de armazenamento e identificação utilizados pela demonstração.

Uma publicação nova não transfere dados de um visitante para outro: cada navegador mantém sua própria demonstração.
