"""Ajuste dos limites de um corte a frases completas e pausas da fala.

A curadoria aponta um intervalo aproximado. Para o corte soar intencional:

1. **Frases completas**: o início vai para o começo da frase mais próxima e o
   fim para o final da frase mais próxima, para nunca abrir ou fechar no meio
   de um pensamento.
2. **Duração**: o fim recua ou avança até a duração ficar entre o mínimo e o
   máximo, sempre parando num final de frase quando possível.
3. **Pausas**: as bordas caem dentro da pausa antes da primeira palavra e
   depois da última, em vez de um recuo fixo que corta respirações.

As pausas vêm dos intervalos entre as palavras do Whisper. Quando não há pausa
mensurável perto da borda, usa-se uma folga fixa pequena.

Adaptado de autoclip/pipeline/boundaries.py (AutoClip, MIT, Jad Ghazi). Veja
THIRD_PARTY_LICENSES.md.
"""
import math
import re

#: Termina frase: ponto, exclamação, interrogação ou reticências, seguidos ou
#: não de aspas e parênteses de fechamento.
FIM_DE_FRASE = re.compile(r"[.!?…]+[\"'”’)\]]*$")

#: Quantas palavras para cada lado da sugestão procuramos uma borda de frase.
BUSCA_PALAVRAS = 12

#: Intervalo mínimo entre palavras para contar como pausa.
PAUSA_MINIMA = 0.20

#: Folga usada quando não há pausa mensurável perto da borda.
FOLGA_INICIO = 0.25
FOLGA_FIM = 0.35

#: Distância máxima entre a borda e a pausa usada para alinhá-la.
RAIO_PAUSA = 0.75
#: Quanto da pausa antes da primeira palavra entra no corte (pega a respiração
#: sem deixar um silêncio morto no começo).
ENTRADA_PAUSA = 0.12
#: Quanto tempo segurar depois da última palavra.
SAIDA_PAUSA = 0.28
#: Nunca cortar rente à borda da pausa.
MARGEM_PAUSA = 0.04


def termina_frase(palavra):
    return bool(FIM_DE_FRASE.search(palavra['word'].strip()))


def pausas(palavras):
    """Intervalos (início, fim) de silêncio entre palavras consecutivas."""
    return [(a['end'], b['start']) for a, b in zip(palavras, palavras[1:])
            if b['start'] - a['end'] >= PAUSA_MINIMA]


def refinar(palavras, inicio, fim, minimo=15.0, maximo=90.0):
    """Ajusta (inicio, fim) às frases e pausas de ``palavras``.

    ``palavras`` deve estar em ordem e pertencer a um trecho contínuo de fala.
    Retorna o novo (inicio, fim) ou None quando nenhum ajuste respeita a
    duração; nesse caso, quem chama mantém o intervalo original.
    """
    palavras = [p for p in palavras if _valida(p)]
    if not palavras:
        return None
    dentro = [i for i, p in enumerate(palavras) if p['end'] > inicio and p['start'] < fim]
    if not dentro:
        return None

    primeira = _ajustar_inicio(palavras, dentro[0])
    ultima = _ajustar_fim(palavras, dentro[-1])
    if ultima <= primeira:
        return None
    ultima = _limitar_duracao(palavras, primeira, ultima, minimo, maximo)
    if ultima is None:
        return None

    silencios = pausas(palavras)
    novo_inicio = _alinhar_inicio(palavras[primeira]['start'], silencios)
    novo_fim = _alinhar_fim(palavras[ultima]['end'], silencios)
    # O alinhamento só alarga o corte; o teto continua valendo.
    novo_fim = min(novo_fim, novo_inicio + maximo)
    return max(0.0, novo_inicio), novo_fim


def _valida(palavra):
    try:
        inicio, fim = float(palavra['start']), float(palavra['end'])
    except (KeyError, TypeError, ValueError):
        return False
    return math.isfinite(inicio) and math.isfinite(fim) and fim > inicio and palavra.get('word', '').strip()


def _ajustar_inicio(palavras, indice):
    """Primeira palavra da frase mais próxima. Empates preferem recuar."""
    for deslocamento in range(BUSCA_PALAVRAS + 1):
        for candidato in (indice - deslocamento, indice + deslocamento):
            if candidato <= 0:
                return 0
            if candidato < len(palavras) and termina_frase(palavras[candidato - 1]):
                return candidato
    return indice


def _ajustar_fim(palavras, indice):
    """Última palavra da frase mais próxima. Empates preferem avançar."""
    ultimo = len(palavras) - 1
    for deslocamento in range(BUSCA_PALAVRAS + 1):
        for candidato in (indice + deslocamento, indice - deslocamento):
            if candidato >= ultimo:
                return ultimo
            if candidato >= 0 and termina_frase(palavras[candidato]):
                return candidato
    return indice


def _limitar_duracao(palavras, primeira, ultima, minimo, maximo):
    inicio = palavras[primeira]['start']

    def duracao(i):
        return palavras[i]['end'] - inicio

    if duracao(ultima) > maximo:
        cabem = [i for i in range(ultima, primeira, -1) if duracao(i) <= maximo]
        if not cabem:
            return None
        frases = [i for i in cabem if termina_frase(palavras[i])]
        ultima = frases[0] if frases else cabem[0]

    if duracao(ultima) < minimo:
        for candidato in range(ultima + 1, len(palavras)):
            if duracao(candidato) > maximo:
                break
            if termina_frase(palavras[candidato]):
                ultima = candidato
                if duracao(ultima) >= minimo:
                    break

    return ultima if minimo <= duracao(ultima) <= maximo else None


def _alinhar_inicio(inicio, silencios):
    perto = [s for s in silencios if abs(s[1] - inicio) <= RAIO_PAUSA]
    if not perto:
        return max(0.0, inicio - FOLGA_INICIO)
    comeco, termino = min(perto, key=lambda s: abs(s[1] - inicio))
    mais_cedo = min(comeco + MARGEM_PAUSA, termino)
    return max(mais_cedo, min(termino - ENTRADA_PAUSA, inicio))


def _alinhar_fim(fim, silencios):
    perto = [s for s in silencios if abs(s[0] - fim) <= RAIO_PAUSA]
    if not perto:
        return fim + FOLGA_FIM
    comeco, termino = min(perto, key=lambda s: abs(s[0] - fim))
    mais_tarde = max(termino - MARGEM_PAUSA, comeco)
    return max(fim, min(comeco + SAIDA_PAUSA, mais_tarde))
