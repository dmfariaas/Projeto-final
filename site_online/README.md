# Raízes do Nordeste — demonstração online

[Abrir o restaurante](https://dmfariaas.github.io/raizes-do-nordeste/)

Esta é a versão do restaurante que pode ser compartilhada por link. Ela abre em computadores, celulares e tablets com um navegador atual, sem instalação de Python. Os arquivos ficam hospedados na web, de modo que o acesso não depende do computador do autor.

## O que pode ser demonstrado

- Escolha das unidades de Recife e João Pessoa e dos cinco canais de atendimento.
- Carrinho, conferência de valores, cupom `RAIZES10` e fidelidade.
- Pagamento aprovado, recusado ou pendente, com resolução da pendência.
- Reenvio de uma solicitação sem duplicar o pedido, a baixa de estoque ou os pontos.
- Recuperação da demonstração ao recarregar a página.

Os pagamentos são fictícios, sem cobrança e sem coleta de dados de cartão.

## Dados da demonstração

O site guarda pedidos, estoque e pontos no IndexedDB do navegador. Cada navegador mantém sua própria demonstração: um pedido feito no computador não aparece no celular. Ao limpar os dados do site, esses registros são apagados. A navegação privada também pode descartá-los no encerramento da sessão.

Para apagar os dados da demonstração e restaurar o estoque inicial, abra **Como os dados são usados** e selecione **Reiniciar demonstração**.

As regras são executadas no navegador. Esta versão permite apresentar o fluxo acadêmico, mas não oferece um servidor de pedidos, contas de clientes ou integração com uma operadora de pagamentos. A implementação local em Python e SQLite está no [pacote acadêmico](../4992220_Projeto_Qualidade_Completo/Projeto_Qualidade_4992220/).

## Arquivos

| Caminho | Responsabilidade |
| --- | --- |
| `dist/index.html` | Estrutura, aparência e conteúdo da página. |
| `dist/app.js` | Interação da interface, carrinho e apresentação dos resultados. |
| `dist/demo-store.js` | Regras de pedidos, pagamento simulado e persistência em IndexedDB. |
| `tests/` | Testes automatizados das regras e da interface. |
| `package.json` e `package-lock.json` | Comando de testes e dependências de desenvolvimento. |

Os arquivos publicados estão em `dist/` e não precisam de compilação. Uma alteração nessa pasta já modifica o material que será enviado à hospedagem. Node.js é necessário para executar os testes. O visitante usa apenas o navegador.

## Testes

Com **Node.js 20 ou superior** e npm instalados, execute nesta pasta:

```powershell
npm ci
npm test
```

Se o PowerShell bloquear `npm.ps1`, use `npm.cmd ci` e `npm.cmd test`.

Os testes usam `fake-indexeddb` como banco em memória e `jsdom` para simular a estrutura da página. Assim, verificam cálculos, estoque, recuperação de pedidos e estados do pagamento sem depender de dados reais. Esse ambiente simulado não substitui a conferência no endereço publicado.

As evidências da pasta acadêmica foram coletadas na implementação Python/SQLite. Os resultados de carga e concorrência ali registrados valem para aquela versão.

## Publicação

O GitHub Pages hospeda o endereço acima a partir do repositório público [raizes-do-nordeste](https://github.com/dmfariaas/raizes-do-nordeste), que contém os arquivos da demonstração. A documentação acadêmica permanece neste repositório privado.

Para atualizar o site:

1. Execute os testes desta pasta.
2. Copie `index.html`, `app.js` e `demo-store.js` de `dist/` para a raiz do repositório público.
3. Preserve o arquivo `.nojekyll` e envie a alteração para a branch `main`.

O GitHub Pages publica essa branch automaticamente. Alterar somente o repositório acadêmico não atualiza o site público.

Se for utilizada outra hospedagem estática, publique o conteúdo de `dist/` com HTTPS e mantenha `index.html`, `app.js` e `demo-store.js` no mesmo diretório, com esses nomes. A conexão segura é necessária para os recursos de identificação usados pela demonstração.

Os dados dos visitantes não fazem parte da publicação: cada navegador conserva seus próprios registros.
