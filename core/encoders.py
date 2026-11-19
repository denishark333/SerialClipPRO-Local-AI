"""Codificação final compartilhada pelo pipeline e pela revisão.

Os encoders de hardware são tentados em ordem. Quando um deles falha e o
seguinte funciona com o mesmo comando, a falha é atribuída ao encoder e ele é
pulado nos próximos cortes desta sessão. Se todos falham, o problema está no
comando (filtros, entrada) e nenhum encoder é marcado.
"""
import threading

ENCODERS = (
    ('NVIDIA NVENC', ['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '20']),
    ('AMD AMF', ['-c:v', 'h264_amf', '-quality', 'balanced', '-rc', 'cqp', '-qp_i', '20', '-qp_p', '20']),
    ('CPU libx264', ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23']),
)

#: -14 LUFS integrado e -1,5 dBTP: o alvo para o qual as plataformas normalizam.
#: Entregar o corte já nesse nível evita que elas alterem o volume.
ARGS_AUDIO = ['-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000']

_lock = threading.Lock()
_indisponiveis = set()


def codecs_renderizacao():
    """Encoders na ordem de preferência, sem os que já falharam nesta sessão."""
    with _lock:
        return tuple((nome, codec) for nome, codec in ENCODERS if nome not in _indisponiveis)


def redefinir():
    """Esquece as falhas registradas. Usado pelos testes."""
    with _lock:
        _indisponiveis.clear()


def renderizar(montar, executar, rotulo, ao_tentar=None):
    """Tenta cada encoder disponível até um funcionar.

    montar(codec_args) devolve o comando completo; executar(comando) devolve um
    CompletedProcess. Retorna (nome_do_encoder, resultado), com nome None quando
    todos falharam.
    """
    falharam = []
    resultado = None
    for nome, codec in codecs_renderizacao():
        if ao_tentar:
            ao_tentar(nome)
        print(f'{rotulo}: tentando {nome}...', flush=True)
        resultado = executar(montar(codec))
        if resultado.returncode == 0:
            if falharam:
                with _lock:
                    _indisponiveis.update(falharam)
                print(f'{rotulo}: {", ".join(falharam)} indisponível nesta máquina; '
                      'será pulado nos próximos cortes.', flush=True)
            print(f'{rotulo}: codificado com {nome}.', flush=True)
            return nome, resultado
        falharam.append(nome)
        print(f'{rotulo}: {nome} falhou: {_texto(resultado.stderr)[-500:]}', flush=True)
    return None, resultado


def _texto(saida):
    if isinstance(saida, bytes):
        return saida.decode(errors='replace')
    return saida or ''
