import { useDialog } from '../layout/useDialog';
import React, { useState, useRef, useEffect, useCallback } from 'react';

import { API_BASE_URL } from '../../api';
import { useI18n, useTAtual } from '../../i18n/useI18n';

export function StudioCropper({ source, previewPronto, buscandoPreview = false }) {
  const { notify } = useDialog();
  const { t } = useI18n();
  const tAtual = useTAtual();
  const [isEnabled, setIsEnabled] = useState(false);
  const [webcamBox, setWebcamBox] = useState({ x: 60, y: 55, width: 35, height: 35 });
  // Posição horizontal do recorte vertical do conteúdo: 0 = esquerda, 50 = centro, 100 = direita.
  const [foco, setFoco] = useState(50);
  const [isInteracting, setIsInteracting] = useState(false);
  
  const [frameUrl, setFrameUrl] = useState('/serial-healer.png');
  const [isMediaTypeVideo, setIsMediaTypeVideo] = useState(false);
  const [hasFrameError, setHasFrameError] = useState(false);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  
  const [mediaAspect, setMediaAspect] = useState(16 / 9);
  const [mediaReady, setMediaReady] = useState(false);
  const sourceVideoRef = useRef(null);
  const pipVideoRef = useRef(null);
  const syncPreview = () => {
    const sourceVideo = sourceVideoRef.current;
    const pipVideo = pipVideoRef.current;
    if (sourceVideo && pipVideo && Math.abs(sourceVideo.currentTime - pipVideo.currentTime) > 0.12) {
      pipVideo.currentTime = sourceVideo.currentTime;
    }
  };
  const containerRef = useRef(null);
  const boxRef = useRef(null);

  // Mesma conta de core/composition.py: com webcam, o conteúdo ocupa 1080 x (1920 - altura da webcam).
  const proporcaoConteudo = (() => {
    if (!isEnabled || webcamBox.width <= 0) return 1080 / 1920;
    const camAltura = Math.max(2, Math.min(960, Math.round(1080 * (webcamBox.height / webcamBox.width) / mediaAspect / 2) * 2));
    return 1080 / (1920 - camAltura);
  })();
  const larguraMoldura = Math.min(100, proporcaoConteudo / mediaAspect * 100);
  const esquerdaMoldura = (100 - larguraMoldura) * foco / 100;

  // 🎯 SALVA EM PORCENTAGEM PURA (0 a 100%) - INDEPENDENTE DE RESOLUÇÃO
  const saveConfigToBackend = async (newIsEnabled, currentBox) => {
    setIsSaving(true);
    
    const configPayload = { 
      modo_estudio_ativo: newIsEnabled,
      enquadramento_feito: newIsEnabled,
      foco_conteudo: Number(foco.toFixed(2)),
      crop_jogo: { x: 0, y: 0, w: 100, h: 100 },
      crop_webcam: { 
        x: Number(currentBox.x.toFixed(4)), 
        y: Number(currentBox.y.toFixed(4)), 
        w: Number(currentBox.width.toFixed(4)), 
        h: Number(currentBox.height.toFixed(4)) 
      }
    };
    
    try {
      const response = await fetch(`${API_BASE_URL}/studio-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configPayload),
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
        setIsEnabled(Boolean(data.modo_estudio_ativo));
        const focoSalvo = Number(data.foco_conteudo);
        if (Number.isFinite(focoSalvo)) setFoco(Math.max(0, Math.min(100, focoSalvo)));
        const box = data.crop_webcam;
        if (box?.w > 0 && box?.h > 0) {
          const pixels = box.w > 100 || box.h > 100;
          setWebcamBox({
            x: pixels ? box.x / 1920 * 100 : box.x,
            y: pixels ? box.y / 1080 * 100 : box.y,
            width: pixels ? box.w / 1920 * 100 : box.w,
            height: pixels ? box.h / 1080 * 100 : box.h,
          });
        }
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
        setMediaReady(false);
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
    const newValue = e.target.checked;
    setIsEnabled(newValue);
    try {
      await saveConfigToBackend(newValue, webcamBox);
    } catch (err) {
      setIsEnabled(!newValue);
      setError(err.message);
    }
  };

  const handleSave = async () => {
    try {
      const result = await saveConfigToBackend(isEnabled, webcamBox);
      notify(`⚡ ${result.mensagem || t('estudio.salvo')}`);
    } catch (err) {
      console.error("Erro ao salvar:", err);
      notify(t('estudio.erroSalvar'));
    }
  };

  const arrastarMoldura = (e) => {
    if (!containerRef.current || larguraMoldura >= 100) return;
    e.preventDefault();
    setIsInteracting(true);
    const larguraContainer = containerRef.current.getBoundingClientRect().width;
    const inicioX = e.clientX;
    const focoInicial = foco;
    const livre = 100 - larguraMoldura;
    const onMouseMove = (moveEvent) => {
      const deslocamento = (moveEvent.clientX - inicioX) / larguraContainer * 100;
      const novo = Math.max(0, Math.min(100, focoInicial + deslocamento / livre * 100));
      // Ímã no centro: fica fácil voltar exatamente para o meio.
      setFoco(Math.abs(novo - 50) < 1.5 ? 50 : novo);
    };
    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      setIsInteracting(false);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const initDragOrResize = useCallback((e, mode) => {
    if (!isEnabled || !containerRef.current || !boxRef.current) return;
    e.stopPropagation();
    e.preventDefault();

    setIsInteracting(true);
    const containerRect = containerRef.current.getBoundingClientRect();
    const startX = e.clientX;
    const startY = e.clientY;

    let currentX = webcamBox.x;
    let currentY = webcamBox.y;
    let currentW = webcamBox.width;
    let currentH = webcamBox.height;

    const onMouseMove = (moveEvent) => {
      const dxPx = moveEvent.clientX - startX;
      const dyPx = moveEvent.clientY - startY;

      const dxPercent = (dxPx / containerRect.width) * 100;
      const dyPercent = (dyPx / containerRect.height) * 100;

      if (mode === 'drag') {
        currentX = Math.max(0, Math.min(100 - currentW, webcamBox.x + dxPercent));
        currentY = Math.max(0, Math.min(100 - currentH, webcamBox.y + dyPercent));

        if (boxRef.current) {
          boxRef.current.style.left = `${currentX}%`;
          boxRef.current.style.top = `${currentY}%`;
        }
      } else if (mode === 'resize') {
        currentW = Math.max(10, Math.min(80, webcamBox.width + dxPercent));
        currentH = currentW * (9 / 16) * (containerRect.width / containerRect.height);

        if (currentX + currentW > 100) {
          currentW = 100 - currentX;
          currentH = currentW * (9 / 16) * (containerRect.width / containerRect.height);
        }
        if (currentY + currentH > 100) {
          currentH = 100 - currentY;
          currentW = currentH * (16 / 9) * (containerRect.height / containerRect.width);
        }

        if (boxRef.current) {
          boxRef.current.style.width = `${currentW}%`;
          boxRef.current.style.height = `${currentH}%`;
        }
      }
      
      setWebcamBox({
        x: Number(currentX.toFixed(4)),
        y: Number(currentY.toFixed(4)),
        width: Number(currentW.toFixed(4)),
        height: Number(currentH.toFixed(4))
      });
    };

    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      setIsInteracting(false);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, [isEnabled, webcamBox]);

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
              checked={isEnabled} 
              onChange={handleToggleChange} 
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-[#1b1528] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-[#b3ff33] peer-checked:to-[#00ffcc]"></div>
          </label>
          <span className="text-[11px] font-mono text-slate-300">
            {isEnabled ? t('estudio.ativo') : t('estudio.desativado')}
          </span>

        </div>

        {/* 🔍 LUPA PIP */}
        {isEnabled && (
          <div className="mt-2 mb-0 flex flex-col items-center justify-center bg-gradient-to-b from-[#070512] to-[#040308] border border-[#1b1528] p-2 rounded-2xl shadow-2xl">
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-2 h-2 rounded-full ${isInteracting ? 'bg-gradient-to-r from-pink-500 to-rose-500 animate-ping' : 'bg-gradient-to-r from-[#b3ff33] to-[#00ffcc]'}`}></span>
              <span className="text-[10px] font-mono text-slate-300 font-bold uppercase tracking-wider">
                {t('estudio.lupa')}
              </span>

            </div>

            <div className={`relative p-[2px] rounded-xl transition-all duration-300 ${
              isInteracting 
                ? 'bg-gradient-to-r from-pink-500 via-fuchsia-500 to-rose-500 scale-105' 
                : 'bg-gradient-to-r from-[#b3ff33] via-[#00ffcc] to-[#7be619] shadow-[0_0_20px_rgba(179,255,51,0.25)]'
            }`}>
              <div className="w-48 rounded-[10px] overflow-hidden bg-black relative" style={{ aspectRatio: isMediaTypeVideo ? mediaAspect * webcamBox.width / webcamBox.height : 16 / 9 }}>
                <div className="relative w-full h-full overflow-hidden">
                  {isMediaTypeVideo ? (
                    <video 
                      ref={pipVideoRef}
                      src={frameUrl} 
                      autoPlay loop muted playsInline 
                      className="absolute max-w-none"
                      style={{
                        width: `${100 * (100 / webcamBox.width)}%`,
                        height: `${100 * (100 / webcamBox.height)}%`,
                        left: `-${webcamBox.x * (100 / webcamBox.width)}%`,
                        top: `-${webcamBox.y * (100 / webcamBox.height)}%`,
                      }}
                      onError={() => setHasFrameError(true)}
                    />
                  ) : (
                    <img 
                      src={frameUrl} 
                      alt={t('estudio.altZoom')} 
                      className="absolute inset-0 w-full h-full object-contain p-2"
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {isEnabled && (
        <label className="block text-xs text-slate-300">{t('estudio.larguraWebcam', { valor: webcamBox.width.toFixed(1) })}
          <input type="range" min="5" max="80" step="0.1" value={webcamBox.width} disabled={!mediaReady}
            onChange={e => {
              const width = Math.min(Number(e.target.value), 100 - webcamBox.x, (100 - webcamBox.y) * 16 / 9 / mediaAspect);
              setWebcamBox(prev => ({ ...prev, width, height: width * 9 / 16 * mediaAspect }));
            }} className="mt-2 block w-full accent-cyan-400 disabled:opacity-40" />
        </label>
      )}

      {mediaReady && !hasFrameError && (
        <label className="block text-xs text-slate-300">
          <span className="flex items-center justify-between">
            <span>{t('estudio.posicaoConteudo', { lado: t(Math.abs(foco - 50) < 2 ? 'estudio.centro' : foco < 50 ? 'estudio.esquerda' : 'estudio.direita'), valor: foco.toFixed(0) })}</span>
            <button type="button" onClick={() => setFoco(50)} disabled={foco === 50}
              className="text-[11px] text-cyan-300 hover:text-cyan-200 disabled:opacity-40 disabled:cursor-default">{t('estudio.centralizar')}</button>
          </span>
          <input type="range" min="0" max="100" step="0.5" value={foco} onChange={e => setFoco(Number(e.target.value))}
            className="mt-2 block w-full accent-cyan-400" />
          <span className="mt-1 block text-[11px] text-slate-500">{t('estudio.dicaMoldura')}</span>
        </label>
      )}

      {/* Container 16:9 Principal */}
      <div className="w-full flex items-center justify-center py-1">
        <div 
          ref={containerRef}
          style={{ aspectRatio: isMediaTypeVideo ? mediaAspect : 16 / 9 }}
          className="relative w-full max-w-[560px] bg-black outline outline-[#221838] rounded-xl overflow-hidden select-none flex items-center justify-center shadow-inner"
        >
          {isMediaTypeVideo ? (
            <video 
              key={frameUrl}
              ref={sourceVideoRef}
              onLoadedMetadata={event => { setMediaAspect(event.currentTarget.videoWidth / event.currentTarget.videoHeight); setMediaReady(true); }}
              onTimeUpdate={syncPreview}
              onSeeked={syncPreview}
              src={frameUrl} 
              autoPlay 
              loop 
              muted 
              playsInline 
              className="absolute inset-0 w-full h-full object-contain"
              onError={() => {
                setHasFrameError(true);
              }}
            />
          ) : !hasFrameError ? (
            <img 
              key={frameUrl}
              ref={sourceVideoRef}
              onLoadedMetadata={event => { setMediaAspect(event.currentTarget.videoWidth / event.currentTarget.videoHeight); setMediaReady(true); }}
              onTimeUpdate={syncPreview}
              onSeeked={syncPreview}
              src={frameUrl} 
              alt={t('estudio.altPreview')} 
              className="absolute inset-0 w-full h-full object-contain bg-black"
              onError={() => setHasFrameError(true)}
            />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#07050f] p-4">
              <img 
                src="/serial-healer.png" 
                alt="Placeholder" 
                className="w-24 h-24 object-contain opacity-75 mb-2 drop-shadow-lg"
              />
              <span className="text-[10px] font-mono tracking-widest text-slate-400">
                {t('estudio.aguardandoFrame')}
              </span>
            </div>
          )}

          <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#b3ff33_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none"></div>

          {/* Moldura do recorte vertical do conteúdo */}
          {mediaReady && !hasFrameError && larguraMoldura < 100 && (
            <>
              <div className="absolute inset-y-0 left-0 bg-black/55 pointer-events-none" style={{ width: `${esquerdaMoldura}%` }} />
              <div className="absolute inset-y-0 right-0 bg-black/55 pointer-events-none" style={{ width: `${100 - esquerdaMoldura - larguraMoldura}%` }} />
              <div
                onMouseDown={arrastarMoldura}
                style={{ left: `${esquerdaMoldura}%`, width: `${larguraMoldura}%` }}
                className="absolute inset-y-0 border-2 border-cyan-300/80 cursor-ew-resize z-[5] flex items-start justify-center"
                title={t('estudio.dicaMolduraCurta')}
              >
                <span className="mt-1 bg-black/50 px-2 py-0.5 rounded text-[10px] font-mono text-cyan-200 font-bold pointer-events-none">{t('estudio.corteVertical')}</span>
              </div>
            </>
          )}

          {/* 🎯 QUADRADO ROSA EM GRADIENTE */}
          {isEnabled && (
            <div 
              ref={boxRef}
              onMouseDown={(e) => initDragOrResize(e, 'drag')}
              style={{ 
                left: `${webcamBox.x}%`, 
                top: `${webcamBox.y}%`, 
                width: `${webcamBox.width}%`, 
                height: `${webcamBox.height}%` 
              }}
              className="absolute border border-pink-400/80 bg-pink-500/5 rounded-xl cursor-move flex items-center justify-center z-10 box-border will-change-[left,top,width,height]"
            >
              <div className="box-content bg-black/20 px-2 py-0.5 rounded pointer-events-none flex items-center gap-1 opacity-60">
                <span className="w-2 h-2 rounded-full bg-gradient-to-r from-pink-400 to-rose-400 animate-pulse shrink-0 shadow-[0_0_8px_#ec4899]"></span>
                <span className="text-[10px] font-mono text-pink-200 font-bold tracking-wide truncate">{t('estudio.webcam')}</span>
              </div>

              <div 
                onMouseDown={(e) => initDragOrResize(e, 'resize')}
                className="absolute bottom-0 right-0 w-7 h-7 bg-gradient-to-br from-pink-400 to-rose-600 rounded-tl-md cursor-se-resize hover:brightness-125 transition flex items-center justify-center shadow-md"
                title={t('estudio.dicaRedimensionar')}
              >
                <div className="w-1.5 h-1.5 bg-black/60 rounded-full"></div>
              </div>
            </div>
          )}
        </div>
      </div>

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
