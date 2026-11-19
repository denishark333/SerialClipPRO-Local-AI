# Serial ClipPRO

**Sua live continua em cada corte.**

Lives longas, pouco tempo para editar? O Serial ClipPRO analisa suas VODs e prepara cortes verticais enquanto você está longe do PC. Depois, você revisa e escolhe o que publicar.

Este repositório reúne o código-fonte, os pacotes de instalação e as versões públicas do aplicativo para Windows.

## Download

Acesse **Releases**, neste repositório, e baixe o instalador anexado à versão desejada (`Serial-ClipPRO-2.0.0-Setup-x64.exe` na versão 2.0).

> Baixe o instalador **Serial ClipPRO**. Os arquivos automáticos “Source code (zip)” e “Source code (tar.gz)” contêm o código-fonte, não o aplicativo pronto.

## O que o aplicativo faz

- Processa VODs de Twitch, YouTube e Kick, além de vídeos locais.
- Seleciona momentos por picos de áudio, contexto ou modo híbrido.
- Gera cortes verticais em formato 9:16 com legendas.
- Permite ajustar o enquadramento da webcam e incluir a marca do seu canal em PNG.
- Oferece uma galeria para revisar, baixar, exportar e excluir cortes.
- Permite revisar e corrigir as legendas de cada corte.
- Reúne atalhos para acessar as plataformas e publicar manualmente.

A IA auxilia na seleção. Revise os cortes e as legendas antes de publicar.

## Instalação e primeiro uso

1. Baixe o instalador em **Releases**.
2. Execute o instalador. Ele cria os atalhos e prepara automaticamente os componentes e modelos.
3. Se aparecer a janela inicial do **Ollama**, prossiga com o **uso local**. Não é necessário usar modelos cloud.
4. Aguarde a preparação terminar. Os modelos são baixados nessa etapa.
5. Ao final, abra o Serial ClipPRO pelo instalador ou pelo atalho criado.

Nos próximos usos, basta abrir o atalho **Serial ClipPRO**.

### Durante a preparação

- É necessária conexão com a internet.
- Os modelos exigem downloads de vários GB e espaço disponível em disco.
- O Windows pode solicitar permissão para instalar componentes.
- Em falhas de rede, tente novamente no instalador ou use **Preparar ou reparar Serial ClipPRO** no menu Iniciar.
- Se houver solicitação de reinício, reinicie o computador e use esse mesmo atalho para concluir.
- A preparação do Whisper pode levar alguns minutos.

Python e Node.js não precisam estar instalados no computador de destino.

## Primeiro teste

Comece com um vídeo curto antes de processar uma VOD longa:

1. Informe uma URL compatível ou selecione um arquivo local.
2. Escolha o modo de análise.
3. Ajuste o enquadramento e a marca, se desejar.
4. Inicie o processamento.
5. Revise os vídeos na galeria e exporte seus favoritos.

Mantenha o computador ligado e sem entrar em suspensão durante o processamento.

## Modos de análise

| Modo | Como funciona |
|---|---|
| **Picos de áudio** | Busca candidatos a partir da intensidade sonora e analisa os trechos selecionados. |
| **Híbrido** | Combina picos de áudio com amostras distribuídas ao longo do conteúdo. |
| **Contexto completo** | Transcreve e analisa toda a fonte, exigindo mais tempo de processamento. |

Nenhum modo garante encontrar todos os momentos interessantes. O tempo varia conforme a duração da VOD, a conexão, o hardware e as configurações escolhidas.

## Processamento local e hardware

A transcrição e a análise por IA utilizam **Whisper e Ollama no computador**.

- O Whisper usa CPU por compatibilidade.
- A renderização tenta utilizar NVENC em GPUs NVIDIA compatíveis.
- Quando NVENC não está disponível, a renderização utiliza CPU.

O processamento local não elimina a necessidade de internet para baixar modelos, acessar VODs e abrir as plataformas sociais.

## Onde ficam os arquivos?

O programa fica em `%LOCALAPPDATA%\Programs\Serial ClipPRO\`. Os dados ficam separados, em:

`%LOCALAPPDATA%\Serial ClipPRO\`

Cole esse caminho na barra de endereços do Explorador de Arquivos.

| Pasta | Conteúdo |
|---|---|
| `Cortes_Prontos` | Vídeos disponíveis na galeria. |
| `Cortes_Exportados` | Cópias dos cortes exportados em lote. |
| `transcricoes` | Cache de transcrições. |
| `relatorios_curadoria` | Relatórios da análise. |
| `cache_revisao` | Bases para revisar legendas dos cortes. |
| `marca` | Imagem e configuração da marca do canal. |
| `logs` | Registros de diagnóstico. |

Excluir um corte da galeria não apaga as cópias já exportadas. O botão **Descarregar** permite escolher onde salvar um vídeo individual.

## Redes sociais

A aba Social reúne atalhos para Instagram, TikTok, YouTube, Twitch e Kick. BiliBili aparece como **Em breve**.

Login e publicação são feitos manualmente nos sites das plataformas. O aplicativo não publica automaticamente.

Se uma plataforma recusar o login na janela integrada, utilize **Abrir no navegador**.

## Atualização

1. Aguarde o processamento terminar e feche o aplicativo.
2. Baixe o instalador da nova versão em **Releases**.
3. Execute o instalador.

Atualizações e desinstalação preservam vídeos, configurações e modelos. Consulte as notas da Release para eventuais instruções específicas.

## Problemas e sugestões

O projeto está em desenvolvimento. Para relatar um problema, abra uma **Issue** neste repositório e informe:

- Versão do Serial ClipPRO.
- Versão do Windows, processador, memória RAM e GPU.
- Origem do vídeo e modo de análise utilizado.
- Etapa em que ocorreu o problema.
- Mensagem de erro e, se possível, uma captura de tela.

Para problemas de instalação, consulte:

`%LOCALAPPDATA%\Serial ClipPRO\instalacao.log`

Revise os logs antes de publicá-los e remova informações pessoais, tokens ou URLs privadas.

## Apoie o projeto

Se o Serial ClipPRO ajudar na sua rotina, você pode contribuir com seu desenvolvimento:

- [Apoiar via Pix — LivePix](https://livepix.gg/serialhealer)
- [Apoiar via PayPal](https://www.paypal.com/donate/?business=6KXEQHVYHLLQ8&no_recurring=0&item_name=Host%2FVPS&currency_code=BRL)

O apoio é voluntário.

---

# Desenvolvimento

Aplicação local para transformar arquivos e VODs de Twitch, YouTube e Kick em cortes verticais. Interface React, API FastAPI, yt-dlp, FFmpeg, faster-whisper e Ollama.

## Uso pelo código

Requer Python e Node para desenvolvimento; FFmpeg/ffprobe no PATH e Ollama com `llama3.1` para processamento.

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
venv\Scripts\python.exe main.py
```

Abra http://127.0.0.1:8765. Para desenvolvimento com atualização automática, mantenha o backend ligado e execute `npm run dev` em `frontend`; acesse a URL indicada pelo Vite. Em **Arquivo**, clique em **Selecionar vídeo** para abrir o seletor do Windows (também no modo navegador local); o vídeo é usado diretamente, sem upload ou cópia. Em **Link**, cole a URL no campo digitável.

Fechar a aba do navegador não encerra o servidor. Para encerrar, pressione **Ctrl+C no terminal que executou `main.py`** e aguarde o retorno do prompt antes de iniciar novamente. O encerramento solicita cancelamento do pipeline e aguarda as tarefas terminarem; chamadas de modelos podem demorar a responder. Se a porta estiver ocupada, a inicialização informa o conflito sem abrir outra aba. No desktop, feche a janela após terminar/cancelar o processamento; revisões e previews também bloqueiam o fechamento enquanto estão ativos. Encerramento forçado pelo Gerenciador de Tarefas não garante a limpeza de subprocessos ou temporários.

## Instalador 2.0 — Windows x64

A distribuição 2.0 usa um único `Serial-ClipPRO-2.0.0-Setup-x64.exe`. O instalador cria os atalhos e executa a preparação dos componentes e modelos automaticamente; não é necessário executar um BAT separado. Os modelos são baixados durante a preparação, exigindo internet e espaço para vários GB. Python e Node não são necessários no computador de destino.

O programa fica em `%LOCALAPPDATA%/Programs/Serial ClipPRO/`, separado dos dados em `%LOCALAPPDATA%/Serial ClipPRO/`. Atualizações e desinstalação preservam vídeos, configurações e modelos. Feche o aplicativo após terminar/cancelar as operações antes de atualizar.

Para compilar, prepare um ambiente Python estável x64 chamado `build-env`, instale `requirements-build.lock.txt`, instale Inno Setup e execute `scripts/build_installer.ps1`. O resultado e seu SHA256 ficam em `dist/installer/`. Veja [compilação, retomada e validação](docs/INSTALADOR_V2.md). O fluxo ainda requer validação completa em Windows limpo antes de distribuição pública.

## Desktop WebView2 e distribuição anterior (pasta/ZIP)

Para preparar o ambiente de build:

```powershell
venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
powershell -ExecutionPolicy Bypass -File scripts\build_desktop.ps1
```

Distribua **a pasta inteira `dist/Serial ClipPRO/`**, incluindo `_internal`, o executável e os scripts de preparação. Não copie somente o EXE. O build usa React compilado e uma janela pywebview/WebView2; o servidor permanece em localhost, em uma porta disponível.

No outro computador Windows x64:

1. Extraia a pasta inteira e execute `Instalar dependencias.bat`. Ele verifica .NET Framework, Visual C++, FFmpeg/ffprobe, WebView2 e Ollama, baixando o que faltar diretamente dos fornecedores. **Não depende de winget, Python, Node ou comandos manuais.** Requer internet e espaço para vários GB de modelos; aceite as solicitações legítimas dos instaladores do Windows.
2. Aguarde as sete etapas: a preparação baixa/verifica `llama3.1` e Whisper Small, testa o runtime e abre o aplicativo ao concluir. Nas próximas vezes, basta `Serial ClipPRO.exe`. Executáveis antigos mantêm o modelo daquela versão até uma nova compilação.
3. Se o Windows solicitar reinicialização, reinicie e clique novamente no mesmo BAT para concluir. Em falhas de rede, repita o BAT; não é necessário corrigir comandos no terminal.
4. Na aba Primeiros Passos, use **Verificar dependências**. O FFmpeg instalado pelo pacote fica na pasta de dados do usuário e é encontrado automaticamente, sem alterar o PATH global.
5. Comece com um vídeo curto, depois teste uma VOD longa. Teste em máquina sem NVIDIA para validar a alternativa em CPU.

A preparação é iniciada pelo BAT e abre a aplicação no final; abrir somente o EXE não instala pré-requisitos. O instalador verifica assinaturas dos instaladores Microsoft/Ollama e SHA256 do pacote FFmpeg. Remove a marca de origem de download somente dos binários da distribuição para permitir o carregamento das DLLs .NET. Não altera exclusões nem desativa o Defender. Registra diagnóstico em `instalacao.log`, `self-test.json` e `models-setup.json` na pasta de dados.

O fluxo atualizado ainda precisa ser revalidado em Windows limpo. Uma detecção do Defender na linha de comando de desenvolvimento não equivale à detecção de um arquivo do pacote; não restaure nem exclua itens da proteção para contornar alertas. O build atual usa o Python do ambiente local; para distribuição definitiva, recrie o ambiente com uma versão estável de Python (o ambiente de origem estava em 3.11.0b4).

O desktop bloqueia fechamento enquanto o pipeline estiver ativo: cancele e aguarde antes de fechar. Uma segunda instância desktop usando a mesma pasta de dados é recusada. Evite executar simultaneamente Gradio, servidor manual e desktop sobre os mesmos dados.

Dados do EXE: `%LOCALAPPDATA%/Serial ClipPRO/`. No desenvolvimento, os dados continuam na raiz do projeto. `CLIPPRO_DATA_DIR` permite escolher outro diretório. Recursos empacotados ficam separados dos vídeos, logos e presets. Não há migração automática de dados de builds antigos; copie-os explicitamente se necessário.

## Modos e custo

- **Picos:** varre o áudio, seleciona até 50 candidatos espaçados e transcreve/avalia somente esses trechos. Não procura conversas fora dos candidatos sonoros.
- **Híbrido:** varre o áudio e combina picos com cobertura temporal. Até 40 amostras de 90 segundos por padrão (60 minutos de áudio para transcrição). Pode perder acontecimentos fora das amostras. O limite de amostras é diferente do limite de cortes gerados.
- **Contexto completo:** prepara e transcreve toda a fonte em blocos; custa mais CPU e leitura de mídia. O cache beneficia apenas novas análises da mesma entrada/configuração.

A varredura de Picos/Híbrido percorre toda a fonte, mesmo sem salvar a VOD integral. Em fontes com áudio/vídeo juntos, tráfego de rede pode continuar elevado. Não há garantia de processamento em 15–30 minutos.

Whisper usa CPU/int8 por compatibilidade. A renderização final e a revisão de legendas tentam NVIDIA NVENC, depois AMD AMF (`h264_amf`) e, se ambos falharem, CPU com libx264. AMF requer GPU AMD com codificação H.264, driver compatível e FFmpeg compilado com esse encoder; sua presença no FFmpeg não garante disponibilidade no hardware. O terminal informa o encoder usado. A composição/filtros, a extração intermediária e os demais passos em CPU continuam como antes. A aceleração AMD ainda precisa de validação em hardware real. As etapas com Ollama/Whisper verificam cancelamento nos pontos disponíveis; nem toda chamada é interrompida instantaneamente.

Picos emite timestamps/RMS por segundo, sem processar vídeo na varredura. Os relatórios distinguem varredura, extração, transcrição e Ollama, além dos tempos gerais. Tempos detalhados estão contidos no total de análise: não some ambos como etapas independentes.

Antes de preparar a mídia, o pipeline verifica se o Ollama responde e se `llama3.1` está instalado. Essa consulta não carrega o modelo nem garante inferência durante toda a execução. Contexto/Híbrido exibem os blocos avaliados, falhos e suspensos; falhas técnicas não são apresentadas como rejeição editorial. Uma conclusão com limitações ou sugestões é identificada na interface e no relatório.

## Estúdio e marca

O preview Twitch é extraído de **30:00 até 30:10**, sem recuar para a abertura. Outras origens usam o minuto 1 e permitem alternativa para arquivos curtos.

O enquadramento usa percentuais da imagem original. O preview acompanha a proporção da fonte, a lupa acompanha a área selecionada, e presets anteriores não são regravados automaticamente. Redimensionar mantém 16:9; o preset antigo pode ter outra proporção.

Na aba **Marca do canal**, envie um PNG (até 5 MB, 4096 pixels por dimensão), ajuste tamanho/posição e salve. Pode ser logo ou texto transparente com o endereço do canal. A posição automática acompanha a divisão webcam/conteúdo; sem webcam, vale a posição vertical configurada. A simulação ilustra uma webcam 16:9, não o vídeo renderizado real. Cada nova execução recebe uma cópia estável da marca; não altera vídeos já gerados.

O envio de um PNG ativa a marca automaticamente. Para uma imagem já salva e desativada, marque **Aplicar marca aos cortes** e salve. Desmarcar e salvar desativa a aplicação. O terminal informa o estado da marca no início de cada execução.

Com o modo estúdio ativo, a webcam ocupa uma área acima do conteúdo, sem cobri-lo. O conteúdo preenche toda a área abaixo com recorte central, mantendo a proporção e cortando as laterais quando necessário, sem faixas de preenchimento. Sem webcam, permanece o recorte vertical central.

As legendas usam Bangers em amarelo, em grupos de 3–5 palavras quando a fala permite. Pausas, finais de frase e duração máxima do grupo podem produzir grupos menores. Os timestamps continuam provenientes da transcrição; essa apresentação não corrige erros de reconhecimento ou sincronização.

## Revisão opcional de legendas (teste)

Galeria e revisão usam a mesma ordenação: execuções mais recentes primeiro e número original do corte em ordem crescente dentro de cada execução. Edições não alteram essa ordem e exclusões não renumeram os demais. A revisão abre na lista de salvos; arquivos que existem apenas em Exportados ficam em um filtro separado. Os cards mostram a identificação da execução para distinguir números iguais de sessões diferentes.

A aba **Revisão de legendas** e o card abaixo de **Hardware & Pastas** permitem abrir os cortes com base disponível. O modal mostra o original horizontal para ouvir a fala e editar os grupos por início/fim em segundos. É possível corrigir texto, adicionar ou excluir grupos; os tempos devem estar em ordem e sem sobreposição. A sobreposição no player é apenas uma prévia de edição.

**Aplicar e gerar corte corrigido** refaz somente a composição vertical, a marca e a legenda, usando as configurações salvas naquela execução. Após validação do vídeo, substitui o corte salvo. Cópias exportadas permanecem intactas: exporte novamente para atualizá-las. Em caso de erro de renderização, o vídeo anterior permanece disponível.

As bases ficam em `cache_revisao/<id único>/`: original horizontal, marca da execução e JSON com sessão, vídeo final, enquadramento e legendas. Novos pipelines usam apenas seus próprios temporários e não removem essas bases. Cortes anteriores à mudança aparecem sem base de revisão.

**Limpar cache**, no lado direito das abas, mostra espaço e quantidade de bases antes de confirmar. Remove somente as bases de revisão, preservando transcrições, finais e exportações. Pipeline, aplicação de revisão e limpeza são mutuamente exclusivos. O cache permanece até limpeza manual e ocupa espaço adicional.

Whisper **Small**, CPU/int8, está ativo nos três modos. O primeiro uso pode baixar o modelo e o processamento pode levar mais tempo. O cache de transcrição identifica o modelo e não reaproveita resultados do Base.

## Galeria e desktop

Na galeria, a exclusão libera os players antes de remover os arquivos. O resultado separa cortes excluídos, ausentes e bloqueados; as cópias em `Cortes_Exportados` são preservadas.

No desktop, **Descarregar** abre o seletor nativo “Salvar como” e copia o corte para o destino escolhido. A exportação em lote continua usando `Cortes_Exportados` e informa essa pasta no modal de resultado. Os botões de apoio Pix e PayPal ficam no cabeçalho e abrem suas páginas no navegador padrão.

No desktop, “Abrir site” da aba Social abre uma janela WebView2 separada do mesmo aplicativo; no navegador, abre outra aba. As sessões ficam no perfil local do WebView2 e essas janelas não recebem a ponte Python da interface principal. Veja [detalhes do fluxo social](docs/REDES_SOCIAIS.md).

## Pastas e API

- `core/`: análise, transcrição, seleção, composição, marca e execução.
- `api/`: rotas, validação, marca e diagnóstico de dependências.
- `frontend/src/`: interface React.
- `desktop.py`: janela WebView2; `main.py`: servidor para navegador.
- `app.py`: Gradio opcional legado; instale Gradio separadamente se precisar.
- `Cortes_Prontos/`, `Cortes_Exportados/`: vídeos; a exportação copia os MP4.
- `temp_clip_cache/`: previews e temporários; `transcricoes/`: cache completo.
- `relatorios_curadoria/`: decisões e tempos; `marca/`: PNG/configuração.
- `logs/`: diagnósticos do desktop. Cortes antigos não são apagados ao iniciar um processamento.

Rotas principais: `POST /api/iniciar-pipeline`, `POST /api/stop-pipeline`, `GET /api/status`, `GET /api/clips`, `POST /api/gerar-preview`, `GET/POST /api/studio-config`, `POST /api/exportar-selecionados`, `POST /api/deletar-selecionados`, `GET /api/relatorios-curadoria/{nome}`, `GET/PUT/DELETE /api/marca`, `GET/PUT /api/marca/imagem`, `GET /api/ambiente`, `GET/PUT /api/social`.

Parâmetros do pipeline: `entrada`, `max_cortes`, `ignorar_inicio_segundos`, `modo_curadoria`, `termos_jogo`, `limite_amostras`.

## Validação

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
cd frontend
npm run lint
npm run build
```

Há testes com mídia sintética e FFmpeg real; as chamadas de IA são simuladas para testes determinísticos. Isso não substitui validação da qualidade editorial, CDN ao vivo, visual da janela e teste em PC limpo. O teste do instalador falha de propósito se o Serial ClipPRO estiver aberto.

O executável aceita `--self-test`: verifica imports, frontend e runtime WebView2 sem abrir janela nem baixar modelos; grava `self-test.json` na pasta de dados. Não valida a renderização da janela nem o pipeline completo.

O andamento das correções está em [Plano de correções](docs/PLANO_DE_CORRECOES.md).

---

## Licença

Código sob licença [MIT](LICENSE): uso, modificação e redistribuição livres, inclusive comercial, mantendo o aviso de copyright. Componentes de terceiros permanecem sujeitos às respectivas licenças (por exemplo, a fonte Bangers, sob [SIL Open Font License](assets/fonts/Bangers/OFL.txt)).

Desenvolvido por **SerialHealer**.
