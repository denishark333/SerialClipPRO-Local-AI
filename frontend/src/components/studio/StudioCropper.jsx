import { useDialog } from '../layout/useDialog';
import React, { useState, useEffect, useCallback } from 'react';

import { API_BASE_URL } from '../../api';
import { useI18n, useTAtual } from '../../i18n/useI18n';
import { EditorEnquadramento } from './EditorEnquadramento';
import { ENQUADRAMENTO_PADRAO, configParaEnquadramento, enquadramentoParaConfig } from './enquadramento';

// Modo Estúdio: o preset global de enquadramento, salvo em /studio-config.
export function StudioCropper({ source, previewPronto, buscandoPreview = false }) {
  const { notify } = useDialog();
  const { t } = useI18n();
  const tAtual = useTAtual();
  const [enquadramento, setEnquadramento] = useState(ENQUADRAMENTO_PADRAO);

  const [frameUrl, setFrameUrl] = useState('/serial-healer.png');
  const [isMediaTypeVideo, setIsMediaTypeVideo] = useState(false);
  const [hasFrameError, setHasFrameError] = useState(false);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [mediaReady, setMediaReady] = useState(false);
  const marcarErroMidia = useCallback(() => setHasFrameError(true), []);

  // 🎯 SALVA EM PORCENTAGEM PURA (0 a 100%) - INDEPENDENTE DE RESOLUÇÃO
  const saveConfigToBackend = async (valor) => {
    setIsSaving(true);
    try {
      const response = await fetch(`${API_BASE_URL}/studio-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(enquadramentoParaConfig(valor)),
      });

      if (!response.ok) throw new Error(t('estudio.erroSalvar'));
      return await response.json();
    } finally {
      setIsSaving(false);
    }
  };

  const [frameRetry, setFrameRetry] = useState(0);
  const loadConfigAndFrame = () => setFrameRetry(value => value + 1);

  // Carrega o preset uma vez; buscar o preview não deve sobrescrever ajustes em edição.
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/studio-config`, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error(tAtual.current('estudio.erroCarregar'));
        const data = await response.json();
        if (controller.signal.aborted) return;
        setEnquadramento(configParaEnquadramento(data));
      })
      .catch(err => { if (!controller.signal.aborted) setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setIsLoadingConfig(false); });
    return () => controller.abort();
  }, [tAtual]);

  useEffect(() => {
    const controller = new AbortController();
    let timer;
    let tentativa = 0;
    const consultar = async () => {
      tentativa += 1;
      if (tentativa === 1) {
        setHasFrameError(false);
        setIsMediaTypeVideo(false);
        setFrameUrl('/serial-healer.png');
      }
      try {
        const param = source ? `?entrada=${encodeURIComponent(source)}` : '';
        const response = await fetch(`${API_BASE_URL}/studio/frame-base${param}`, { signal: controller.signal });
        if (!response.ok) throw new Error(tAtual.current('estudio.erroConsultar'));
        const data = await response.json();
        if (controller.signal.aborted) return;
        if (data.tipo === 'erro') {
          // A geração falhou no backend: não adianta continuar esperando.
          setHasFrameError(true);
          setError(`${tAtual.current('estudio.erroGerar')} ${data.mensagem || ''}`.trim());
          return;
        }
        if (source && data.tipo !== 'video_real') {
          if (tentativa < 120) { timer = setTimeout(consultar, 1500); return; }
          throw new Error(tAtual.current('estudio.previewIndisponivelDetalhe'));
        }
        const root = API_BASE_URL.replace(/\/api$/, '');
        const url = data.url.startsWith('http') || !data.url.includes('temp_clip_cache')
          ? data.url : `${root}${data.url}`;
        setFrameUrl(data.tipo === 'video_real' ? `${url}?t=${Date.now()}` : url);
        setIsMediaTypeVideo(data.tipo === 'video_real');
        setHasFrameError(false);
        setError('');
      } catch (err) {
        if (controller.signal.aborted) return;
        if (tentativa < 120) timer = setTimeout(consultar, 1500);
        else { setHasFrameError(true); setError(err.message); }
      }
    };
    timer = setTimeout(consultar, 0);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [source, previewPronto, frameRetry, tAtual]);

  const handleToggleChange = async (e) => {
    const anterior = enquadramento;
    const novo = { ...enquadramento, ativo: e.target.checked };
    setEnquadramento(novo);
    try {
      await saveConfigToBackend(novo);
    } catch (err) {
      setEnquadramento(anterior);
      setError(err.message);
    }
  };

  const handleSave = async () => {
    try {
      const result = await saveConfigToBackend(enquadramento);
      notify(`⚡ ${result.mensagem || t('estudio.salvo')}`);
    } catch (err) {
      console.error("Erro ao salvar:", err);
      notify(t('estudio.erroSalvar'));
    }
  };

  return (
    <div className="bg-[#0a0712] border border-[#1b1528] p-4 rounded-2xl shadow-2xl w-full flex flex-col gap-2 text-slate-200">

      {/* Topo */}
      <div>
        <div className="flex justify-between items-center pb-2">
          <h3 className="text-sm font-bold flex items-center gap-2">
            <span className="text-[#b3ff33]"></span> {t('estudio.titulo')}
          </h3>

          {/* Badge Preview Pronto */}
          <div role="status" className={`flex items-center gap-2 border px-3 py-2 rounded-full text-xs font-bold ${hasFrameError ? 'border-rose-500/50 bg-rose-950/40 text-rose-300' : source && (!mediaReady || buscandoPreview) ? 'border-amber-400/60 bg-amber-950/40 text-amber-300' : mediaReady ? 'border-lime-400/50 bg-lime-950/30 text-lime-300' : 'border-slate-600 text-slate-300'}`}>
            {source && (!mediaReady || buscandoPreview) && !hasFrameError && <span className="h-3 w-3 animate-spin rounded-full border-2 border-amber-300 border-t-transparent" />}
            <span>{hasFrameError ? t('estudio.previewIndisponivel') : source && (!mediaReady || buscandoPreview) ? t('estudio.buscandoPreview') : mediaReady ? t('estudio.previewPronto') : t('estudio.aguardandoFonte')}</span>
          </div>
        </div>

        <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-[#1b1528] to-transparent mb-2"></div>

        <p className="text-xs text-slate-400 text-center px-2 mb-2">
          {t('estudio.instrucao')}
        </p>

        {isLoadingConfig && (
          <div className="text-center text-xs text-amber-400 mb-2 font-mono p-2 bg-amber-950/30 rounded-lg animate-pulse border border-amber-500/20">
            {t('estudio.gerandoPreview')}
          </div>
        )}
        {error && (
          <div className="text-center text-xs text-red-400 mb-2 font-mono p-2 bg-red-950/30 rounded-lg border border-red-500/20">
            {error}
          </div>
        )}

        {/* Chavinha com Ativação */}
        <div className="flex items-center justify-center gap-3 bg-gradient-to-r from-[#05070b]/90 via-[#0f0c1b]/90 to-[#05070b]/90 border border-[#1b1528] px-3 py-2.5 rounded-xl mb-2 shadow-inner">
          <label className="relative inline-flex items-center cursor-pointer shrink-0">
            <input
              type="checkbox"
              checked={enquadramento.ativo}
              onChange={handleToggleChange}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-[#1b1528] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-[#b3ff33] peer-checked:to-[#00ffcc]"></div>
          </label>
          <span className="text-[11px] font-mono text-slate-300">
            {enquadramento.ativo ? t('estudio.ativo') : t('estudio.desativado')}
          </span>
        </div>
      </div>

      <EditorEnquadramento
        value={enquadramento}
        onChange={setEnquadramento}
        mediaUrl={frameUrl}
        isVideo={isMediaTypeVideo}
        hasMediaError={hasFrameError}
        onMediaError={marcarErroMidia}
        onReadyChange={setMediaReady}
      />

      {hasFrameError && <button onClick={loadConfigAndFrame} className="text-xs text-amber-400">{t('estudio.atualizarPreview')}</button>}
      {/* 🟢 BOTÃO DE SALVAR */}
      <div className="pt-2 border-t border-[#1b1528] flex justify-center">
        <button
          onClick={handleSave}
          disabled={isLoadingConfig || isSaving}
          className={`w-full py-3 rounded-xl text-xs font-mono font-bold bg-gradient-to-r from-[#b3ff33] via-[#8ce619] to-[#00ffcc] text-black hover:brightness-110 active:scale-[0.99] transition-all duration-200 shadow-[0_0_20px_rgba(179,255,51,0.25)] hover:shadow-[0_0_30px_rgba(0,255,204,0.4)] flex items-center justify-center gap-2 cursor-pointer ${(isLoadingConfig || isSaving) ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {isSaving ? `⚡ ${t('estudio.salvando')}` : isLoadingConfig ? t('estudio.carregando') : t('estudio.salvar')}
        </button>
      </div>

    </div>
  );
}
