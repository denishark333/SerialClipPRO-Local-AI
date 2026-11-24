<div align="center">
  <img width="256" alt="Serial ClipPRO" src="https://github.com/user-attachments/assets/2953e1f4-7822-4cbd-99e9-09bf8a27694a" />
  <h1>Serial ClipPRO</h1>
</div>


[English](README.md) | **Português**

<img width="1920" height="1045" alt="image" src="https://github.com/user-attachments/assets/4de74f11-5c49-43de-a4cd-ec6592ea3d06" />

**Sua live continua em cada corte.**

Lives longas, pouco tempo para editar? O Serial ClipPRO analisa suas VODs e prepara cortes verticais enquanto você está longe do PC. Depois, você revisa e escolhe o que publicar.

Este repositório reúne o código-fonte, os pacotes de instalação e as versões públicas do aplicativo para Windows.

## Download

Acesse **Releases**, neste repositório, e baixe o instalador anexado à versão desejada (`Serial-ClipPRO-3.0.1-Setup-x64.exe` na versão 3.0.1). A partir da 3.0.1, as versões novas também podem ser instaladas pelo próprio aplicativo (veja [Atualização](#atualização)).

> Baixe o instalador **Serial ClipPRO**. Os arquivos automáticos “Source code (zip)” e “Source code (tar.gz)” contêm o código-fonte, não o aplicativo pronto.

## O que o aplicativo faz

- Processa VODs de Twitch, YouTube e Kick, além de vídeos locais.
- Encontra os melhores momentos da VOD inteira com IA local, citando a fala que justifica cada corte.
- Funciona com lives em vários idiomas e com qualquer gênero; o campo **O que procurar** indica os momentos que você quer priorizar.
- Gera cortes verticais em formato 9:16 com legendas animadas: a palavra falada fica em destaque.
- Permite ajustar o enquadramento da webcam, escolher qual parte do conteúdo entra no corte vertical e incluir a marca do seu canal em PNG.
- Oferece uma galeria para revisar, baixar, exportar e excluir cortes.
- Permite revisar e corrigir as legendas e o enquadramento de cada corte.
- Reúne atalhos para acessar as plataformas e publicar manualmente.
- Interface em português ou inglês, e atualização pelo próprio app quando você quiser.

A IA auxilia na seleção. Revise os cortes e as legendas antes de publicar.

## Novidades da versão 3.0.1

- **Atualização pelo próprio app:** o botão **Verificar atualizações**, ao lado da versão, mostra se há versão nova e o que mudou, e instala com um clique. O app só confere quando você pede e só atualiza se você quiser. Cada instalador é verificado pela assinatura digital antes de rodar, e vídeos, configurações e o seu modelo de IA são mantidos.
- **Interface em inglês:** o seletor **PT | EN**, abaixo do cabeçalho, traduz a interface inteira, inclusive as mensagens do processamento. O instalador também está em português e inglês: o idioma escolhido nele é o que o app usa ao abrir (sem escolha, segue o do Windows).
- **Recorte vertical fora do centro:** arraste a moldura para escolher qual parte do conteúdo aparece no corte, ideal para HUDs, chats ou ação fora do centro.
- **Enquadramento por corte:** na **Revisão de legendas**, corrija a webcam ou o recorte de um corte específico quando a câmera mudou de lugar ou de tamanho na live, sem reprocessar a VOD e sem mudar os outros cortes.
- **Placas AMD e Intel:** a renderização agora usa AMD AMF (testado em placa Radeon) e Intel QuickSync, além da NVIDIA NVENC, e recorre à CPU quando nenhuma está disponível. O seletor de modelos também passou a ler a memória de vídeo das placas AMD.
- **Progresso mais claro:** em VODs longas, a barra avança enquanto o áudio é mapeado e mostra o ponto que está sendo lido (ex.: "04:12:30 de 11:31:59"). O idioma da live fica sempre visível ao lado de **Configurações avançadas**, e o card **IA Engine** mostra o modelo de IA em uso.

## Novidades da versão 3.0

- **Curadoria refeita:** cortes que começam e terminam em frases completas, momentos curtos ampliados com o contexto ao redor e a fala-chave de cada corte conferida na transcrição.
- **Modelo de IA à sua escolha:** Gemma 4 12B (recomendado), Llama 3.1 8B (leve) e outros; escolha na instalação e troque quando quiser no app.
- **Idioma da live** e **O que procurar**, com modelos prontos para MMORPG, FPS, Just Chatting e Podcast.
- **Legenda em destaque:** a palavra que está sendo falada cresce; o estilo clássico continua disponível na aba Marca.
- **Kick:** VODs com o identificador novo funcionam, e links de live são recusados com a orientação de usar o VOD.
- **Mais rápido:** transcrição na GPU NVIDIA (opcional na instalação) e etapas já feitas reaproveitadas ao processar a mesma VOD de novo.
- **Instalador personalizável:** você escolhe os modelos e a aceleração NVIDIA, e a preparação acontece dentro do assistente, com barra de progresso.

## Instalação e primeiro uso

1. Baixe o instalador em **Releases**, execute-o e escolha o idioma (português ou inglês). O app abre no mesmo idioma, e você pode trocar depois em **PT | EN**.
2. Na página **Componentes**, escolha:
   - **Modelos de IA:** marque um ou mais. O **Gemma 4 12B** é o recomendado (precisa de ~10 GB de memória de vídeo); o **Llama 3.1 8B** é o mais leve. Se nenhum for marcado, o Llama 3.1 é instalado.
   - **Aceleração NVIDIA (CUDA):** transcrição ~4x mais rápida em placas NVIDIA (download de 528 MB). Vem marcada quando há placa NVIDIA.
   - Os componentes essenciais (aplicativo, FFmpeg, Ollama, Whisper, WebView2 e curl_cffi) são sempre instalados.
3. Aguarde a preparação: a barra mostra cada download e verificação.
4. Se aparecer a janela inicial do **Ollama**, prossiga com o **uso local**. Não é necessário usar modelos cloud.
5. Ao final, abra o Serial ClipPRO pelo instalador ou pelo atalho criado.

Nos próximos usos, basta abrir o atalho **Serial ClipPRO**. Outros modelos podem ser instalados depois com `ollama pull nome-do-modelo` e escolhidos em **Primeiros Passos**.

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

1. Informe o link de uma VOD (Twitch, Kick ou YouTube) ou selecione um arquivo local. Lives em andamento não são aceitas.
2. Escolha o modo de análise e, em **Configurações avançadas**, o idioma da live.
3. Ajuste o enquadramento e a marca, se desejar.
4. Inicie o processamento.
5. Revise os vídeos na galeria e exporte seus favoritos.

Mantenha o computador ligado e sem entrar em suspensão durante o processamento.

## Modos de análise

| Modo | Como funciona |
|---|---|
| **Híbrido** | Combina picos de áudio com amostras distribuídas ao longo de toda a VOD. Recomendado para lives longas. |
| **Picos de áudio** | Avalia todos os momentos mais intensos da VOD e fica com os de maior nota. |
| **Contexto completo** | Transcreve e analisa toda a fonte, exigindo mais tempo de processamento. |

Nos três modos, os cortes são escolhidos pela nota em toda a VOD, não pela ordem em que aparecem. Nenhum modo garante encontrar todos os momentos interessantes. O tempo varia conforme a duração da VOD, a conexão, o hardware e as configurações escolhidas.

## Processamento local e hardware

A transcrição e a análise por IA utilizam **Whisper e Ollama no computador**.

- Com a **Aceleração NVIDIA** instalada, o Whisper transcreve na GPU; sem ela, ou sem placa NVIDIA, usa a CPU.
- O modelo de IA da curadoria roda no Ollama; o Gemma 4 12B precisa de ~10 GB de memória de vídeo para rodar inteiro na placa.
- A renderização tenta NVIDIA NVENC, depois AMD AMF, depois Intel QuickSync e, se nenhum estiver disponível, a CPU.
- O seletor de modelos, em **Primeiros Passos**, confere a memória de vídeo de placas NVIDIA e AMD para recomendar um modelo.

O processamento local não elimina a necessidade de internet para baixar modelos, acessar VODs e abrir as plataformas sociais.

## Onde ficam os arquivos?

O programa fica em `%LOCALAPPDATA%\Programs\Serial ClipPRO\`. Os dados ficam separados, em:

`%LOCALAPPDATA%\Serial ClipPRO\`

Cole esse caminho na barra de endereços do Explorador de Arquivos.

| Pasta | Conteúdo |
|---|---|
| `Cortes_Prontos` | Vídeos disponíveis na galeria. |
| `Cortes_Exportados` | Cópias dos cortes exportados em lote. |
| `transcricoes` | Cache de transcrições, amostras, mapas de áudio e curadoria. |
| `relatorios_curadoria` | Relatórios da análise. |
| `cache_revisao` | Bases para revisar legendas dos cortes. |
| `marca` | Imagem e configuração da marca do canal. |
| `logs` | Registros de diagnóstico. |
| `tools` | FFmpeg e, se instalada, a aceleração NVIDIA. |
| `atualizacao` | Instalador baixado pelo atualizador do app; apagado sozinho depois da atualização. |

Excluir um corte da galeria não apaga as cópias já exportadas. O botão **Descarregar** permite escolher onde salvar um vídeo individual.

## Redes sociais

A aba Social reúne atalhos para Instagram, TikTok, YouTube, Twitch e Kick. BiliBili aparece como **Em breve**.

Login e publicação são feitos manualmente nos sites das plataformas. O aplicativo não publica automaticamente.

Se uma plataforma recusar o login na janela integrada, utilize **Abrir no navegador**.

## Atualização

**Pelo próprio aplicativo (a partir da 3.0.1):**

1. Clique em **Verificar atualizações**, ao lado da versão, no topo do app.
2. Se houver versão nova, veja o que mudou e clique em **Baixar atualização**.
3. Com o download verificado, clique em **Instalar agora**. O app fecha, o instalador mostra o progresso e o Serial ClipPRO reabre sozinho.

Nada é consultado nem instalado sem o seu clique. A instalação fica bloqueada enquanto um corte está sendo processado, revisado ou pré-visualizado.

**Manualmente (necessário uma vez para passar da 3.0.0 para a 3.0.1):**

1. Aguarde o processamento terminar e feche o aplicativo.
2. Baixe o instalador da nova versão em **Releases**.
3. Execute o instalador.

As atualizações substituem a versão anterior no mesmo lugar (uma instalação, um atalho) e preservam vídeos, configurações e modelos. Consulte as notas da Release para eventuais instruções específicas.

## Problemas e sugestões

O projeto está em desenvolvimento. Para relatar um problema, abra uma **Issue** neste repositório e informe:

- Versão do Serial ClipPRO.
- Versão do Windows, processador, memória RAM e GPU.
- Origem do vídeo e modo de análise utilizado.
- Etapa em que ocorreu o problema.
- Mensagem de erro e, se possível, uma captura de tela.

Para problemas de instalação, consulte:

`%LOCALAPPDATA%\Serial ClipPRO\instalacao.log`

Para problemas ao atualizar pelo app, consulte também `%LOCALAPPDATA%\Serial ClipPRO\logs\atualizacao.log`.

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

Requer Python e Node para desenvolvimento; FFmpeg/ffprobe no PATH e Ollama com ao menos um modelo (`llama3.1` por padrão; `gemma4:12b` recomendado) para processamento. Com uma placa NVIDIA, instale `nvidia-cublas-cu12` no ambiente para transcrever na GPU.

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

## Instalador - Windows x64

A distribuição usa um único `Serial-ClipPRO-3.0.1-Setup-x64.exe` (Inno Setup). A página de componentes mostra os essenciais (fixos) e as opções: modelos de IA e aceleração NVIDIA. Depois da cópia dos arquivos, o assistente executa `bootstrap.ps1` sem console, com `-Modelos` e `-Gpu`; o script emite linhas `@@PROGRESSO|pct|mensagem`, que o assistente usa na barra de progresso.

- Modelos são baixados pela API do Ollama; se o Ollama for antigo demais para um modelo, ele é atualizado e o download refeito. O mais forte entre os escolhidos vira o modelo da curadoria (`config_ia.json`).
- A aceleração NVIDIA baixa o pacote oficial `nvidia-cublas-cu12` do PyPI (SHA256 fixo) e extrai só `cublas64_12.dll` e `cublasLt64_12.dll` para `tools/cuda`; o CTranslate2 já traz o cuDNN.
- O atalho **Preparar ou reparar** roda a mesma preparação; sem escolha, mantém o modelo já configurado.

O programa fica em `%LOCALAPPDATA%/Programs/Serial ClipPRO/`, separado dos dados em `%LOCALAPPDATA%/Serial ClipPRO/`. Atualizações e desinstalação preservam vídeos, configurações e modelos. Feche o aplicativo após terminar/cancelar as operações antes de atualizar.

Para compilar, prepare um ambiente Python estável x64 chamado `build-env`, instale `requirements-build.lock.txt`, instale Inno Setup e execute `scripts/build_installer.ps1`. O resultado, seu SHA256 e sua assinatura (`.sig`) ficam em `dist/installer/`. O fluxo requer validação em Windows limpo antes de cada distribuição pública.

### Atualização pelo app

O botão **Verificar atualizações** consulta a última Release do GitHub (`/api/atualizacao/*`, `core/atualizacao.py`) só quando o usuário clica. O instalador é baixado para `atualizacao/` na pasta de dados e só é aceito com uma assinatura Ed25519 válida sobre a versão, o nome do arquivo e o SHA-256; a chave pública vem embutida no app. Depois do download, um PowerShell oculto espera o processo do app encerrar e roda o instalador com `/SILENT /ATUALIZACAO=1`. Nesse modo, o instalador reabre o app ao final e roda o `bootstrap.ps1` como reparo (sem `-Modelos`), mantendo o modelo escolhido no app. Toda instalação apaga a `_internal` antes de copiar, para não sobrarem bibliotecas da versão anterior. A versão nova apaga o instalador baixado ao abrir.

Cada Release (tag `vX.Y.Z`) precisa anexar o instalador **e** o `.sig`; sem a assinatura, o app leva o usuário à página da Release. O `build_installer.ps1` assina com a chave privada de `CLIPPRO_CHAVE_ATUALIZACAO` ou `%USERPROFILE%\.serialclippro\chave-atualizacao.pem`, que nunca entra no repositório (`scripts/chave_atualizacao.py gerar` cria o par de chaves; `-SemAssinatura` pula a assinatura, só para testes locais).

O instalador verifica assinaturas dos instaladores Microsoft/Ollama e o SHA256 do FFmpeg e do pacote NVIDIA. Não altera exclusões nem desativa o Defender. Registra diagnóstico em `instalacao.log`, `self-test.json` e `models-setup.json` na pasta de dados.

O desktop bloqueia fechamento enquanto o pipeline estiver ativo: cancele e aguarde antes de fechar. Uma segunda instância desktop usando a mesma pasta de dados é recusada. `CLIPPRO_DATA_DIR` permite escolher outro diretório de dados; no desenvolvimento, os dados ficam na raiz do projeto.

## Modos e custo

- **Híbrido:** varre o áudio e combina picos com cobertura temporal. Até 40 amostras de 90 segundos por padrão (60 minutos de áudio para transcrição). Pode perder acontecimentos fora das amostras. O limite de amostras é diferente do limite de cortes gerados.
- **Picos:** uma amostra por pico de áudio; todas são avaliadas e os cortes saem pela nota.
- **Contexto completo:** prepara e transcreve toda a fonte em blocos; custa mais CPU e leitura de mídia.

A varredura percorre toda a fonte, mesmo sem salvar a VOD integral; o ffmpeg grava a posição com `-progress`, e a barra avança de 15% a 25% durante a varredura. Na Twitch, a análise usa a variante só de áudio; na Kick, a menor qualidade de vídeo (mesmo áudio). Mapa de áudio, amostras transcritas e blocos avaliados ficam em cache: uma nova execução da mesma VOD só refaz o que mudou (o mapa é refeito se a VOD cresceu).

A curadoria envia cada bloco ao modelo configurado com o idioma da live e as prioridades do campo **O que procurar**. A resposta segue um esquema JSON; a fala-chave de cada momento é conferida na transcrição, momentos curtos são ampliados com a fala vizinha, candidatos adjacentes são fundidos e os limites são ajustados a frases completas e pausas. Se a IA não aprovar nada, o app sugere trechos para revisão por sinais neutros (termos e foco informados, exclamações, perguntas, repetições, fala acelerada).

A renderização final e a revisão de legendas tentam NVIDIA NVENC, depois AMD AMF (`h264_amf`), depois Intel QuickSync (`h264_qsv`) e, se todos falharem, CPU com libx264; um encoder que falhar não é tentado de novo na sessão. O áudio é normalizado em duas passagens a -14 LUFS. As etapas com Ollama/Whisper verificam cancelamento nos pontos disponíveis; nem toda chamada é interrompida instantaneamente.

Antes de preparar a mídia, o pipeline verifica se o Ollama responde e se o modelo configurado está instalado. Falhas técnicas não são apresentadas como rejeição editorial; só blocos sem avaliação tornam a curadoria parcial.

## Estúdio e marca

O preview do estúdio é extraído da **metade da VOD** (10 segundos), onde a live costuma estar em andamento e com a webcam visível. Sem duração conhecida, usa 30:00 na Twitch e o minuto 1 nas demais origens.

O enquadramento usa percentuais da imagem original. O preview acompanha a proporção da fonte, a lupa acompanha a área selecionada, e presets anteriores não são regravados automaticamente. Redimensionar mantém 16:9; o preset antigo pode ter outra proporção.

Na aba **Marca do canal**, envie um PNG (até 5 MB, 4096 pixels por dimensão), ajuste tamanho/posição e salve. Pode ser logo ou texto transparente com o endereço do canal. A posição automática acompanha a divisão webcam/conteúdo; sem webcam, vale a posição vertical configurada. A simulação ilustra uma webcam 16:9, não o vídeo renderizado real. Cada nova execução recebe uma cópia estável da marca; não altera vídeos já gerados.

O envio de um PNG ativa a marca automaticamente. Para uma imagem já salva e desativada, marque **Aplicar marca aos cortes** e salve. Desmarcar e salvar desativa a aplicação. O terminal informa o estado da marca no início de cada execução.

Com o modo estúdio ativo, a webcam ocupa uma área acima do conteúdo, sem cobri-lo. O conteúdo preenche toda a área abaixo, mantendo a proporção e cortando as laterais quando necessário, sem faixas de preenchimento. Sem webcam, o conteúdo ocupa o corte vertical inteiro. Nos dois casos, **Posição do conteúdo** (ou arrastar a moldura **Corte vertical** sobre o preview) escolhe qual parte da imagem fica no corte, da esquerda (0%) à direita (100%); o padrão é o centro (50%).

As legendas usam Bangers em amarelo, em grupos de até 5 palavras, quebrando em pausas e finais de frase. No estilo **Destaque** (padrão), a palavra que está sendo falada fica 22% maior; no **Clássico**, a frase aparece inteira de uma vez. O estilo é escolhido na aba Marca e vale também para a revisão. Os tempos vêm da transcrição; essa apresentação não corrige erros de reconhecimento ou sincronização.

## Revisão opcional de legendas (teste)

Galeria e revisão usam a mesma ordenação: execuções mais recentes primeiro e número original do corte em ordem crescente dentro de cada execução. Edições não alteram essa ordem e exclusões não renumeram os demais. A revisão abre na lista de salvos; arquivos que existem apenas em Exportados ficam em um filtro separado. Os cards mostram a identificação da execução para distinguir números iguais de sessões diferentes.

A aba **Revisão de legendas** e o card abaixo de **Hardware & Pastas** permitem abrir os cortes com base disponível. O modal mostra o original horizontal para ouvir a fala e editar os grupos por início/fim em segundos. É possível corrigir texto, adicionar ou excluir grupos; os tempos devem estar em ordem e sem sobreposição. A sobreposição no player é apenas uma prévia de edição.

**Enquadramento deste corte**, abaixo do player, abre o mesmo editor de enquadramento do Modo Estúdio sobre o original daquele corte: ligue ou desligue a webcam, mova ou redimensione o retângulo e mude a posição do conteúdo. A mudança vale só para aquele corte e fica salva na base de revisão dele depois de uma renderização válida; o padrão do Modo Estúdio não muda.

**Aplicar e gerar corte corrigido** refaz somente a composição vertical, a marca e a legenda, usando as configurações salvas naquela execução (ou o novo enquadramento do corte). Após validação do vídeo, substitui o corte salvo. Cópias exportadas permanecem intactas: exporte novamente para atualizá-las. Em caso de erro de renderização, o vídeo anterior permanece disponível.

As bases ficam em `cache_revisao/<id único>/`: original horizontal, marca da execução e JSON com sessão, vídeo final, enquadramento e legendas. Novos pipelines usam apenas seus próprios temporários e não removem essas bases. Cortes anteriores à mudança aparecem sem base de revisão.

**Limpar cache**, no lado direito das abas, mostra espaço e quantidade de bases antes de confirmar. Remove somente as bases de revisão, preservando transcrições, finais e exportações. Pipeline, aplicação de revisão e limpeza são mutuamente exclusivos. O cache permanece até limpeza manual e ocupa espaço adicional.

Ao aplicar uma revisão, frases não editadas mantêm o tempo real de cada palavra; nas editadas e nas bases antigas, o tempo é estimado pelo tamanho de cada palavra.

Whisper **Small** está ativo nos três modos, na GPU NVIDIA quando disponível e na CPU nos demais casos. O primeiro uso pode baixar o modelo.

## Galeria e desktop

Na galeria, a exclusão libera os players antes de remover os arquivos. O resultado separa cortes excluídos, ausentes e bloqueados; as cópias em `Cortes_Exportados` são preservadas.

No desktop, **Descarregar** abre o seletor nativo “Salvar como” e copia o corte para o destino escolhido. A exportação em lote continua usando `Cortes_Exportados` e informa essa pasta no modal de resultado. Os botões de apoio Pix e PayPal ficam no cabeçalho e abrem suas páginas no navegador padrão.

No desktop, “Abrir site” da aba Social abre uma janela WebView2 separada do mesmo aplicativo; no navegador, abre outra aba. As sessões ficam no perfil local do WebView2 e essas janelas não recebem a ponte Python da interface principal.

## Pastas e API

- `core/`: análise, transcrição, seleção, composição, marca e execução.
- `api/`: rotas, validação, marca e diagnóstico de dependências.
- `frontend/src/`: interface React.
- `desktop.py`: janela WebView2; `main.py`: servidor para navegador.
- `Cortes_Prontos/`, `Cortes_Exportados/`: vídeos; a exportação copia os MP4.
- `temp_clip_cache/`: previews e temporários; `transcricoes/`: cache completo.
- `relatorios_curadoria/`: decisões e tempos; `marca/`: PNG/configuração.
- `logs/`: diagnósticos do desktop. Cortes antigos não são apagados ao iniciar um processamento.
- `atualizacao/`: instalador baixado pelo atualizador, removido depois da atualização.

Os textos da interface ficam em `frontend/src/i18n/` (`pt.js`, `en.js`); as mensagens do backend exibidas na tela ficam em `core/textos.py` e seguem o idioma da interface.

Rotas principais: `POST /api/iniciar-pipeline`, `POST /api/stop-pipeline`, `GET /api/status`, `GET /api/clips`, `POST /api/gerar-preview`, `GET/POST /api/studio-config`, `POST /api/exportar-selecionados`, `POST /api/deletar-selecionados`, `GET /api/relatorios-curadoria/{nome}`, `GET/PUT/DELETE /api/marca`, `GET/PUT /api/marca/imagem`, `GET /api/ambiente`, `GET/PUT /api/social`, `GET/PUT /api/ia`, `GET/PUT /api/interface`, `GET /api/atualizacao/verificar`, `GET /api/atualizacao/status`, `POST /api/atualizacao/{baixar,cancelar,instalar}`.

Parâmetros do pipeline: `entrada`, `max_cortes`, `ignorar_inicio_segundos`, `modo_curadoria`, `termos_jogo`, `limite_amostras`, `idioma`, `foco`.

## Diagnóstico

O executável aceita `--self-test`: verifica imports, frontend, runtime WebView2, o acesso à Kick (curl_cffi) e a verificação de assinatura do atualizador sem abrir janela nem baixar modelos; grava `self-test.json` na pasta de dados. Não valida a renderização da janela nem o pipeline completo.

---

## Licença

Código sob licença [MIT](LICENSE): uso, modificação e redistribuição livres, inclusive comercial, mantendo o aviso de copyright. Componentes de terceiros permanecem sujeitos às respectivas licenças; veja [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). A fonte Bangers está sob a [SIL Open Font License](assets/fonts/Bangers/OFL.txt).

Desenvolvido por **SerialHealer**.
