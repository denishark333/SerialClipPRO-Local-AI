"""Diagnóstico técnico da curadoria, separado das notas editoriais."""
import httpx
import ollama


def verificar_ollama(execucao):
    """Consulta servidor/modelo sem baixar nem carregar pesos para inferência."""
    execucao.verificar()
    try:
        with ollama.Client(timeout=5, trust_env=False) as cliente:
            cliente.show('llama3.1')
    except ollama.ResponseError as erro:
        execucao.verificar()
        if erro.status_code == 404:
            raise RuntimeError('Modelo llama3.1 não encontrado no Ollama. Prepare as dependências antes de iniciar.') from erro
        raise RuntimeError(f'Ollama recusou a verificação do modelo: {erro}') from erro
    except (ConnectionError, httpx.HTTPError) as erro:
        execucao.verificar()
        raise RuntimeError('Ollama não respondeu. Abra o Ollama e verifique as dependências antes de iniciar novamente.') from erro
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
    situacao = ('sem_fala' if not janelas else 'nao_avaliada' if not analisadas
                else 'parcial' if falhas or decisoes_invalidas else 'completa')
    if situacao == 'nao_avaliada':
        mensagem = 'Curadoria não concluída: nenhum bloco recebeu avaliação válida da IA. Consulte o relatório.'
    elif situacao == 'parcial':
        mensagem = (f'Curadoria parcial: {falhas} de {len(janelas)} blocos não foram avaliados.' if falhas
                    else f'Blocos avaliados: {analisadas}/{len(janelas)}. Sem falhas de chamada.')
        if decisoes_invalidas:
            mensagem += f' Decisões descartadas por intervalos inválidos: {decisoes_invalidas}.'
    elif situacao == 'sem_fala':
        mensagem = 'Nenhum segmento de fala disponível para curadoria.'
    elif sugestoes:
        mensagem = 'A IA avaliou os blocos, mas não selecionou candidatos; os cortes são sugestões para revisão.'
    else:
        mensagem = 'Curadoria concluída. Revise os cortes selecionados antes de publicar.'
    if sugestoes and situacao in ('parcial', 'nao_avaliada'):
        mensagem += ' Os cortes são sugestões automáticas, sem aprovação da IA.'
    return dict(situacao=situacao, mensagem=mensagem, janelas=len(janelas),
                analisadas=analisadas, falhas_analise=falhas, suspensas=suspensas,
                falhas_tentadas=falhas-suspensas, respostas_invalidas=invalidas,
                decisoes_invalidas=decisoes_invalidas, selecionados=len(selecionados),
                sugestoes=sugestoes, descartes=descartes)


def mensagem_conclusao(resumo, tempo):
    if resumo and not resumo.get('falhas_analise', 0) and resumo.get('decisoes_invalidas', 0):
        return f'Processamento concluído; intervalos inválidos descartados. ({tempo})'
    if resumo and (resumo.get('falhas_analise', 0) or resumo.get('decisoes_invalidas', 0)):
        return f'Processamento concluído com limitações na curadoria. ({tempo})'
    if resumo and resumo.get('sugestoes', 0):
        return f'Processamento concluído com sugestões para revisão. ({tempo})'
    return f'Pipeline Concluído com Sucesso! ({tempo})'
