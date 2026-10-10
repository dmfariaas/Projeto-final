# Projeto de Qualidade de Software

Diego Monteiro de Farias · RU 4992220

Revisão editorial de 10 de outubro de 2026. As evidências de execução são de 24 de setembro de 2026.

Para entregar o trabalho no AVA, use o PDF único. Para experimentar a versão local do restaurante, abra `INICIAR_DEMONSTRACAO.cmd`. O arquivo avulso `ABRIR_RESTAURANTE_NORDESTINO.cmd` também inicia essa versão.

A [demonstração online](https://dmfariaas.github.io/raizes-do-nordeste/) pode ser aberta diretamente no navegador. Ela guarda os dados no próprio navegador e simula os pagamentos. As instruções de execução e as evidências deste pacote se referem à versão local, em Python e SQLite.

## O que está incluído

- `output/4992220_Projeto_Qualidade.pdf`: relatório principal com requisitos, arquitetura, plano de qualidade, cenários de teste, métricas, rastreabilidade, resultados e referências.
- `output/4992220_Projeto_Qualidade.md`: o mesmo conteúdo em texto editável.
- `output/4992220_Metricas_Qualidade.xlsx`: planilha com fórmulas, resultados individuais dos testes e duzentas amostras de carga.
- `prototipo/`: demonstração local em Python e HTML, sem cobrança.
- `evidencias/`: registros dos testes e capturas do navegador.

O iniciador foi verificado em três execuções isoladas. Nessas verificações, o pedido continuou disponível entre as aberturas, conforme o registro em `evidencias/inicializador.json`.

O relatório distingue os testes executados das avaliações que ainda dependem de coleta ou da participação de usuários. Antes da submissão, confira os requisitos acadêmicos e os critérios de entrega do roteiro.

## Apresentação acadêmica

A organização do relatório segue as normas ABNT aplicáveis à atividade: NBR 14724:2024 (apresentação), NBR 6023:2025 (referências), NBR 10520:2023 (citações), NBR 6024:2012 (seções), NBR 6027:2012 (sumário) e NBR 6028:2021 (resumos).

O PDF reúne capa, folha de rosto, resumo, abstract, sumário e as cinco entregas do roteiro, além de introdução, conclusão e referências. O texto usa papel A4, fonte Arial 12 e espaçamento 1,5. As margens superior e esquerda têm 3 cm, enquanto a inferior e a direita têm 2 cm. As indicações de fonte das figuras e o conteúdo dos quadros usam tamanho menor e espaçamento simples. A contagem das páginas começa na folha de rosto, mas a numeração só aparece na introdução, no canto superior direito.

A capa e a folha de rosto trazem o nome Diego Monteiro de Farias, o RU 4992220, o curso de Análise e Desenvolvimento de Sistemas e o local Porto, Portugal. O arquivo Markdown serve para editar o texto. A diagramação da entrega está no PDF.

Referências para a formatação: [guia da Biblioteca Universitária da UFSC, atualizado para a NBR 14724:2024](https://repositorio.ufsc.br/bitstream/handle/123456789/180829/Trabalhos%20Academicos_A4_24-03-2025.pdf?isAllowed=y&sequence=8), [NBR 6023:2025 disponibilizada pela FHO](https://www.fho.edu.br/assets/documentos/FHO_Biblioteca_Referencia_ABNT_6023_2025.pdf) e [guia de citações da UFC conforme a NBR 10520:2023](https://biblioteca.ufc.br/wp-content/uploads/2025/06/guianormalizacaocitacoes2025.pdf).

## Identidade visual

A interface usa tons de areia, barro e verde-mandacaru, com ilustrações inspiradas em xilogravura. O cardápio e os textos de atendimento seguem a proposta de uma casa de comida nordestina. As ilustrações fazem parte dos arquivos do projeto. Os testes da interface verificam a montagem do pedido, as mensagens, a recuperação da compra e a adaptação a telas menores.

## Como experimentar

1. Extraia o ZIP para acessar todos os documentos. Se quiser apenas usar a demonstração, baixe e execute `INICIAR_DEMONSTRACAO.cmd`, que inclui os arquivos necessários.
2. No Windows, abra `INICIAR_DEMONSTRACAO.cmd`. O iniciador verifica Python 3.11 ou superior, inicia o servidor local na porta 8765 e abre o navegador. Se a demonstração já estiver em execução nessa porta, ele abre o servidor existente.
3. Se o navegador não abrir, acesse `http://127.0.0.1:8765/`. Mantenha o servidor aberto enquanto usa a demonstração. Depois de reiniciar o computador, abra o iniciador novamente.
4. Adicione dois baiões de dois e um suco de cajá. Aplique o cupom `RAIZES10` e, se desejar, marque a fidelidade. O total esperado é R$ 52,20. Com o pagamento aprovado e a fidelidade selecionada, são concedidos 52 pontos.
5. No seletor de pagamento, experimente aprovação, recusa ou ausência de resposta.
6. A ausência de resposta deixa o pedido pendente. Para concluí-lo, use os controles de aprovação ou recusa simulada. Antes de aprovar, o serviço confere o estoque novamente. Os pontos só são concedidos quando a fidelidade foi selecionada.
7. Recarregue a mesma aba para conferir se o rascunho ou o resultado foi recuperado. Após concluir a compra, use a opção de novo pedido para começar outra.
8. Para encerrar o servidor, pressione **Ctrl+C** na janela em que ele está em execução.

Os preços, as identidades e os controles de sessão são demonstrativos. Não use dados pessoais, cartões ou informações de uma empresa real nos testes.

### Quando algo interromper a compra

- **Cardápio não carregou:** use a opção de tentar novamente. A compra fica bloqueada enquanto o catálogo da unidade escolhida não estiver disponível.
- **Envio sem resposta:** após oito segundos, a interface permite tentar novamente com a mesma solicitação. Como o servidor pode já ter processado o pedido, o reenvio recupera o resultado existente sem criar outra compra.
- **Página recarregada:** o carrinho, o resultado e a solicitação que ainda não recebeu resposta ficam na sessão da aba. Mantenha a mesma aba e o mesmo endereço, incluindo a porta. Fechar a aba, limpar os dados do navegador ou abrir outro endereço pode impedir essa recuperação.
- **Sessão expirada:** use a opção de atualizar a sessão. A tentativa permanece guardada para ser concluída após a recarga, com o mesmo conteúdo e a mesma chave.
- **Pendência sem estoque:** a tentativa de aprovação é recusada, sem baixar parte do estoque nem conceder pontos. O pedido permanece pendente e ainda pode receber uma recusa simulada.
- **Pedido pendente de uma versão antiga:** se faltarem os itens necessários à conferência, a aprovação fica bloqueada. A recusa continua disponível. Para experimentar a versão atual, crie outro pedido.

O banco mantém os pedidos entre as aberturas do servidor. A recuperação da tela, por sua vez, depende da sessão do navegador. Os cinco canais são opções do mesmo protótipo, sem aplicativos separados ou um fluxo operacional completo de retirada.

Se o iniciador informar que não encontrou Python, instale Python 3.11 ou superior. Também é possível abrir um terminal na pasta `prototipo` e executar:

```text
python api.py
```

O iniciador e o comando `python api.py` usam a porta 8765 por padrão. Se outro programa estiver usando essa porta, o iniciador informa o conflito. Para escolher outra, execute `INICIAR_DEMONSTRACAO.cmd --port 8766` e use o endereço mostrado na janela. A opção `--port 0` permite escolher uma porta livre automaticamente.

Quando executado sozinho, o iniciador prepara os arquivos em `%LOCALAPPDATA%\ProjetoQualidade4992220` e guarda o banco em `dados/demo.sqlite3`. No pacote completo, ele usa a pasta `prototipo` que o acompanha. A atualização dos arquivos de execução preserva o banco da demonstração.

## Como repetir os testes

Na pasta `prototipo`, execute:

```text
python run_evidence.py
```

O comando executa os testes de regras, sistema, API, segurança, concorrência, regressão e resolução de pendências. Depois, realiza um ensaio de carga com 200 pedidos. Os bancos usados nos testes são temporários e isolados.

Os novos relatórios, com os totais da execução, são gravados em `evidencias`. Antes de rodar o comando, copie os registros anteriores se quiser conservá-los. A execução inicial que demonstrou D01 já foi preservada com nome próprio.

Falhas em subtestes ou no ensaio de carga ficam registradas e fazem o comando terminar com erro. Os testes RG01–RG04 provocam falhas controladas para verificar esse tratamento. Quando são aprovados, confirmam que as falhas foram detectadas como esperado.

Para repetir os testes de interface, é necessário ter Node.js 20 ou superior, npm e Google Chrome. Na raiz do pacote, instale o Playwright e execute:

```text
npm install --no-save playwright
node qa_interface.mjs
```

A automação usa um navegador temporário, sem acesso ao perfil pessoal do usuário. O script abre seu próprio servidor em uma porta livre e cria um banco temporário. Ao terminar, encerra o servidor e remove esse banco. Você não precisa abrir a demonstração antes: o estoque usado manualmente permanece intacto.

## Correções da versão local

- Pedidos pendentes podem receber aprovação ou recusa simulada. O serviço confere o estoque antes de confirmar e aplica estoque, pontos e evento de mudança uma única vez.
- A mesma aba recupera o carrinho, o resultado e a solicitação ainda sem resposta após uma recarga.
- Uma sessão expirada pode ser atualizada sem descartar a tentativa em andamento.
- Requisições sem resposta têm limite de oito segundos. A tentativa seguinte conserva o conteúdo e a chave para evitar duplicação.
- A falha no carregamento do cardápio tem opção de nova tentativa. A troca de unidade não permite comprar com o catálogo anterior.
- Os botões de quantidade mantêm o mínimo de zero e respeitam o estoque disponível e o limite de dez unidades por produto.
- A confirmação da compra permanece visível se houver falha ao atualizar o cardápio. Um aviso informa que o estoque exibido não foi atualizado.
- A planilha diferencia campos vazios de resultados iguais a zero e identifica entradas inválidas. A disponibilidade é calculada sobre todas as verificações previstas no mês.
- Cabeçalhos de sessão inválidos recebem uma resposta de erro sem interromper a conexão.
- O pedido fica protegido contra alterações durante o envio. Após perda da resposta, a nova tentativa reutiliza o mesmo conteúdo e a mesma chave.
- O coletor registra falhas em subtestes e na limpeza e informa erro quando a carga falha.
- O iniciador inclui os arquivos da demonstração, funciona quando baixado sozinho e usa a porta 8765 por padrão. Suas mensagens orientam a correção de problemas com a versão do Python, a porta ou o acesso ao banco.

Os resultados registrados estão em `evidencias/testes.json` e `evidencias/interface.json`. O arquivo `evidencias/correcoes_execucao.json` relaciona cada correção aos testes correspondentes. A medição do tempo de correção de D01 mantém o fechamento original.

## Como revisar a entrega

Envie ao AVA o arquivo único `4992220_Projeto_Qualidade.PDF`. Ele reúne o Documento de Requisitos, o Plano de Qualidade, o Plano de Testes, a Planilha de Métricas e o Relatório Final de Conformidade. O código, a planilha editável e o ZIP são materiais de apoio. As métricas e as evidências essenciais já constam no PDF.

- Leia e compreenda os oito requisitos funcionais e os oito requisitos de qualidade.
- Repita compra aprovada, recusa, resolução de pendência, cupom inválido e recuperação após recarga. Confira também a repetição segura quando a resposta é perdida.
- Registre alterações e novas execuções.
- Confira o nome do curso, a disciplina e os demais dados de capa exigidos pelo seu polo.
- Confirme a presença dos cinco componentes no PDF e o nome exigido para o arquivo.
- Execute o protocolo humano antes de preencher satisfação, sucesso de uso ou aceite. Não marque como realizado um teste apenas planejado.
- Preencha as entradas amarelas da planilha apenas com dados coletados. Disponibilidade e satisfação começam vazias e aparecem como **Não medido**. Atualize o relatório quando houver uma nova medição.
- Ao apresentar a cobertura de 100%, explique que os oito requisitos funcionais têm testes associados. O indicador não mede a cobertura de código, não abrange todas as regras e não comprova ausência de defeitos.

## Limitações técnicas principais

A demonstração não inclui autenticação de clientes reais, integração com provedor de pagamento, aplicação nativa, conciliação automática com operadora ou reserva distribuída de estoque. Também não foram realizados monitoramento mensal, pesquisa com usuários ou auditoria completa de segurança.

A resolução de pendências depende da escolha feita no simulador. A recuperação após recarga funciona na mesma aba e no mesmo endereço. Não existe uma conta de cliente que sincronize compras entre dispositivos. Os testes de concorrência deste pacote se limitam ao SQLite local.

Para reiniciar o estoque da demonstração, pare o servidor e remova somente `prototipo/demo.sqlite3` e seus eventuais arquivos auxiliares de mesmo prefixo. Se estiver usando o iniciador sozinho, o banco está em `%LOCALAPPDATA%\ProjetoQualidade4992220\dados\demo.sqlite3`. Não é necessário remover o banco para rodar os testes.
