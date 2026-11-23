"""Diagnóstico técnico da curadoria, separado das notas editoriais."""
import httpx
import ollama
from core.textos import tr


def verificar_ollama(execucao, modelo=None):
    """Consulta servidor/modelo sem baixar nem carregar pesos para inferência."""
    from core.ia import modelo as modelo_configurado
    modelo = modelo or modelo_configurado()
    execucao.verificar()
    try:
        with ollama.Client(timeout=5, trust_env=False) as cliente:
            cliente.show(modelo)
    except ollama.ResponseError as erro:
        execucao.verificar()
        if erro.status_code == 404:
            raise RuntimeError(tr('ollama.modelo_ausente', modelo=modelo)) from erro
        raise RuntimeError(tr('ollama.recusou', erro=erro)) from erro
    except (ConnectionError, httpx.HTTPError) as erro:
        execucao.verificar()
        raise RuntimeError(tr('ollama.offline')) from erro
    execucao.verificar()


def tipo_falha(erro):
    if isinstance(erro, (ConnectionError, httpx.HTTPError, ollama.ResponseError)):
        return 'falha_ollama'
    if isinstance(erro, (ValueError, KeyError, TypeError)):
        return 'resposta_invalida'
    return 'erro_analise'


def resumir_curadoria(relatorio):
    janelas = relatorio['janelas']
    analisadas = sum(j['estado'] == 'analisado' for j in janelas)
    suspensas = sum(j.get('tipo_erro') == 'analise_suspensa' for j in janelas)
    falhas = len(janelas) - analisadas
    invalidas = sum(j.get('tipo_erro') == 'resposta_invalida' for j in janelas)
    decisoes_invalidas = sum(d.get('validacao') != 'valido'
                            for j in janelas for d in j.get('decisoes', []))
    descartes = dict(abaixo_minimo=0, acima_maximo=0, ids_inexistentes=0, ordem_invalida=0, nao_detalhado=0)
    for j in janelas:
        for d in j.get('decisoes', []):
            if d.get('validacao') != 'valido':
                causa = d.get('motivo_descarte', 'nao_detalhado')
                descartes[causa if causa in descartes else 'nao_detalhado'] += 1
    selecionados = relatorio.get('selecionados', [])
    sugestoes = sum(c.get('avaliacao') == 'sugestao' for c in selecionados)
    # Só blocos sem avaliação tornam a curadoria parcial. Um momento descartado
    # (curto demais, IDs errados) é a validação funcionando, não uma falha.
    situacao = ('sem_fala' if not janelas else 'nao_avaliada' if not analisadas
                else 'parcial' if falhas else 'completa')
    if situacao == 'nao_avaliada':
        mensagem = tr('curadoria.nao_avaliada')
    elif situacao == 'parcial':
        mensagem = tr('curadoria.parcial', falhas=falhas, total=len(janelas))
    elif situacao == 'sem_fala':
        mensagem = tr('curadoria.sem_fala')
    elif sugestoes:
        mensagem = tr('curadoria.so_sugestoes')
    else:
        mensagem = tr('curadoria.completa')
    if sugestoes and situacao in ('parcial', 'nao_avaliada'):
        mensagem += tr('curadoria.sugestoes_sem_aprovacao')
    if decisoes_invalidas:
        mensagem += (tr('curadoria.um_descartado') if decisoes_invalidas == 1
                     else tr('curadoria.varios_descartados', total=decisoes_invalidas))
    return dict(situacao=situacao, mensagem=mensagem, janelas=len(janelas),
                analisadas=analisadas, falhas_analise=falhas, suspensas=suspensas,
                falhas_tentadas=falhas-suspensas, respostas_invalidas=invalidas,
                decisoes_invalidas=decisoes_invalidas, selecionados=len(selecionados),
                sugestoes=sugestoes, descartes=descartes)


def mensagem_conclusao(resumo, tempo):
    if resumo and resumo.get('falhas_analise', 0):
        return tr('status.concluido_limitacoes', tempo=tempo)
    if resumo and resumo.get('sugestoes', 0):
        return tr('status.concluido_sugestoes', tempo=tempo)
    return tr('status.concluido', tempo=tempo)
