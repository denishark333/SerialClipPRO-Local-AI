"""Contexto sob demanda com orçamento explícito de áudio, sem cache integral."""
import math
from pathlib import Path
import subprocess
import time
import wave
from core.textos import tr

from core import transcription
from core.whisper import MODELO, carregar_modelo, dispositivo
from core.idiomas import para_whisper
from core.audio import detectar_segmentos_narrativos, medir_duracao
from core.config import atualizar_estado, formatar_tempo
from core.execution import executar_comando
from core.erros import ErroFFmpeg


def planejar_janelas(picos, duracao, limite=40, ignorar_inicio=0):
    """Reserva 1/3 da amostra para cobertura temporal, independente do volume."""
    inicio = ignorar_inicio if duracao > ignorar_inicio else 0
    if not math.isfinite(duracao) or duracao <= inicio:
        return []
    tamanho = min(90., duracao-inicio)
    quantidade = min(limite, max(1, math.ceil((duracao-inicio)/tamanho)))
    cobertura = max(1, math.ceil(quantidade/3))
    janelas = []

    def adicionar(centro, origem):
        a = max(inicio, min(centro-30, duracao-tamanho))
        b = min(duracao, a+tamanho)
        if any(max(0, min(b, j['fim'])-max(a, j['inicio'])) > tamanho*.25 for j in janelas):
            return
        if len(janelas) < quantidade:
            janelas.append({'inicio': a, 'fim': b, 'origem': origem})

    for i in range(cobertura):
        adicionar(inicio+(i+.5)*(duracao-inicio)/cobertura, 'cobertura_temporal')
    # Distribui os picos pela VOD, sem preencher primeiro todas as vagas no início.
    candidatos = [p for p in picos if inicio <= p < duracao]
    while candidatos and len(janelas) < quantidade:
        centro = max(candidatos, key=lambda p: min(abs(p-(j['inicio']+j['fim'])/2) for j in janelas))
        candidatos.remove(centro)
        adicionar(centro, 'pico_audio')
    for i in range(quantidade*2):
        adicionar(inicio+(i+.5)*(duracao-inicio)/(quantidade*2), 'cobertura_temporal')
    return sorted(janelas, key=lambda j: j['inicio'])


def planejar_picos(picos, duracao, ignorar_inicio=0, tamanho=90.):
    """Uma amostra por pico de áudio (30 s antes, 60 s depois), sem cobertura temporal.

    É o modo Picos: todas as amostras são avaliadas e os cortes saem pela nota,
    não pela ordem em que os picos aparecem na VOD.
    """
    inicio = ignorar_inicio if duracao > ignorar_inicio else 0
    if not math.isfinite(duracao) or duracao <= inicio:
        return []
    tamanho = min(tamanho, duracao - inicio)
    janelas = []
    for centro in sorted(picos):
        if not inicio <= centro < duracao:
            continue
        a = max(inicio, min(centro - 30, duracao - tamanho))
        b = min(duracao, a + tamanho)
        if any(max(0, min(b, j['fim']) - max(a, j['inicio'])) > tamanho * .25 for j in janelas):
            continue
        janelas.append({'inicio': a, 'fim': b, 'origem': 'pico_audio'})
    return janelas


def _transcrever_amostra(modelo, fonte, janela, arquivo, execucao, termos, tempos, idioma="pt"):
    """Transcreve uma amostra. Tempos relativos ao início da amostra."""
    t = time.monotonic()
    res = executar_comando([
        'ffmpeg', '-y', '-ss', str(janela['inicio']), '-i', fonte,
        '-t', str(janela['fim']-janela['inicio']), '-vn', '-map', '0:a:0',
        '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(arquivo),
    ], execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tempos['extracao_audio_trechos'] += time.monotonic()-t
    if res.returncode:
        raise ErroFFmpeg(tr('ffmpeg.extrair_amostra'), res.stderr)
    try:
        with wave.open(str(arquivo), 'rb') as wav:
            duracao = wav.getnframes()/wav.getframerate()
        t = time.monotonic()
        iterator, _ = modelo.transcribe(str(arquivo), language=para_whisper(idioma), word_timestamps=True,
                                        beam_size=5, vad_filter=True, hotwords=termos or None)
        segmentos = []
        for seg in iterator:
            execucao.verificar()
            a, b = max(0., float(seg.start)), min(duracao, float(seg.end))
            if not math.isfinite(a) or not math.isfinite(b) or b <= a or not seg.text.strip():
                continue
            palavras = []
            for w in seg.words or []:
                st, et = max(a, float(w.start)), min(b, float(w.end))
                if math.isfinite(st) and math.isfinite(et) and et > st and w.word.strip():
                    palavras.append({'start': st, 'end': et, 'word': w.word.strip()})
            segmentos.append({'start': a, 'end': b, 'text': seg.text.strip(), 'palavras': palavras})
        tempos['transcricao_trechos'] += time.monotonic()-t
    finally:
        arquivo.unlink(missing_ok=True)
    return {'versao': 1, 'duracao': duracao, 'segmentos': segmentos}


def mapear_audio(fonte, entrada, ignorar_inicio, execucao, rotulo=''):
    """Picos de áudio da fonte, com cache por VOD.

    A chave inclui a duração atual da fonte: o VOD de uma live em andamento
    cresce, e um mapa antigo deixaria o final de fora. Sem duração conhecida,
    a varredura é refeita.
    """
    cache = None
    duracao = medir_duracao(fonte, execucao)
    if entrada is not None:
        if duracao:
            cache = transcription.CACHE_DIR / 'mapas' / (transcription.chave(
                'mapa_audio', 1, transcription.identidade_entrada(entrada), round(duracao), ignorar_inicio) + '.json')
            salvo = transcription.ler_json(cache)
            if isinstance(salvo, dict) and isinstance(salvo.get('picos'), list) and salvo.get('duracao', 0) > 0:
                atualizar_estado(tr('status.mapa_cache'), 2, 15)
                return {**salvo, 'do_cache': True}
    def progresso(lido, total):
        # A varredura ocupa de 15% a 25% da barra; a transcrição das amostras vem depois.
        atualizar_estado(tr('status.mapeando_progresso', rotulo=rotulo, feito=formatar_tempo(lido),
                            total=formatar_tempo(total)), 2, 15 + int(10 * lido / total))

    mapa = detectar_segmentos_narrativos(fonte, execucao=execucao, ignorar_inicio_segundos=ignorar_inicio,
                                         retornar_detalhes=True, duracao=duracao, ao_progresso=progresso)
    execucao.verificar()
    if cache and mapa['duracao'] > 0:
        transcription.salvar_json(cache, mapa)
    return mapa


def transcrever_hibrido(fonte, pasta_temp, execucao, termos, ignorar_inicio, limite, registrar, entrada=None,
                        modo='hibrido', idioma='pt'):
    """Amostra e transcreve a fonte.

    No Híbrido, as amostras combinam picos de áudio e cobertura temporal; no
    Picos, há uma amostra por pico. Com ``entrada``, cada amostra transcrita
    fica em cache: uma nova execução da mesma VOD (por exemplo, depois de uma
    queda do Ollama) só transcreve as amostras que faltam.
    """
    rotulo = tr('status.rotulo_picos' if modo == 'picos' else 'status.rotulo_hibrido')
    tempos = {}
    atualizar_estado(tr('status.mapeando', rotulo=rotulo), 2, 15)
    t = time.monotonic()
    mapa = mapear_audio(fonte, entrada, ignorar_inicio, execucao, rotulo)
    tempos['varredura_audio'] = time.monotonic()-t
    tempos['mapa_do_cache'] = bool(mapa.get('do_cache'))
    if modo == 'picos':
        plano = planejar_picos(mapa['picos'], mapa['duracao'], ignorar_inicio)
        limite = len(plano)
    else:
        plano = planejar_janelas(mapa['picos'], mapa['duracao'], limite, ignorar_inicio)
    if not plano:
        raise ValueError(tr('pipeline.sem_amostras'))
    registrar({'amostragem': plano, 'orcamento_trechos': limite,
               'segundos_audio_planejados': sum(j['fim']-j['inicio'] for j in plano), 'tempos_hibrido': tempos})
    execucao.verificar()
    tempos.update(extracao_audio_trechos=0., transcricao_trechos=0., amostras_do_cache=0)
    modelo = None
    segmentos, palavras, grupos = [], [], []
    for indice, janela in enumerate(plano):
        execucao.verificar()
        atualizar_estado(tr('status.transcrevendo_amostra', rotulo=rotulo, atual=indice+1, total=len(plano), dispositivo=dispositivo()), 2, 25+int(9*indice/len(plano)))
        cache = None
        if entrada is not None:
            cache = transcription.CACHE_DIR / 'amostras' / (transcription.chave(
                'amostra_hibrido', 1, transcription.identidade_entrada(entrada), round(janela['inicio'], 3),
                round(janela['fim'], 3), MODELO, idioma, termos) + '.json')
        dados = transcription.ler_json(cache) if cache else None
        if dados and dados.get('versao') == 1 and isinstance(dados.get('segmentos'), list):
            tempos['amostras_do_cache'] += 1
        else:
            if modelo is None:
                t = time.monotonic()
                modelo = carregar_modelo()
                tempos['carregamento_whisper'] = time.monotonic()-t
            dados = _transcrever_amostra(modelo, fonte, janela, Path(pasta_temp) / f"amostra_{indice}.wav",
                                         execucao, termos, tempos, idioma)
            execucao.verificar()
            if cache:
                transcription.salvar_json(cache, dados)
        offset = janela['inicio']
        grupo = []
        for seg in dados['segmentos']:
            # Índice da amostra acompanha cada segmento, para legendas sem duplicação.
            item = {'id': f's{len(segmentos)+1:06d}', 'start': offset+seg['start'], 'end': offset+seg['end'],
                    'text': seg['text'], 'amostra': indice}
            segmentos.append(item)
            grupo.append(item)
            palavras.extend({'start': offset+p['start'], 'end': offset+p['end'], 'word': p['word'], 'amostra': indice}
                            for p in seg['palavras'])
        grupos.append(grupo)
        registrar({'tempos_hibrido': tempos, 'amostras_transcritas': indice+1})
    execucao.verificar()
    return {'duracao': mapa['duracao'], 'segmentos': segmentos, 'palavras': palavras,
            'janelas_amostradas': grupos}, tempos
