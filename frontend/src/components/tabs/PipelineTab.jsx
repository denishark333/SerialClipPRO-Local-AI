import { useDialog } from '../layout/useDialog';
import React, { useEffect } from 'react';
import { apiFetch, MEDIA_BASE_URL, API_BASE_URL } from '../../api';
import { StudioCropper } from '../studio/StudioCropper';
import { clipIdentity } from '../../clipIdentity';
import { useI18n } from '../../i18n/useI18n';
import { IDIOMAS as IDIOMAS_INTERFACE, traduzir } from '../../i18n/traduzir';

// Idiomas que o Whisper reconhece na live; os nomes ficam em pipeline.idiomasLive.*.
const IDIOMAS_LIVE = ['pt', 'en', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'auto'];

// Pontos de partida editáveis (pipeline.presets.*). A IA recebe o texto como prioridade, não como molde.
const PRESETS = ['nenhum', 'mmorpg', 'fps', 'chatting', 'podcast'];

// O foco fica salvo entre execuções e pode ter sido escrito no outro idioma da interface.
function presetDoFoco(foco) {
  return PRESETS.find(chave => IDIOMAS_INTERFACE.some(({ id }) => traduzir(id, `pipeline.presets.${chave}.texto`) === foco))
    ?? 'personalizado';
}

export function PipelineTab({
  abrirRevisao,
  modoInput, setModoInput,
  entrada, setEntrada,
  maxCortes, setMaxCortes, ignorarInicio, setIgnorarInicio,
  modoCuradoria, setModoCuradoria, termosJogo, setTermosJogo, detalhesClips = {},
  idioma, setIdioma, foco, setFoco,
  limiteAmostras, setLimiteAmostras,
  carregando, iniciarGeracao,
  statusInfo,
  selecionados, toggleCheckbox, exportarSelecionados,
  selecionarTodos, limparSelecao,
  deletarSelecionados
}) {
  const { notify } = useDialog();
  const { t } = useI18n();
  const presetAtual = presetDoFoco(foco);
  const resumoAvancado = [
    idioma !== 'pt' && t(`pipeline.idiomaCurto.${idioma}`),
    foco.trim() && (presetAtual === 'personalizado' ? t('pipeline.resumo.focoPersonalizado')
      : t('pipeline.resumo.foco', { nome: t(`pipeline.presets.${presetAtual}.rotulo`) })),
    termosJogo.trim() && t('pipeline.resumo.termos'),
    Number(ignorarInicio) > 0 && t('pipeline.resumo.abertura', { segundos: Number(ignorarInicio) }),
  ].filter(Boolean).join(' · ');
  const [carregandoPreview, setCarregandoPreview] = React.useState(false);
  // Modelo da curadoria em uso (escolhido em Primeiros Passos); a aba é remontada ao voltar para ela.
  const [modeloIA, setModeloIA] = React.useState('');
  useEffect(() => {
    let ativo = true;
    apiFetch('/ia').then(r => r.json()).then(dados => {
      if (!ativo) return;
      const instalado = dados.instalados?.find(m => m.id === dados.modelo_id);
      setModeloIA(instalado?.nome || dados.modelo);
    }).catch(() => { /* backend fora do ar: o card fica com o traço */ });
    return () => { ativo = false; };
  }, []);
  const [previewPronto, setPreviewPronto] = React.useState(0);
  const [selecionandoArquivo, setSelecionandoArquivo] = React.useState(false);
  const entradas = React.useRef({ arquivo: '', url: '' });
  function trocarModo(modo) {
    if (modo === modoInput) return;
    entradas.current[modoInput] = entrada;
    setEntrada(entradas.current[modo]);
    setModoInput(modo);
  }
  async function selecionarArquivo() {
    if (selecionandoArquivo) return;
    setSelecionandoArquivo(true);
    try {
      const resultado = window.pywebview?.api?.selecionar_video
        ? await window.pywebview.api.selecionar_video()
        : await (await apiFetch('/selecionar-video', { method: 'POST' })).json();
      if (resultado.caminho) setEntrada(resultado.caminho);
    } catch (erro) {
      notify(t('pipeline.erroSelecionar', { erro: erro.message }));
    } finally {
      setSelecionandoArquivo(false);
    }
  }
  const quantidadeSelecionada = statusInfo.videos.filter(url => selecionados[url]).length;
  // Função para lidar com a paragem forçada do pipeline
  const pararPipeline = async () => {
    try {
      const res = await apiFetch('/stop-pipeline', {
        method: 'POST',
      });
      if (res.ok) {
        console.log("Cancelamento solicitado.");
        // O polling acompanha o encerramento real da execução.
      }
    } catch (err) {
      notify(t('pipeline.erroCancelar', { erro: err.message }));
    }
  };

  // 🚀 Disparador automático do Preview com sincronização de estado e cache-buster
  useEffect(() => {
    if (!entrada.trim()) return;

    const timer = setTimeout(async () => {
      try {
        setCarregandoPreview(true);
        setPreviewPronto(0);
        console.log("🎬 A solicitar preview antecipado para a URL:", entrada);
        
        const response = await apiFetch('/gerar-preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ entrada })
        });

        if (response.ok) {
          console.log("Preview solicitado; aguardando processamento.");
          setPreviewPronto(Date.now());
        }
      } catch (err) {
        console.error("Erro ao disparar o preview em background:", err);
      } finally {
        setCarregandoPreview(false);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [entrada, modoInput]);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.12fr)_minmax(0,1fr)_minmax(0,1.2fr)] gap-3 items-start">
        
        {/* 1. CONFIGURAÇÕES */}
        <div className="min-w-0 bg-[#0a0712] border border-[#1b1528] p-5 rounded-2xl shadow-xl flex flex-col justify-between relative overflow-hidden">
          <div>
            <div className="flex justify-between items-center border-b border-[#1b1528] pb-3 mb-4">
              <h2 className="text-base font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                <span className="text-[#9333ea]">⚙️</span> {t('pipeline.configuracoes')}
              </h2>
              <div className="flex gap-1 bg-[#05070b] p-1 rounded-lg border border-[#1b1528]">
                <button 
                  disabled={selecionandoArquivo} onClick={() => trocarModo('arquivo')}
                  className={`px-2 py-1 rounded-md text-[12px] font-medium transition-all ${modoInput === 'arquivo' ? 'bg-[#9333ea] text-white font-bold' : 'text-slate-400 hover:text-white'}`}
                >
                  📁 {t('pipeline.arquivo')}
                </button>
                <button 
                  disabled={selecionandoArquivo} onClick={() => trocarModo('url')}
                  className={`px-2 py-1 rounded-md text-[12px] font-medium transition-all ${modoInput === 'url' ? 'bg-[#9333ea] text-white font-bold' : 'text-slate-400 hover:text-white'}`}
                >
                  🌐 {t('pipeline.link')}
                </button>
              </div>
            </div>
            
            {modoInput === 'arquivo' ? (
              <div className="flex flex-col gap-2 mb-4 relative">
                <div className="flex justify-between items-center">
                  <label className="text-sm text-slate-400 font-medium">{t('pipeline.videoComputador')}</label>
                  {entrada && (
                    <div className="flex items-center gap-1 bg-[#b3ff33]/10 border border-[#b3ff33]/30 px-2 py-0.5 rounded-full" title={t('pipeline.caminhoInformado')}>
                      <span className="w-3.5 h-3.5 rounded-full bg-[#b3ff33] flex items-center justify-center text-black text-[9px] font-bold">✓</span>
                      <span className="text-[9px] font-mono text-[#b3ff33]">{t('pipeline.informado')}</span>
                    </div>
                  )}
                </div>
                <button type="button" onClick={selecionarArquivo} disabled={selecionandoArquivo}
                  title={entrada || t('pipeline.selecionarNoComputador')}
                  className="w-full min-w-0 bg-[#0e0a1a] border border-purple-500/60 rounded-xl p-3 text-sm text-left text-white hover:bg-purple-950 focus-visible:outline-2 focus-visible:outline-cyan-400 disabled:opacity-50">
                  <span className="block font-semibold text-cyan-200">📁 {selecionandoArquivo ? t('pipeline.aguardandoSelecao') : entrada ? t('pipeline.trocarVideo') : t('pipeline.selecionarVideo')}</span>
                  {entrada && <span className="mt-1 block truncate text-xs text-slate-300">{entrada}</span>}
                </button>
                <span className="text-sm text-slate-400">{t('pipeline.dicaArquivo')}</span>
              </div>
            ) : (
              <div className="flex flex-col gap-2 mb-4 relative">
                <div className="flex justify-between items-center">
                  <label className="text-sm text-slate-400 font-medium flex items-center gap-1.5">
                    {t('pipeline.urlTransmissao')}
                    {carregandoPreview && <span className="text-[10px] font-mono text-amber-400 animate-pulse">({t('pipeline.carregandoPreview')})</span>}
                  </label>
                  {entrada && !carregandoPreview && (
                    <div className="flex items-center gap-1 bg-[#b3ff33]/10 border border-[#b3ff33]/30 px-2 py-0.5 rounded-full" title={t('pipeline.urlInformada')}>
                      <span className="w-3.5 h-3.5 rounded-full bg-[#b3ff33] flex items-center justify-center text-black text-[9px] font-bold">✓</span>
                      <span className="text-[9px] font-mono text-[#b3ff33]">{t('pipeline.informada')}</span>
                    </div>
                  )}
                </div>
                <input 
                  type="text" 
                  value={entrada} 
                  onChange={(e) => setEntrada(e.target.value)}
                  placeholder="https://www.twitch.tv/videos/..."
                  className="w-full bg-[#0e0a1a] border border-[#1f1633] rounded-xl p-3 text-xs text-white focus:outline-none focus:border-[#9333ea]"
                />
                <p className="text-xs text-slate-500 mt-1.5">{t('pipeline.dicaUrl')}</p>
              </div>
            )}

            <div className="flex flex-col gap-2 mb-4">
              <div className="flex flex-wrap justify-between items-center gap-2 text-xs">
                <label htmlFor="limite-cortes" className="text-slate-400 font-medium text-sm">{t('pipeline.limiteCortes')}</label>
                <span className="font-mono text-[#b3ff33] font-bold whitespace-nowrap">{t('pipeline.ateCortes', { total: maxCortes })}</span>
              </div>
              <input 
                type="range" 
                id="limite-cortes"
                min="1" 
                max="50" 
                value={maxCortes} 
                onChange={(e) => setMaxCortes(e.target.value)}
                className="accent-[#b3ff33] cursor-pointer bg-[#0e0a1a]"
              />
            </div>
          </div>

          <label className="text-sm text-slate-400 mb-3 flex flex-col gap-1">
            {t('pipeline.selecaoCortes')}
            <select value={modoCuradoria} onChange={e => setModoCuradoria(e.target.value)} disabled={carregando}
              className="bg-[#0e0a1a] border border-[#1f1633] rounded p-2">
              <option value="hibrido">{t('pipeline.modos.hibrido')}</option>
              <option value="contexto">{t('pipeline.modos.contexto')}</option>
              <option value="picos">{t('pipeline.modos.picos')}</option>
            </select>
            {modoCuradoria === 'contexto' && <span className="text-sm">{t('pipeline.dicaContexto')}</span>}
          </label>
          {modoCuradoria === 'hibrido' && <details className="text-sm text-slate-400 mb-3 border border-[#1f1633] rounded-lg p-3">
            <summary className="cursor-pointer font-medium text-slate-300">{t('pipeline.analiseAvancada')}</summary>
            <label className="mt-3 flex flex-col gap-2">
              {t('pipeline.limiteAmostras')}
              <input type="number" min="10" max="80" value={limiteAmostras} disabled={carregando}
                onChange={e => setLimiteAmostras(e.target.value)} className="bg-[#0e0a1a] border border-[#1f1633] rounded p-2" />
              <span>{t('pipeline.dicaAmostras')}</span>
              <span>{t('pipeline.dicaMinutos', { minutos: Number(limiteAmostras) * 1.5 })}</span>
            </label>
          </details>}
          {/* Idioma e foco ficam salvos entre execuções: o título lembra o que está fora do padrão. */}
          <details className="text-sm text-slate-400 mb-3 border border-[#1f1633] rounded-lg p-3">
            <summary className="cursor-pointer font-medium text-slate-300">
              {t('pipeline.configuracoesAvancadas')}
              {resumoAvancado && <span className="ml-2 text-xs font-normal text-cyan-300/80">· {resumoAvancado}</span>}
            </summary>
            <div className="mt-3 flex flex-col">
          <label className="text-sm text-slate-400 mb-3 flex flex-col gap-1">
            {t('pipeline.idiomaLive')}
            <select value={idioma} onChange={e => setIdioma(e.target.value)} disabled={carregando}
              className="bg-[#0e0a1a] border border-[#1f1633] rounded p-2">
              {IDIOMAS_LIVE.map(codigo => <option key={codigo} value={codigo}>{t(`pipeline.idiomasLive.${codigo}`)}</option>)}
            </select>
            <span>{t('pipeline.dicaIdiomaLive')}</span>
          </label>
          <label className="text-sm text-slate-400 mb-3 flex flex-col gap-1">
            {t('pipeline.oQueProcurar')}
            <select value={presetAtual} disabled={carregando}
              onChange={e => { if (e.target.value !== 'personalizado') setFoco(t(`pipeline.presets.${e.target.value}.texto`)); }}
              className="bg-[#0e0a1a] border border-[#1f1633] rounded p-2">
              {PRESETS.map(chave => <option key={chave} value={chave}>{t(`pipeline.presets.${chave}.rotulo`)}</option>)}
              {presetAtual === 'personalizado' && <option value="personalizado">{t('pipeline.personalizado')}</option>}
            </select>
            <textarea value={foco} onChange={e => setFoco(e.target.value)} maxLength={500} disabled={carregando} rows={2}
              placeholder={t('pipeline.placeholderFoco')}
              className="bg-[#0e0a1a] border border-[#1f1633] rounded p-2" />
            <span>{t('pipeline.dicaFoco')}</span>
          </label>
          <label className="text-sm text-slate-400 mb-3 flex flex-col gap-1">
            {t('pipeline.termos')}
            <input value={termosJogo} onChange={e => setTermosJogo(e.target.value)} maxLength={500} disabled={carregando}
              placeholder={t('pipeline.placeholderTermos')}
              className="bg-[#0e0a1a] border border-[#1f1633] rounded p-2" />
          </label>
          <label className="text-sm text-slate-400 mb-3 flex flex-col gap-1">
            {t('pipeline.ignorarAbertura')}
            <input type="number" min="0" value={ignorarInicio}
              onChange={e => setIgnorarInicio(e.target.value)}
              className="bg-[#0e0a1a] border border-[#1f1633] rounded p-2" />
            <span>{t('pipeline.dicaAbertura')}</span>
          </label>
            </div>
          </details>

          {/* BOTÕES DE CONTROLE: INICIAR E PARAR */}
          <div className="flex flex-col gap-2.5 mt-2">
            <button 
              onClick={iniciarGeracao}
              disabled={carregando}
              className="w-full bg-gradient-to-r from-[#b3ff33] via-[#9333ea] to-[#00ffff] hover:opacity-90 disabled:from-slate-800 disabled:to-slate-800 text-[#05070b] font-black py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(147,51,234,0.3)] flex items-center justify-center gap-2 uppercase text-sm tracking-wider cursor-pointer"
            >
              {carregando ? t('pipeline.processando') : t('pipeline.iniciar')}
            </button>

            <button 
              onClick={pararPipeline}
              disabled={!carregando || statusInfo.cancelando}
              className={`w-full font-bold py-2.5 rounded-xl transition-all uppercase text-xs tracking-wider flex items-center justify-center gap-1.5 ${
                carregando 
                  ? 'bg-gradient-to-r from-red-600 via-rose-600 to-orange-600 text-white shadow-[0_0_15px_rgba(239,68,68,0.5)] cursor-pointer hover:opacity-90' 
                  : 'bg-gradient-to-r from-red-950/40 via-rose-950/30 to-zinc-900/50 text-slate-500 border border-red-900/20 opacity-40 cursor-not-allowed shadow-none'
              }`}
            >
              🛑 {t('pipeline.parar')}
            </button>
          </div>
        </div>

        {/* 2. MONITORAMENTO EM TEMPO REAL */}
        <div className="bg-[#0a0712] border border-[#1b1528] p-5 rounded-2xl shadow-xl flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider mb-3 text-slate-200 flex items-center gap-2">
              <span></span> {t('pipeline.monitoramento')}
            </h2>
            <div className="bg-[#0e0a1a] border border-[#1f1633] p-4 rounded-xl mb-4 flex items-start gap-3 justify-between text-sm font-mono">
              <span role="status" className={`min-w-0 whitespace-pre-wrap break-words leading-relaxed ${statusInfo.etapa === -1 && !/cancelad/i.test(statusInfo.status) || (statusInfo.semComunicacao || /sem comunicação|erro|falha/i.test(statusInfo.status)) ? 'text-rose-300' : 'text-[#b3ff33]'}`}>{carregando && <span aria-hidden="true" className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />}{carregando || statusInfo.etapa === -1 || (statusInfo.semComunicacao || /sem comunicação|erro|falha/i.test(statusInfo.status)) ? statusInfo.status : statusInfo.progresso_pct === 100 ? t('pipeline.concluido') : t('pipeline.pronto')}</span>
              <span className="shrink-0 font-bold text-white bg-[#1b1528] px-2.5 py-0.5 rounded-full border border-[#261b3d]">
                {statusInfo.progresso_pct}%
              </span>
            </div>

            <details className="my-4 rounded-xl border border-purple-900/60 bg-[#0e0a1a] p-3 text-sm">
              <summary className="cursor-pointer font-semibold text-cyan-300">{t('pipeline.detalhesExecucao')}</summary>
              <p className="mt-3 whitespace-pre-wrap break-words text-slate-300 leading-relaxed">{statusInfo.status}</p>
            {statusInfo.relatorio_curadoria && <a
              href={`${API_BASE_URL}/relatorios-curadoria/${statusInfo.relatorio_curadoria.split('/').pop()}`}
              className="text-xs text-cyan-400 underline" target="_blank" rel="noreferrer">
              {t('pipeline.baixarRelatorio')}
            </a>}
            {statusInfo.resumo_curadoria?.mensagem && <p role="status" className={`text-xs mt-2 ${
              statusInfo.resumo_curadoria.situacao === 'completa' && !statusInfo.resumo_curadoria.sugestoes
                ? 'text-slate-300' : 'text-amber-400'}`}>
              {statusInfo.resumo_curadoria.mensagem}
            </p>}
            {Number.isInteger(statusInfo.resumo_curadoria?.analisadas) && <p className="text-xs text-slate-400 mt-2">
              {t('pipeline.blocosAvaliados', { analisadas: statusInfo.resumo_curadoria.analisadas,
                janelas: statusInfo.resumo_curadoria.janelas, falhas: statusInfo.resumo_curadoria.falhas_tentadas,
                suspensos: statusInfo.resumo_curadoria.suspensas })}
            </p>}
            {statusInfo.resumo_curadoria?.decisoes_invalidas > 0 && statusInfo.resumo_curadoria?.descartes &&
              <ul className="text-xs text-slate-400 mt-2 space-y-1" aria-label={t('pipeline.motivosDescartes')}>
                {['abaixo_minimo', 'acima_maximo', 'ids_inexistentes', 'ordem_invalida', 'nao_detalhado'].map(key =>
                  statusInfo.resumo_curadoria.descartes[key] > 0 && <li key={key}>{t(`pipeline.descartes.${key}`)}: {statusInfo.resumo_curadoria.descartes[key]}</li>)}
              </ul>}
            </details>
            <div className="w-full bg-[#0e0a1a] rounded-full h-2.5 overflow-hidden border border-[#1f1633] mb-4">
              <div 
                className="bg-gradient-to-r from-[#9333ea] via-[#b3ff33] to-[#00ffff] h-full transition-all duration-500 rounded-full" 
                style={{ width: `${statusInfo.progresso_pct}%` }}
              ></div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            <div className="bg-[#0e0a1a] border border-[#1f1633] p-3 rounded-xl flex flex-col">
              <span className="text-[10px] font-mono text-slate-400 uppercase">{t('pipeline.decorrido')}</span>
              <span className="text-sm font-mono font-bold text-white mt-0.5">{statusInfo.tempo_decorrido || '00:00'}</span>
            </div>
            <div className="bg-[#0e0a1a] border border-[#1f1633] p-3 rounded-xl flex flex-col">
              <span className="text-[10px] font-mono text-slate-400 uppercase">{t('pipeline.totalRegistrado')}</span>
              <span className="text-sm font-mono font-bold text-[#00ffff] mt-0.5">{statusInfo.tempo_total || '00:00'}</span>
            </div>
          </div>
        </div>

        {/* 3. HARDWARE & PASTAS */}
        <div className="min-w-0 flex flex-col gap-3">
        <div className="bg-[#0a0712] border border-[#1b1528] p-5 rounded-2xl shadow-xl flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider mb-3 text-slate-200 flex items-center gap-2">
              <span></span> {t('pipeline.hardwarePastas')}
            </h2>
            <div className="flex flex-col gap-2.5 text-xs font-mono">
              <div className="bg-[#0e0a1a] border border-[#1f1633] p-2.5 rounded-xl flex justify-between items-center">
                <span className="text-slate-400">{t('pipeline.encoder')}</span>
                <span className="text-[#b3ff33] font-bold text-right" role="status">{statusInfo.encoder_tentativa ? t('pipeline.testandoEncoder', { encoder: statusInfo.encoder_tentativa }) : statusInfo.encoder || t('pipeline.aguardandoRender')}</span>
              </div>
              <div className="bg-[#0e0a1a] border border-[#1f1633] p-2.5 rounded-xl flex justify-between items-center">
                <span className="text-slate-400">{t('pipeline.iaEngine')}</span>
                <span className="text-cyan-400 font-bold text-right">{modeloIA || '—'}</span>
              </div>
            </div>
          </div>

          <div className="bg-[#0e0a1a] border border-[#1f1633] p-3 rounded-xl flex items-center justify-between mt-4">
            <span className="text-xs font-mono text-slate-400">{t('pipeline.exportSeguro')}</span>
            <span className="text-xs font-mono font-bold text-cyan-400">Cortes_Exportados</span>
          </div>
        </div>
        <div className="bg-gradient-to-br from-purple-950/70 via-[#0a0712] to-cyan-950/40 border border-purple-500/60 p-4 rounded-2xl flex flex-col gap-2">
          <h2 className="text-center font-bold">{t('pipeline.revisaoTitulo')}</h2>
          <p className="text-center text-sm text-slate-400">{t('pipeline.revisaoTexto')}</p>
          <button onClick={abrirRevisao} className="self-end mt-1 bg-gradient-to-r from-purple-600 to-cyan-600 px-4 py-2 rounded-xl text-sm font-bold hover:brightness-110">{t('pipeline.abrirRevisao')}</button>
        </div>
        </div>

        <div className="min-w-0 flex flex-col gap-3">
        {/* 4. MODO ESTÚDIO COMPONENTIZADO */}
        <div className="flex flex-col">
          <StudioCropper 
            source={entrada}
            previewPronto={previewPronto}
            buscandoPreview={carregandoPreview}
          />
        </div>

        </div>
        {/* GALERIA */}
        <div className="md:col-span-2 xl:col-span-4 min-w-0 mx-1 sm:mx-3 bg-[#0a0712] border border-[#1b1528] p-4 sm:p-5 rounded-2xl shadow-xl flex flex-col gap-4">
          <div className="flex justify-between items-center border-b border-[#1b1528] pb-3 flex-wrap gap-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <span></span> {t('pipeline.galeria')}
            </h2>
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-xs font-mono text-slate-400" aria-live="polite">{t('pipeline.selecionados', { selecionados: quantidadeSelecionada, total: statusInfo.videos.length })}</span>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={selecionarTodos}
                  disabled={statusInfo.videos.length === 0 || quantidadeSelecionada === statusInfo.videos.length}
                  className="bg-[#1b1528] hover:bg-[#9333ea] text-white px-3.5 py-2 rounded-xl text-xs font-mono transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {t('pipeline.selecionarTodos')}
                </button>
                <button
                  type="button"
                  onClick={limparSelecao}
                  disabled={quantidadeSelecionada === 0}
                  className="bg-[#1b1528] hover:bg-[#9333ea] text-white px-3.5 py-2 rounded-xl text-xs font-mono transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {t('pipeline.limparSelecao')}
                </button>
                <button 
                  onClick={deletarSelecionados}
                  className="bg-gradient-to-r from-red-600 to-rose-600 hover:opacity-90 text-white font-black px-3.5 py-2 rounded-xl text-xs font-mono tracking-wide shadow transition-all flex items-center gap-1.5 cursor-pointer"
                >
                   {t('pipeline.excluirSelecionados')}
                </button>
                <button 
                  onClick={exportarSelecionados}
                  className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:opacity-90 text-slate-950 font-black px-4 py-2 rounded-xl text-xs font-mono tracking-wide shadow transition-all flex items-center gap-1.5 cursor-pointer"
                >
                   {t('pipeline.exportarSelecionados')}
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 items-start">
            {statusInfo.videos.map(vidUrl => (
              <div key={vidUrl} className={`bg-[#0e0a1a] border p-3 rounded-xl flex flex-col gap-2.5 shadow-lg transition-all group ${selecionados[vidUrl] ? 'border-[#b3ff33] bg-[#12101e]' : 'border-[#1b1528] hover:border-[#9333ea]'}`}>
                {detalhesClips[vidUrl] && <div className="text-xs text-slate-300">
                  <strong>{['recomendado', 'revisar', 'sugestao'].includes(detalhesClips[vidUrl].avaliacao) ? t(`pipeline.avaliacao.${detalhesClips[vidUrl].avaliacao}`) : t('pipeline.avaliacao.curadoria')}</strong>
                  <details className="mt-1"><summary className="cursor-pointer text-cyan-300">{t('pipeline.verAvaliacao')}</summary><p className="mt-2 leading-relaxed">{detalhesClips[vidUrl].motivo}</p></details>
                </div>}
                <div className="relative rounded-lg overflow-hidden bg-black aspect-[9/16] shadow-inner w-full border border-[#1f1633]">
                  <video data-clip-url={vidUrl}
                    controls 
                    preload="metadata" 
                    className="w-full h-full object-cover"
                  >
                    <source src={`${MEDIA_BASE_URL}${vidUrl}`} type="video/mp4" />
                    {t('pipeline.semVideo')}
                  </video>
                  
                  <div className="absolute top-2 left-2 z-10">
                    <input 
                      type="checkbox" 
                      checked={!!selecionados[vidUrl]} 
                      onChange={() => toggleCheckbox(vidUrl)}
                      className="w-5 h-5 accent-[#b3ff33] cursor-pointer rounded shadow"
                    />
                  </div>

                  <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-mono text-cyan-400 border border-white/10 pointer-events-none">
                    {clipIdentity(vidUrl, t).numero !== null ? `#${clipIdentity(vidUrl, t).numero}` : t('corte.salvo')}
                  </div>
                </div>

                <div className="flex justify-between items-center mt-0.5">
                  <span title={vidUrl.split('/').pop()} className="text-xs font-mono font-bold text-slate-300 truncate max-w-[110px]">{clipIdentity(vidUrl, t).titulo}</span>
                  <a 
                    href={`${MEDIA_BASE_URL}${vidUrl}`} 
                    onClick={async event => {
                      if (!window.pywebview?.api?.salvar_corte) return;
                      event.preventDefault();
                      try {
                        const result = await window.pywebview.api.salvar_corte(vidUrl.split('/').pop());
                        if (!result.cancelado) notify(t('pipeline.videoSalvo', { caminho: result.caminho }), t('pipeline.downloadConcluido'));
                      } catch (error) { notify(error.message, t('pipeline.erroSalvarVideo')); }
                    }}
                    download
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] bg-[#1b1528] hover:bg-[#9333ea] text-slate-200 hover:text-white px-2.5 py-1 rounded-md transition-all font-mono shadow"
                  >
                     {t('pipeline.baixar')}
                  </a>
                </div>
                <p className="text-[10px] text-slate-400">{clipIdentity(vidUrl, t).sessao}</p>
              </div>
            ))}
            {statusInfo.videos.length === 0 && (
              <div className="text-center py-16 border border-dashed border-[#1b1528] rounded-xl col-span-full bg-[#0e0a1a]/50">
                <span className="text-4xl block mb-2 opacity-50"></span>
                <p className="text-xs text-slate-400 font-mono">{t('pipeline.galeriaVazia')}</p>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
