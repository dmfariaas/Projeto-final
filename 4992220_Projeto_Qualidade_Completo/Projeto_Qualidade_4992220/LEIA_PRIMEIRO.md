# Projeto de Qualidade de Software

Diego Monteiro de Farias · RU 4992220

Revisão 0.4, de 24 de setembro de 2026. Para entregar no AVA, use o PDF único. Para experimentar o restaurante, abra `INICIAR_DEMONSTRACAO.cmd`. O arquivo avulso `ABRIR_RESTAURANTE_NORDESTINO.cmd` abre a mesma demonstração.

## O que está incluído

- `output/4992220_Projeto_Qualidade.pdf`: relatório principal com requisitos, arquitetura, plano de QA, cenários, métricas, rastreabilidade, resultados e referências.
- `output/4992220_Projeto_Qualidade.md`: o mesmo conteúdo em texto editável.
- `output/4992220_Metricas_Qualidade.xlsx`: planilha com fórmulas, resultados individuais dos testes e duzentas amostras de carga.
- `prototipo/`: demonstração local em Python e HTML, sem cobrança.
- `evidencias/`: registros dos testes e capturas do navegador.

O iniciador também foi verificado em três execuções isoladas, com persistência do pedido entre aberturas. O registro está em `evidencias/inicializador.json`.

O relatório apresenta os testes executados e as validações que ainda dependem de coleta ou participação humana. Confira os requisitos acadêmicos e os critérios de entrega antes da submissão.

## Apresentação acadêmica

O relatório foi organizado conforme as normas ABNT aplicáveis à atividade: NBR 14724:2024 (apresentação), NBR 6023:2025 (referências), NBR 10520:2023 (citações), NBR 6024:2012 (seções), NBR 6027:2012 (sumário) e NBR 6028:2021 (resumos).

O PDF contém capa, folha de rosto, resumo, abstract, sumário e as cinco entregas do roteiro, além de introdução, conclusão e referências. Foram adotados papel A4, margens superior/esquerda de 3 cm e inferior/direita de 2 cm, Arial 12 e espaçamento 1,5 no texto. Fontes de figuras e conteúdo de quadros usam tamanho menor e espaçamento simples. As páginas são contadas a partir da folha de rosto; os números aparecem no canto superior direito a partir da introdução.

A capa e a folha de rosto identificam Diego Monteiro de Farias, RU 4992220, curso de Análise e Desenvolvimento de Sistemas e local Porto, Portugal. A versão em Markdown permite revisar o texto, mas não conserva a diagramação do PDF.

Referências para a formatação: [guia da Biblioteca Universitária da UFSC, atualizado para a NBR 14724:2024](https://repositorio.ufsc.br/bitstream/handle/123456789/180829/Trabalhos%20Academicos_A4_24-03-2025.pdf?isAllowed=y&sequence=8), [NBR 6023:2025 disponibilizada pela FHO](https://www.fho.edu.br/assets/documentos/FHO_Biblioteca_Referencia_ABNT_6023_2025.pdf) e [guia de citações da UFC conforme a NBR 10520:2023](https://biblioteca.ufc.br/wp-content/uploads/2025/06/guianormalizacaocitacoes2025.pdf).

## Identidade visual

A página recebeu cores de areia, barro e verde-mandacaru, ilustrações inspiradas em xilogravura e textos que valorizam a cozinha nordestina. As ilustrações estão incluídas no próprio projeto. Os testes da interface verificam a montagem do pedido, as mensagens, a recuperação da compra e o uso em telas menores.

## Como experimentar

1. Para acessar todos os documentos, extraia o ZIP. Para abrir apenas a demonstração, você também pode baixar e executar somente `INICIAR_DEMONSTRACAO.cmd`; ele já inclui os arquivos necessários.
2. No Windows, abra `INICIAR_DEMONSTRACAO.cmd`. O iniciador verifica Python 3.11 ou superior, escolhe uma porta livre, inicia o servidor local e abre o navegador.
3. Se o navegador não abrir automaticamente, copie o endereço mostrado na janela, começando por `http://127.0.0.1:`.
4. Adicione dois baiões e um suco. Aplique RAIZES10 e, se desejar, marque fidelidade. O total esperado é R$ 52,20 e, em aprovação com fidelidade, 52 pontos.
5. Use o seletor da demonstração para experimentar aprovação, recusa ou ausência de resposta.
6. Se escolher ausência de resposta, o pedido ficará pendente. Use os controles de aprovação ou recusa simulada para concluir esse mesmo pedido. A aprovação confere o estoque novamente e concede pontos somente quando a fidelidade foi selecionada.
7. Recarregue a página na mesma aba para conferir a retomada do rascunho ou do resultado. Depois de concluir a compra, use a opção de novo pedido para começar outra.
8. Para encerrar o servidor, pressione Ctrl+C na janela em que ele está executando.

Não preencha dados pessoais, cartões ou informações de uma empresa real. Todos os preços e identidades deste recorte são fictícios. Os controles de sessão são apenas demonstrativos.

### Quando algo interromper a compra

- **Cardápio não carregou:** use a opção de tentar novamente. A compra fica bloqueada enquanto o catálogo da unidade escolhida não estiver disponível.
- **Envio sem resposta:** após oito segundos, a interface libera uma tentativa com a mesma solicitação. O pedido pode ter sido processado pelo servidor; o reenvio recupera o resultado sem criar outra compra.
- **Página recarregada:** carrinho, resultado e solicitação ainda sem resposta são guardados na sessão da aba. Mantenha a mesma aba e o mesmo endereço, incluindo a porta. Fechar a aba, limpar os dados do navegador ou abrir outro endereço pode encerrar essa retomada.
- **Sessão expirada:** use a opção de atualizar a sessão. A tentativa permanece guardada para ser concluída após a recarga, com o mesmo conteúdo e a mesma chave.
- **Pendência sem estoque:** a aprovação é recusada sem alterar parcialmente o estoque ou conceder pontos. O pedido continua pendente e pode receber uma recusa simulada.
- **Pedido pendente de uma versão antiga:** se ele não contém os itens necessários à conferência, a aprovação é bloqueada. A recusa continua disponível; crie outro pedido para repetir a demonstração atual.

O banco preserva os pedidos entre aberturas do servidor. Já a recuperação da tela depende da sessão do navegador. Os cinco canais são opções do mesmo protótipo; não há aplicativos separados nem um fluxo operacional completo de retirada.

Se o iniciador informar que não encontrou Python, instale Python 3.11 ou superior. Também é possível abrir um terminal na pasta `prototipo` e executar:

```text
python api.py
```

O iniciador escolhe uma porta livre automaticamente. Para usar uma porta específica, execute `INICIAR_DEMONSTRACAO.cmd --port 8766`. Ao iniciar diretamente com `python api.py`, a porta padrão continua sendo 8765.

Quando o iniciador é aberto sozinho, prepara os arquivos em `%LOCALAPPDATA%\ProjetoQualidade4992220` e guarda o banco em `dados/demo.sqlite3`. Ao abrir o pacote completo, usa a pasta `prototipo` que acompanha o iniciador. As atualizações dos arquivos de execução preservam o banco da demonstração.

## Como repetir os testes

Na pasta `prototipo`, execute:

```text
python run_evidence.py
```

A suíte cobre regras, sistema, API, segurança, concorrência, regressão e resolução de pendências, seguida de uma carga de 200 pedidos. Os bancos dos testes são temporários e isolados. A pasta `evidencias` recebe os novos relatórios, incluindo os totais da execução. Copie as evidências anteriores se desejar preservar outra versão. A execução inicial que demonstrou D01 já está preservada com nome próprio. Falhas em subtestes e na carga são registradas e fazem a execução terminar com erro. As regressões RG01–RG04 provocam erros controlados para conferir esse tratamento; o resultado aprovado indica que foram detectados corretamente.

Para repetir os testes de interface, é necessário Node.js, Playwright e Google Chrome. Na raiz do pacote:

```text
npm install --no-save playwright
node qa_interface.mjs
```

O navegador usado pela automação é temporário e não acessa o perfil pessoal do usuário. O script inicia seu próprio servidor em uma porta livre e usa um banco temporário. Ao terminar, encerra o servidor e remove esse banco. Não é necessário abrir a demonstração antes; o estoque de uso manual não é alterado.

## Correções desta revisão

- Pedidos pendentes podem receber aprovação ou recusa simulada. O serviço confere o estoque antes de confirmar e aplica estoque, pontos e evento de mudança uma única vez.
- A mesma aba recupera o carrinho, o resultado e a solicitação ainda sem resposta após uma recarga.
- Uma sessão expirada pode ser atualizada sem descartar a tentativa em andamento.
- Requisições sem resposta têm limite de oito segundos. A tentativa seguinte conserva o conteúdo e a chave para evitar duplicação.
- A falha no carregamento do cardápio tem opção de nova tentativa. A troca de unidade não permite comprar com o catálogo anterior.
- Os botões de quantidade respeitam zero, o estoque disponível e o limite de dez por produto.
- A confirmação da compra permanece visível se houver falha ao atualizar o cardápio. Um aviso informa que o estoque exibido não foi atualizado.
- A planilha diferencia campos vazios de resultados iguais a zero e identifica entradas inválidas. A disponibilidade é calculada sobre todas as verificações previstas no mês.
- Cabeçalhos de sessão inválidos recebem uma resposta de erro sem interromper a conexão.
- O pedido fica protegido contra alterações durante o envio. Após perda da resposta, a nova tentativa reutiliza o mesmo conteúdo e a mesma chave.
- O coletor registra falhas em subtestes e na limpeza e informa erro quando a carga falha.
- O iniciador inclui os arquivos da demonstração, funciona quando baixado sozinho e escolhe uma porta livre. Também orienta erros de Python incompatível e de acesso ao banco.

Os resultados atuais estão em `evidencias/testes.json` e `evidencias/interface.json`; `evidencias/correcoes_execucao.json` relaciona as correções aos testes. A medição do tempo de correção de D01 conserva seu fechamento original.

## Como revisar a entrega

O arquivo a enviar no AVA é o PDF único `4992220_Projeto_Qualidade.PDF`. Ele reúne Documento de Requisitos, Plano de Qualidade, Plano de Testes, Planilha de Métricas e Relatório Final de Conformidade. Os arquivos de código, a planilha editável e o ZIP são materiais de apoio; as métricas e as evidências essenciais já estão no PDF. Confira os dados de identificação antes da submissão.

- Leia e compreenda os oito requisitos funcionais e os oito requisitos de qualidade.
- Repita compra aprovada, recusa, resolução de pendência, cupom inválido e recuperação após recarga. Confira também a repetição segura quando a resposta é perdida.
- Registre alterações e novas execuções.
- Confira o nome do curso, a disciplina e os demais dados de capa exigidos pelo seu polo.
- Confira os cinco componentes no PDF único e o nome exigido para o arquivo. O protótipo e os registros detalhados são materiais de apoio à reprodução local.
- Execute o protocolo humano antes de preencher satisfação, sucesso de uso ou aceite. Não marque como realizado um teste apenas planejado.
- A planilha tem entradas amarelas. Disponibilidade e satisfação começam vazias e aparecem como Não medido. Atualize o relatório após uma nova medição.
- A cobertura de 100% é de presença de testes para os oito requisitos funcionais. Não representa 100% de código, de regras ou ausência de defeitos.

## Limitações técnicas principais

Não há autenticação comercial, gateway real, aplicação nativa, conciliação automática com operadora, reserva distribuída, monitoramento mensal, pesquisa humana ou auditoria completa de segurança. A resolução de pendências depende de uma escolha explícita no simulador. A recuperação após recarga vale para a sessão da mesma aba e endereço; ela não é uma conta de cliente nem sincroniza compras entre dispositivos. A prova de concorrência é limitada ao SQLite local.

Para reiniciar o estoque da demonstração, pare o servidor e remova somente `prototipo/demo.sqlite3` e seus eventuais arquivos auxiliares de mesmo prefixo. Se estiver usando o iniciador sozinho, o banco está em `%LOCALAPPDATA%\ProjetoQualidade4992220\dados\demo.sqlite3`. Não é necessário remover o banco para rodar os testes.
