"""Troca automática de perfil do Podcast, plano a plano, sem detecção de rosto.

Podcasts com várias câmeras repetem sempre os mesmos ângulos. O usuário marca no editor um
quadro do plano aberto (obrigatório) e um de close como referências; cada plano do corte é
comparado com elas por uma miniatura e segue a mais parecida. Só com o aberto, parecido com ele
usa o perfil 1 e diferente usa o 2. Perfil 1: tela dividida; perfil 2: corte único.
"""
import base64
import re

#: Miniatura usada na comparação (largura, altura). O editor gera a referência no mesmo tamanho.
LARGURA_ASSINATURA, ALTURA_ASSINATURA = 48, 27
TAMANHO_ASSINATURA = LARGURA_ASSINATURA * ALTURA_ASSINATURA * 3
#: scdet (0 a 100): mudança entre quadros que conta como troca de plano.
LIMIAR_TROCA = 10
#: Trocas mais próximas que isso (segundos) são ignoradas: cortes rápidos viram um plano só.
PLANO_MINIMO = .6
#: Distância média por canal (0 a 255) abaixo da qual o plano é o mesmo ângulo da referência.
#: Medido em 48 planos reais: planos abertos ficaram entre 1 e 22, closes entre 52 e 57.
LIMIAR_PLANO_ABERTO = 30


#: Trechos mais curtos que isso (s) seguem o perfil vizinho: a tela dividida não "pisca".
TRECHO_MINIMO = 1.5


def absorver_curtos(segmentos, minimo=TRECHO_MINIMO):
    """Junta cada trecho curto ao vizinho, do mais curto ao mais longo, até não sobrar nenhum.

    Entre dois vizinhos do mesmo perfil, os três viram um trecho só; na ponta do corte, segue o
    único vizinho; entre perfis diferentes, segue o vizinho mais longo.
    """
    segmentos = [list(s) for s in segmentos]
    while len(segmentos) > 1:
        curtos = [i for i, (inicio, fim, _) in enumerate(segmentos) if fim - inicio < minimo]
        if not curtos:
            break
        i = min(curtos, key=lambda k: segmentos[k][1] - segmentos[k][0])
        vizinhos = [k for k in (i - 1, i + 1) if 0 <= k < len(segmentos)]
        alvo = max(vizinhos, key=lambda k: segmentos[k][1] - segmentos[k][0])
        segmentos[i][2] = segmentos[alvo][2]
        juntos = []
        for segmento in segmentos:
            if juntos and juntos[-1][2] == segmento[2]:
                juntos[-1][1] = segmento[1]
            else:
                juntos.append(segmento)
        segmentos = juntos
    return [tuple(s) for s in segmentos]


def modo_automatico(config):
    return (bool(config.get('modo_estudio_ativo')) and config.get('layout_estudio') == 'podcast'
            and config.get('perfil_podcast') == 'automatico')


#: Campo de cada referência no enquadramento.
REFERENCIAS = {'dividido': 'referencia_plano_aberto', 'centralizado': 'referencia_close'}


def referencia(config, campo='referencia_plano_aberto'):
    """Assinatura salva no enquadramento, ou None se não houver uma válida."""
    try:
        dados = base64.b64decode(config.get(campo) or '', validate=True)
    except (ValueError, TypeError):
        return None
    return dados if len(dados) == TAMANHO_ASSINATURA else None


def referencias_do_video(config, origem):
    """(config, descartadas): sem as referências se elas foram marcadas no preview de outro vídeo.

    Cada podcast tem seus ângulos; a referência de um compararia errado os planos de outro.
    Configurações sem origem (anteriores a ela) seguem valendo.
    """
    marcada = config.get('referencia_origem')
    if not marcada or marcada == origem or not any(config.get(c) for c in REFERENCIAS.values()):
        return config, False
    limpas = {c: None for c in (*REFERENCIAS.values(), 'referencia_miniatura', 'referencia_close_miniatura')}
    return {**config, **limpas, 'referencia_origem': None}, True


def distancia(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def classificar(assinatura_plano, referencias):
    """Perfil de um plano pelas referências ({perfil: assinatura}), ou perfil 1 sem quadro para comparar."""
    if assinatura_plano is None:
        return 'dividido'
    distancias = {perfil: distancia(ref, assinatura_plano) for perfil, ref in referencias.items()}
    if len(distancias) > 1:
        return min(distancias, key=distancias.get)
    (perfil, valor), = distancias.items()
    outro = 'centralizado' if perfil == 'dividido' else 'dividido'
    return perfil if valor < LIMIAR_PLANO_ABERTO else outro


def trocas(video, executar):
    """Instantes (s) em que a imagem muda de plano."""
    resultado = executar(['ffmpeg', '-hide_banner', '-nostats', '-i', str(video), '-an',
                          '-vf', f'scale=320:-2,scdet=threshold={LIMIAR_TROCA}', '-f', 'null', '-'])
    if resultado.returncode != 0:
        return []
    texto = resultado.stderr if isinstance(resultado.stderr, str) else resultado.stderr.decode('utf-8', 'replace')
    return sorted(float(t) for t in re.findall(r'lavfi\.scd\.time:\s*([\d.]+)', texto))


def assinatura(video, instante, executar):
    resultado = executar(['ffmpeg', '-v', 'error', '-ss', f'{instante:.3f}', '-i', str(video), '-frames:v', '1',
                          '-vf', f'scale={LARGURA_ASSINATURA}:{ALTURA_ASSINATURA}:flags=area',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], binario=True)
    dados = resultado.stdout if resultado.returncode == 0 else b''
    return dados if len(dados) == TAMANHO_ASSINATURA else None


def segmentos(config, video, duracao, executar):
    """[(início, fim, perfil)] do corte no modo automático, com planos vizinhos do mesmo perfil juntos.

    ``executar(comando, binario=False)`` roda o FFmpeg e devolve o CompletedProcess. Retorna None
    fora do modo automático ou sem a referência do plano aberto: o corte segue com o perfil 1 inteiro.
    """
    referencias = {perfil: ref for perfil, campo in REFERENCIAS.items()
                   if (ref := referencia(config, campo)) is not None} if modo_automatico(config) else {}
    # O plano aberto é obrigatório: um close sozinho só reconhece os closes com o mesmo fundo, e os
    # das outras câmeras viram tela dividida (medido num VOD real: 313 s de 2568 s errados, contra
    # nenhum erro com as duas referências).
    if 'dividido' not in referencias or duracao <= 0:
        return None
    cortes = [0.0]
    for instante in trocas(video, executar):
        if instante - cortes[-1] >= PLANO_MINIMO and duracao - instante >= PLANO_MINIMO:
            cortes.append(instante)
    resultado = []
    for inicio, fim in zip(cortes, cortes[1:] + [duracao]):
        # Sem quadro para comparar, fica no perfil 1, que mostra a cena inteira.
        perfil = classificar(assinatura(video, (inicio + fim) / 2, executar), referencias)
        if resultado and resultado[-1][2] == perfil:
            resultado[-1] = (resultado[-1][0], fim, perfil)
        else:
            resultado.append((inicio, fim, perfil))
    return absorver_curtos(resultado)
