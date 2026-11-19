"""Contexto sob demanda com orçamento explícito de áudio, sem cache integral."""
import math
from pathlib import Path
import subprocess
import time
import wave

from core.whisper import carregar_modelo, dispositivo
from core.audio import detectar_segmentos_narrativos
from core.config import atualizar_estado
from core.execution import executar_comando


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


def transcrever_hibrido(fonte, pasta_temp, execucao, termos, ignorar_inicio, limite, registrar):
    tempos = {}
    atualizar_estado("Híbrido: mapeando áudio para escolher amostras...", 2, 15)
    t = time.monotonic()
    mapa = detectar_segmentos_narrativos(fonte, execucao=execucao, ignorar_inicio_segundos=ignorar_inicio, retornar_detalhes=True)
    tempos['varredura_audio'] = time.monotonic()-t
    plano = planejar_janelas(mapa['picos'], mapa['duracao'], limite, ignorar_inicio)
    if not plano:
        raise ValueError("Não foi possível determinar trechos para amostragem.")
    registrar({'amostragem': plano, 'orcamento_trechos': limite,
               'segundos_audio_planejados': sum(j['fim']-j['inicio'] for j in plano), 'tempos_hibrido': tempos})
    execucao.verificar()
    t = time.monotonic()
    modelo = carregar_modelo()
    tempos['carregamento_whisper'] = time.monotonic()-t
    tempos.update(extracao_audio_trechos=0., transcricao_trechos=0.)
    segmentos, palavras, grupos = [], [], []
    for indice, janela in enumerate(plano):
        execucao.verificar()
        atualizar_estado(f"Híbrido: transcrevendo amostra {indice+1}/{len(plano)} ({dispositivo()})...", 2, 16+int(18*indice/len(plano)))
        arquivo = Path(pasta_temp) / f"amostra_{indice}.wav"
        t = time.monotonic()
        res = executar_comando([
            'ffmpeg', '-y', '-ss', str(janela['inicio']), '-i', fonte,
            '-t', str(janela['fim']-janela['inicio']), '-vn', '-map', '0:a:0',
            '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(arquivo),
        ], execucao=execucao, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tempos['extracao_audio_trechos'] += time.monotonic()-t
        if res.returncode:
            raise RuntimeError('Falha ao extrair amostra: '+res.stderr.decode(errors='replace')[-1500:])
        with wave.open(str(arquivo), 'rb') as wav:
            duracao = wav.getnframes()/wav.getframerate()
        t = time.monotonic()
        iterator, _ = modelo.transcribe(str(arquivo), language='pt', word_timestamps=True,
                                       beam_size=5, vad_filter=True, hotwords=termos or None)
        grupo = []
        for seg in iterator:
            execucao.verificar()
            a, b = max(0., float(seg.start)), min(duracao, float(seg.end))
            if not math.isfinite(a) or not math.isfinite(b) or b <= a or not seg.text.strip():
                continue
            offset = janela['inicio']
            item = {'id': f's{len(segmentos)+1:06d}', 'start': offset+a, 'end': offset+b, 'text': seg.text.strip()}
            segmentos.append(item)
            grupo.append(item)
            for w in seg.words or []:
                st, et = max(a, float(w.start)), min(b, float(w.end))
                if math.isfinite(st) and math.isfinite(et) and et > st and w.word.strip():
                    palavras.append({'start': offset+st, 'end': offset+et, 'word': w.word.strip(), 'amostra': indice})
        tempos['transcricao_trechos'] += time.monotonic()-t
        # Índice da amostra acompanha cada segmento, para legendas sem duplicação.
        for item in grupo:
            item['amostra'] = indice
        grupos.append(grupo)
        arquivo.unlink()
        registrar({'tempos_hibrido': tempos, 'amostras_transcritas': indice+1})
    execucao.verificar()
    return {'duracao': mapa['duracao'], 'segmentos': segmentos, 'palavras': palavras,
            'janelas_amostradas': grupos}, tempos
