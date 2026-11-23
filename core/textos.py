"""Mensagens do backend que aparecem na tela, em português e inglês.

O idioma é o da interface (core/interface.py). Logs técnicos (print), o
relatório de curadoria e o prompt da IA não passam por aqui.
Use tr('chave', variavel=valor); variáveis entram como {variavel}.
"""
from core import interface

TEXTOS = {
    # --- Status do pipeline ---
    'status.preparando_execucao': ('Preparando execução...', 'Preparing run...'),
    'status.cancelando': ('Cancelando; aguardando a etapa atual encerrar...',
                          'Cancelling; waiting for the current step to finish...'),
    'status.cancelado': ('Pipeline cancelado pelo usuário.', 'Pipeline cancelled by the user.'),
    'status.verificando_ollama': ('Verificando Ollama e modelo {modelo}...', 'Checking Ollama and model {modelo}...'),
    'status.passo1': ('Passo 1/3: Preparando fontes de mídia...', 'Step 1/3: Preparing media sources...'),
    'status.passo2': ('Passo 2/3: Analisando contexto de diálogos e reações...',
                      'Step 2/3: Analyzing dialogue and reaction context...'),
    'status.passo3': ('Passo 3/3: Renderizando corte {atual} de {total}...', 'Step 3/3: Rendering clip {atual} of {total}...'),
    'status.erro': ('Erro: {erro}', 'Error: {erro}'),
    'status.concluido': ('Pipeline Concluído com Sucesso! ({tempo})', 'Pipeline Completed Successfully! ({tempo})'),
    'status.concluido_limitacoes': ('Processamento concluído com limitações na curadoria. ({tempo})',
                                    'Processing finished with curation limitations. ({tempo})'),
    'status.concluido_sugestoes': ('Processamento concluído com sugestões para revisão. ({tempo})',
                                   'Processing finished with suggestions to review. ({tempo})'),
    'status.corte_contexto': ('Preparando corte por contexto {atual}/{total}...', 'Preparing context clip {atual}/{total}...'),
    'status.analisando_bloco': ('Analisando contexto: bloco {atual}/{total}...', 'Analyzing context: block {atual}/{total}...'),
    'status.mapa_cache': ('Mapa de áudio recuperado do cache.', 'Audio map restored from cache.'),
    'status.rotulo_picos': ('Picos', 'Peaks'),
    'status.rotulo_hibrido': ('Híbrido', 'Hybrid'),
    'status.mapeando': ('{rotulo}: mapeando áudio para escolher amostras...', '{rotulo}: mapping audio to pick samples...'),
    'status.mapeando_progresso': ('{rotulo}: mapeando áudio para escolher amostras ({feito} de {total})...',
                                  '{rotulo}: mapping audio to pick samples ({feito} of {total})...'),
    'status.transcrevendo_amostra': ('{rotulo}: transcrevendo amostra {atual}/{total} ({dispositivo})...',
                                     '{rotulo}: transcribing sample {atual}/{total} ({dispositivo})...'),
    'status.transcricao_cache': ('Transcrição completa recuperada do cache.', 'Full transcript restored from cache.'),
    'status.preparando_audio': ('Preparando áudio completo para análise de contexto...',
                                'Preparing full audio for context analysis...'),
    'status.transcrevendo_vod': ('Transcrevendo a VOD: bloco {atual}/{total} ({dispositivo})...',
                                 'Transcribing the VOD: block {atual}/{total} ({dispositivo})...'),

    # --- Resumo da curadoria ---
    'curadoria.nao_avaliada': ('Curadoria não concluída: nenhum bloco recebeu avaliação válida da IA. Consulte o relatório.',
                               'Curation not completed: no block got a valid evaluation from the AI. Check the report.'),
    'curadoria.parcial': ('Curadoria parcial: {falhas} de {total} blocos não foram avaliados.',
                          'Partial curation: {falhas} of {total} blocks were not evaluated.'),
    'curadoria.sem_fala': ('Nenhum segmento de fala disponível para curadoria.', 'No speech segments available for curation.'),
    'curadoria.so_sugestoes': ('A IA avaliou os blocos, mas não selecionou candidatos; os cortes são sugestões para revisão.',
                               'The AI evaluated the blocks but selected no candidates; the clips are suggestions to review.'),
    'curadoria.completa': ('Curadoria concluída. Revise os cortes selecionados antes de publicar.',
                           'Curation complete. Review the selected clips before publishing.'),
    'curadoria.sugestoes_sem_aprovacao': (' Os cortes são sugestões automáticas, sem aprovação da IA.',
                                          ' The clips are automatic suggestions, not approved by the AI.'),
    'curadoria.um_descartado': (' 1 momento indicado pela IA foi descartado por duração ou IDs inválidos.',
                                ' 1 moment picked by the AI was discarded for invalid duration or IDs.'),
    'curadoria.varios_descartados': (' {total} momentos indicados pela IA foram descartados por duração ou IDs inválidos.',
                                     ' {total} moments picked by the AI were discarded for invalid duration or IDs.'),

    # --- Ollama e modelos ---
    'ollama.modelo_ausente': ('Modelo {modelo} não encontrado no Ollama. Instale-o ou escolha outro modelo em Primeiros Passos antes de iniciar.',
                              'Model {modelo} not found in Ollama. Install it or choose another model in Getting Started before starting.'),
    'ollama.recusou': ('Ollama recusou a verificação do modelo: {erro}', 'Ollama refused the model check: {erro}'),
    'ollama.offline': ('Ollama não respondeu. Abra o Ollama e verifique as dependências antes de iniciar novamente.',
                       'Ollama did not respond. Open Ollama and check the dependencies before starting again.'),
    'ollama.offline_escolha': ('O Ollama não respondeu. Abra o Ollama para escolher um modelo instalado.',
                               'Ollama did not respond. Open Ollama to choose an installed model.'),
    'ollama.nao_instalado': ('O modelo {modelo} não está instalado no Ollama.', 'The model {modelo} is not installed in Ollama.'),
    'modelo.perfil.Recomendado': ('Recomendado', 'Recommended'),
    'modelo.perfil.Leve': ('Leve', 'Light'),
    'modelo.perfil.Intermediário': ('Intermediário', 'Intermediate'),
    'modelo.perfil.Experimental': ('Experimental', 'Experimental'),
    'modelo.gemma4:12b': ('Melhor curadoria nos testes: descreve os momentos com precisão e cita falas reais.',
                          'Best curation in our tests: describes moments precisely and quotes real lines.'),
    'modelo.llama3.1:latest': ('Funciona na maioria das placas. Encontra mais momentos, com descrições menos precisas.',
                               'Runs on most GPUs. Finds more moments, with less precise descriptions.'),
    'modelo.qwen3.5:9b': ('Boas descrições, mas pode juntar ou alterar as falas citadas.',
                          'Good descriptions, but may merge or alter the quoted lines.'),
    'modelo.qwen3:14b': ('Muito seletivo: encontrou poucos momentos nos testes.', 'Very selective: found few moments in our tests.'),
    'modelo.nao_avaliado': ('Modelo não avaliado no ClipPRO; os resultados podem variar.',
                            'Model not evaluated in ClipPRO; results may vary.'),

    # --- Dependências ---
    'ambiente.nao_encontrado': ('Não encontrado no PATH', 'Not found on PATH'),
    'ambiente.disponivel': ('Disponível', 'Available'),
    'ambiente.falha': ('Falha ao executar', 'Failed to run'),
    'ambiente.modelo': ('modelo de IA ({modelo})', 'AI model ({modelo})'),
    'ambiente.modelo_ausente': ('Modelo não instalado', 'Model not installed'),
    'ambiente.sem_resposta': ('Servidor não respondeu', 'Server did not respond'),
    'ambiente.nao_verificado': ('Não verificado', 'Not checked'),
    'ambiente.observacao': ('Whisper Small: usa a GPU NVIDIA quando ela funciona e, senão, a CPU (int8). O primeiro uso pode baixar o modelo.',
                            'Whisper Small: uses the NVIDIA GPU when it works, otherwise the CPU (int8). The first use may download the model.'),

    # --- Erros do FFmpeg (core/erros.py) ---
    'ffmpeg.expirou': ('o link do vídeo expirou ou deixou de existir (o servidor respondeu {codigo}). Inicie de novo; se o link for de uma live, use o link do VOD.',
                       'the video link expired or no longer exists (the server answered {codigo}). Start again; if the link is from a live stream, use the VOD link.'),
    'ffmpeg.recusou': ('o servidor recusou o acesso ao vídeo (403). O VOD pode ser privado, exclusivo para inscritos, ou o link expirou. Inicie de novo.',
                       'the server refused access to the video (403). The VOD may be private, subscriber-only, or the link expired. Start again.'),
    'ffmpeg.conexao': ('a conexão com o servidor do vídeo falhou. Verifique a internet e inicie de novo.',
                       'the connection to the video server failed. Check your internet and start again.'),
    'ffmpeg.disco': ('não há espaço livre em disco.', 'there is no free disk space.'),
    'ffmpeg.sem_detalhe': ('o FFmpeg terminou sem detalhar o erro.', 'FFmpeg stopped without detailing the error.'),
    'ffmpeg.link_video': ('<link do vídeo>', '<video link>'),
    'ffmpeg.analisar_audio': ('Falha ao analisar o áudio', 'Failed to analyze the audio'),
    'ffmpeg.extrair_trecho': ('Falha ao extrair o trecho do corte', 'Failed to extract the clip segment'),
    'ffmpeg.extrair_amostra': ('Falha ao extrair amostra de áudio', 'Failed to extract an audio sample'),
    'ffmpeg.renderizar': ('Falha ao renderizar o corte {numero}', 'Failed to render clip {numero}'),
    'ffmpeg.preparar_audio': ('Falha ao preparar o áudio', 'Failed to prepare the audio'),

    # --- Links e downloads ---
    'link.live': ('Esse link é de uma live em andamento (ou do canal). O Serial ClipPRO trabalha com vídeos completos: '
                  'use o link do VOD, por exemplo twitch.tv/videos/… ou kick.com/canal/videos/…, depois que a live terminar.',
                  'This link is for a live stream in progress (or the channel). Serial ClipPRO works with complete videos: '
                  'use the VOD link, for example twitch.tv/videos/… or kick.com/channel/videos/…, after the stream ends.'),
    'link.offline': ('O canal está offline e o link não aponta para um VOD. Use o link do VOD (twitch.tv/videos/… ou kick.com/canal/videos/…).',
                     'The channel is offline and the link does not point to a VOD. Use the VOD link (twitch.tv/videos/… or kick.com/channel/videos/…).'),
    'link.kick_api': ('A Kick não encontrou esse VOD pela API.', 'Kick could not find this VOD through its API.'),
    'link.nao_abre': ('Não foi possível abrir o link: {erro}', 'Could not open the link: {erro}'),
    'link.kick_curl': ('A Kick só entrega a página do VOD a navegadores. Falta o componente curl_cffi, que permite ao app acessar a Kick como um navegador.',
                       'Kick only serves the VOD page to browsers. The curl_cffi component, which lets the app reach Kick like a browser, is missing.'),
    'link.kick_sem_video': ('A página do VOD da Kick não trouxe o link do vídeo. Confira se o VOD abre no navegador e se não é exclusivo para inscritos.',
                            'The Kick VOD page did not include the video link. Check that the VOD opens in the browser and is not subscriber-only.'),
    'link.sem_stream': ('Não foi possível obter a URL de streaming do vídeo.', 'Could not get the video streaming URL.'),
    'link.sem_audio_hibrido': ('Não foi possível obter uma fonte de áudio para o modo híbrido.', 'Could not get an audio source for hybrid mode.'),
    'link.youtube_sem_audio': ('O áudio do YouTube não foi gerado.', 'The YouTube audio was not generated.'),
    'link.youtube_falhou': ('Falha ao preparar YouTube: {erro}', 'Failed to prepare YouTube: {erro}'),

    # --- Pipeline ---
    'pipeline.em_andamento': ('Já existe uma execução em andamento.', 'A run is already in progress.'),
    'pipeline.entrada_invalida': ('Informe uma entrada e um limite de 1 a 50 cortes.', 'Provide an input and a limit of 1 to 50 clips.'),
    'pipeline.arquivo_ausente': ('Arquivo de vídeo local não encontrado: {entrada}', 'Local video file not found: {entrada}'),
    'pipeline.modo_invalido': ('Modo de curadoria inválido.', 'Invalid curation mode.'),
    'pipeline.sem_gancho': ('Nenhum gancho válido encontrado na varredura.', 'No valid hook found in the scan.'),
    'pipeline.video_invalido': ('O vídeo produzido não pôde ser validado: {erro}', 'The produced video could not be validated: {erro}'),
    'pipeline.video_incompleto': ('O arquivo produzido precisa conter vídeo, áudio e duração positiva.',
                                  'The produced file must contain video, audio and a positive duration.'),
    'pipeline.audio_sem_timestamps': ('A análise de áudio não retornou timestamps válidos.', 'The audio analysis returned no valid timestamps.'),
    'pipeline.sem_cortes_falas': ('Não foi possível montar cortes a partir das falas. Consulte o relatório de curadoria.',
                                  'Could not build clips from the speech. Check the curation report.'),
    'pipeline.sem_amostras': ('Não foi possível determinar trechos para amostragem.', 'Could not determine segments to sample.'),
    'pipeline.sem_audio': ('Nenhum áudio disponível para transcrição.', 'No audio available for transcription.'),
    'pipeline.fonte_ausente': ('Fonte Bangers ausente. Verifique os arquivos do aplicativo.', 'Bangers font missing. Check the app files.'),
    'pipeline.ja_em_execucao': ('Pipeline em execução ou encerrando. Aguarde.', 'Pipeline running or stopping. Please wait.'),
    'pipeline.iniciado': ('Pipeline iniciado.', 'Pipeline started.'),
    'pipeline.cancelamento': ('Cancelamento solicitado.', 'Cancellation requested.'),
    'pipeline.nada_ativo': ('Nenhuma execução ativa.', 'No active run.'),

    # --- Preview e estúdio ---
    'preview.entrada_invalida': ('URL ou entrada inválida.', 'Invalid URL or input.'),
    'preview.cache': ('Preview recuperado do cache instantaneamente.', 'Preview restored from cache instantly.'),
    'preview.iniciado': ('Geração do preview do estúdio iniciada em segundo plano.', 'Studio preview generation started in the background.'),
    'preview.nao_gerado': ('O preview não foi gerado.', 'The preview was not generated.'),
    'preview.arquivo_ausente': ('Arquivo não encontrado: {entrada}', 'File not found: {entrada}'),
    'estudio.salvo': ('Configuração salva; será aplicada aos próximos cortes renderizados.',
                      'Settings saved; they will apply to the next rendered clips.'),
    'estudio.fora_do_video': ('O enquadramento deve ficar dentro do vídeo (0 a 100%).', 'The framing must stay inside the video (0 to 100%).'),
    'entrada.vazia': ('Informe um caminho de vídeo ou URL.', 'Provide a video path or URL.'),

    # --- Seletor de arquivos ---
    'seletor.so_local': ('O seletor está disponível somente neste computador.', 'The file picker is only available on this computer.'),
    'seletor.origem': ('Origem não permitida.', 'Origin not allowed.'),
    'seletor.falhou': ('Não foi possível abrir o seletor de arquivos: {erro}', 'Could not open the file picker: {erro}'),
    'seletor.windows': ('O seletor local requer Windows.', 'The local file picker requires Windows.'),
    'seletor.aberto': ('Já existe um seletor de arquivos aberto.', 'A file picker is already open.'),
    'seletor.titulo': ('Selecionar vídeo — Serial ClipPRO', 'Choose video — Serial ClipPRO'),
    'seletor.videos': ('Vídeos', 'Videos'),
    'seletor.todos': ('Todos os arquivos', 'All files'),

    # --- Galeria ---
    'galeria.relatorio_ausente': ('Relatório não encontrado.', 'Report not found.'),
    'galeria.exportados': ('{total} cortes exportados com segurança!', '{total} clips exported safely!'),
    'galeria.nome_invalido': ('Nome de corte inválido.', 'Invalid clip name.'),
    'galeria.em_uso': ('Arquivo em uso ou sem permissão para excluir.', 'File in use or no permission to delete it.'),
    'galeria.metadados': ('Vídeo excluído; metadados não puderam ser removidos.', 'Video deleted; its metadata could not be removed.'),
    'galeria.excluidos': ('{apagados} corte(s) excluído(s). {falhas} não puderam ser excluídos. {ausentes} já estavam ausentes.',
                          '{apagados} clip(s) deleted. {falhas} could not be deleted. {ausentes} were already missing.'),
    'galeria.nao_encontrado': ('Corte não encontrado.', 'Clip not found.'),

    # --- Revisão ---
    'revisao.aguarde': ('Aguarde o pipeline ou a revisão terminar.', 'Wait for the pipeline or the review to finish.'),
    'revisao.cache_limpo': ('Bases de revisão removidas. Vídeos finais, exportados e transcrições preservados.',
                            'Review bases removed. Final videos, exports and transcripts were kept.'),
    'revisao.sem_base': ('Base de revisão indisponível.', 'Review base unavailable.'),
    'revisao.iniciada': ('Revisão iniciada.', 'Review started.'),
    'revisao.id_invalido': ('Identificador inválido.', 'Invalid identifier.'),
    'revisao.fora_cache': ('Base fora do cache de revisão.', 'Base outside the review cache.'),
    'revisao.sem_espaco': ('Espaço insuficiente para preservar o original de revisão. Libere espaço e tente novamente.',
                           'Not enough space to keep the review original. Free up space and try again.'),
    'revisao.original_removido': ('Original removido do cache.', 'Original removed from the cache.'),
    'revisao.cache_invalido': ('Diretório de cache inválido.', 'Invalid cache folder.'),
    'revisao.legenda_mudou': ('A legenda mudou. Reabra o corte antes de editar.', 'The subtitles changed. Reopen the clip before editing.'),
    'revisao.tempos': ('Timestamps devem estar em ordem, sem sobreposição e dentro do corte.',
                       'Timestamps must be in order, without overlaps and inside the clip.'),

    # --- Marca e redes ---
    'marca.limite': ('O limite da imagem é 5 MB.', 'The image limit is 5 MB.'),
    'marca.ausente': ('Nenhuma marca enviada.', 'No branding uploaded.'),
    'marca.png': ('Envie um PNG de até 5 MB.', 'Upload a PNG of up to 5 MB.'),
    'marca.dimensao': ('Envie um PNG com até 4096 pixels por dimensão.', 'Upload a PNG of up to 4096 pixels per side.'),
    'social.metodo': ('Método indisponível.', 'Method unavailable.'),
    'social.plataforma': ('Plataforma indisponível.', 'Platform unavailable.'),

    # --- Janela desktop ---
    'desktop.ja_aberto': ('O Serial ClipPRO já está aberto. Use a janela existente.',
                          'Serial ClipPRO is already open. Use the existing window.'),
    'desktop.servidor': ('O servidor local não iniciou. Consulte a pasta logs.', 'The local server did not start. Check the logs folder.'),
    'desktop.reparar': ('Use Preparar ou reparar Serial ClipPRO no menu Iniciar para verificar dependências. '
                        'Detalhes em logs/errors.log na pasta de dados.',
                        'Use “Preparar ou reparar Serial ClipPRO” in the Start menu to check the dependencies. '
                        'Details in logs/errors.log in the data folder.'),
    'desktop.processando_titulo': ('Processamento em andamento', 'Processing in progress'),
    'desktop.processando_texto': ('Cancele o pipeline ou aguarde a revisão/preview terminar antes de fechar a aplicação.',
                                  'Cancel the pipeline or wait for the review/preview to finish before closing the app.'),
    # --- Atualização pelo app ---
    'atualizacao.sem_conexao': ('Não foi possível consultar as atualizações: {erro}',
                                'Could not check for updates: {erro}'),
    'atualizacao.resposta_invalida': ('O GitHub respondeu num formato inesperado. Tente de novo mais tarde.',
                                      'GitHub replied in an unexpected format. Try again later.'),
    'atualizacao.ja_atualizado': ('Você já está na versão mais recente.', 'You are already on the latest version.'),
    'atualizacao.sem_assinatura': ('Esta versão não tem instalador assinado para atualizar pelo app. Baixe pela página da Release.',
                                   'This version has no signed installer for in-app updates. Download it from the Release page.'),
    'atualizacao.ja_baixando': ('O download da atualização já está em andamento.', 'The update download is already in progress.'),
    'atualizacao.assinatura_invalida': ('O instalador baixado não passou na verificação de assinatura e foi apagado. '
                                        'Baixe pela página da Release ou tente mais tarde.',
                                        'The downloaded installer failed the signature check and was deleted. '
                                        'Download it from the Release page or try later.'),
    'atualizacao.falha_download': ('O download da atualização falhou: {erro}', 'The update download failed: {erro}'),
    'atualizacao.so_instalado': ('A atualização pelo app só funciona no Serial ClipPRO instalado.',
                                 'In-app updates only work in the installed Serial ClipPRO.'),
    'atualizacao.nao_baixada': ('Baixe a atualização antes de instalar.', 'Download the update before installing.'),
    'atualizacao.aguarde': ('Aguarde o processamento, a revisão ou o preview terminar antes de atualizar.',
                            'Wait for processing, review or preview to finish before updating.'),
    'atualizacao.instalando': ('O app vai fechar e o instalador abrirá em seguida. Ao terminar, o Serial ClipPRO reabre sozinho.',
                               'The app will close and the installer will open next. When it finishes, Serial ClipPRO reopens on its own.'),
}


def tr(chave, **variaveis):
    """Texto da chave no idioma da interface; chave desconhecida volta como está."""
    par = TEXTOS.get(chave)
    if par is None:
        return chave
    texto = par[1] if interface.idioma() == 'en' else par[0]
    return texto.format(**variaveis) if variaveis else texto
