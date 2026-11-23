import React, { useState, useRef, useEffect } from 'react';

import { useI18n } from '../../i18n/useI18n';

// Editor controlado do enquadramento: retângulo da webcam, lupa PIP e posição do recorte
// vertical do conteúdo. Não carrega nem salva nada; quem usa decide onde guardar `value`.
// Usado pelo Modo Estúdio (preset global) e pela revisão (ajuste de um corte).
export function EditorEnquadramento({ value, onChange, mediaUrl, isVideo, hasMediaError, onMediaError, onReadyChange }) {
  const { t } = useI18n();
  const { ativo, webcam: webcamBox, foco } = value;
  const [isInteracting, setIsInteracting] = useState(false);
  const [mediaAspect, setMediaAspect] = useState(16 / 9);
  // A mídia está pronta quando a URL atual carregou; trocar a URL volta a "não pronta".
  const [urlCarregada, setUrlCarregada] = useState(null);
  const mediaReady = urlCarregada === mediaUrl;
  const sourceVideoRef = useRef(null);
  const pipVideoRef = useRef(null);
  const containerRef = useRef(null);
  const boxRef = useRef(null);

  useEffect(() => { onReadyChange?.(mediaReady); }, [mediaReady, onReadyChange]);

  // Num arrasto só muda o campo arrastado, então o valor do início do gesto basta para o resto.
  const atualizar = (parcial) => onChange({ ...value, ...parcial });

  const syncPreview = () => {
    const sourceVideo = sourceVideoRef.current;
    const pipVideo = pipVideoRef.current;
    if (sourceVideo && pipVideo && Math.abs(sourceVideo.currentTime - pipVideo.currentTime) > 0.12) {
      pipVideo.currentTime = sourceVideo.currentTime;
    }
  };

  // Mesma conta de core/composition.py: com webcam, o conteúdo ocupa 1080 x (1920 - altura da webcam).
  const proporcaoConteudo = (() => {
    if (!ativo || webcamBox.width <= 0) return 1080 / 1920;
    const camAltura = Math.max(2, Math.min(960, Math.round(1080 * (webcamBox.height / webcamBox.width) / mediaAspect / 2) * 2));
    return 1080 / (1920 - camAltura);
  })();
  const larguraMoldura = Math.min(100, proporcaoConteudo / mediaAspect * 100);
  const esquerdaMoldura = (100 - larguraMoldura) * foco / 100;

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
      atualizar({ foco: Math.abs(novo - 50) < 1.5 ? 50 : novo });
    };
    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      setIsInteracting(false);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const initDragOrResize = (e, mode) => {
    if (!ativo || !containerRef.current || !boxRef.current) return;
    e.stopPropagation();
    e.preventDefault();

    setIsInteracting(true);
    const containerRect = containerRef.current.getBoundingClientRect();
    const startX = e.clientX;
    const startY = e.clientY;
    const inicial = webcamBox;

    let currentX = inicial.x;
    let currentY = inicial.y;
    let currentW = inicial.width;
    let currentH = inicial.height;

    const onMouseMove = (moveEvent) => {
      const dxPercent = ((moveEvent.clientX - startX) / containerRect.width) * 100;
      const dyPercent = ((moveEvent.clientY - startY) / containerRect.height) * 100;

      if (mode === 'drag') {
        currentX = Math.max(0, Math.min(100 - currentW, inicial.x + dxPercent));
        currentY = Math.max(0, Math.min(100 - currentH, inicial.y + dyPercent));
      } else if (mode === 'resize') {
        currentW = Math.max(10, Math.min(80, inicial.width + dxPercent));
        currentH = currentW * (9 / 16) * (containerRect.width / containerRect.height);

        if (currentX + currentW > 100) {
          currentW = 100 - currentX;
          currentH = currentW * (9 / 16) * (containerRect.width / containerRect.height);
        }
        if (currentY + currentH > 100) {
          currentH = 100 - currentY;
          currentW = currentH * (16 / 9) * (containerRect.height / containerRect.width);
        }
      }

      atualizar({ webcam: {
        x: Number(currentX.toFixed(4)),
        y: Number(currentY.toFixed(4)),
        width: Number(currentW.toFixed(4)),
        height: Number(currentH.toFixed(4)),
      } });
    };

    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      setIsInteracting(false);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  return (
    <>
      {/* 🔍 LUPA PIP */}
      {ativo && (
        <div className="flex flex-col items-center justify-center bg-gradient-to-b from-[#070512] to-[#040308] border border-[#1b1528] p-2 rounded-2xl shadow-2xl">
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
            <div className="w-48 rounded-[10px] overflow-hidden bg-black relative" style={{ aspectRatio: isVideo ? mediaAspect * webcamBox.width / webcamBox.height : 16 / 9 }}>
              <div className="relative w-full h-full overflow-hidden">
                {isVideo ? (
                  <video
                    ref={pipVideoRef}
                    src={mediaUrl}
                    autoPlay loop muted playsInline
                    className="absolute max-w-none"
                    style={{
                      width: `${100 * (100 / webcamBox.width)}%`,
                      height: `${100 * (100 / webcamBox.height)}%`,
                      left: `-${webcamBox.x * (100 / webcamBox.width)}%`,
                      top: `-${webcamBox.y * (100 / webcamBox.height)}%`,
                    }}
                    onError={onMediaError}
                  />
                ) : (
                  <img
                    src={mediaUrl}
                    alt={t('estudio.altZoom')}
                    className="absolute inset-0 w-full h-full object-contain p-2"
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {ativo && (
        <label className="block text-xs text-slate-300">{t('estudio.larguraWebcam', { valor: webcamBox.width.toFixed(1) })}
          <input type="range" min="5" max="80" step="0.1" value={webcamBox.width} disabled={!mediaReady}
            onChange={e => {
              const width = Math.min(Number(e.target.value), 100 - webcamBox.x, (100 - webcamBox.y) * 16 / 9 / mediaAspect);
              atualizar({ webcam: { ...webcamBox, width, height: width * 9 / 16 * mediaAspect } });
            }} className="mt-2 block w-full accent-cyan-400 disabled:opacity-40" />
        </label>
      )}

      {mediaReady && !hasMediaError && (
        <label className="block text-xs text-slate-300">
          <span className="flex items-center justify-between">
            <span>{t('estudio.posicaoConteudo', { lado: t(Math.abs(foco - 50) < 2 ? 'estudio.centro' : foco < 50 ? 'estudio.esquerda' : 'estudio.direita'), valor: foco.toFixed(0) })}</span>
            <button type="button" onClick={() => atualizar({ foco: 50 })} disabled={foco === 50}
              className="text-[11px] text-cyan-300 hover:text-cyan-200 disabled:opacity-40 disabled:cursor-default">{t('estudio.centralizar')}</button>
          </span>
          <input type="range" min="0" max="100" step="0.5" value={foco} onChange={e => atualizar({ foco: Number(e.target.value) })}
            className="mt-2 block w-full accent-cyan-400" />
          <span className="mt-1 block text-[11px] text-slate-500">{t('estudio.dicaMoldura')}</span>
        </label>
      )}

      {/* Container 16:9 Principal */}
      <div className="w-full flex items-center justify-center py-1">
        <div
          ref={containerRef}
          style={{ aspectRatio: isVideo ? mediaAspect : 16 / 9 }}
          className="relative w-full max-w-[560px] bg-black outline outline-[#221838] rounded-xl overflow-hidden select-none flex items-center justify-center shadow-inner"
        >
          {isVideo ? (
            <video
              key={mediaUrl}
              ref={sourceVideoRef}
              onLoadedMetadata={event => { setMediaAspect(event.currentTarget.videoWidth / event.currentTarget.videoHeight); setUrlCarregada(mediaUrl); }}
              onTimeUpdate={syncPreview}
              onSeeked={syncPreview}
              src={mediaUrl}
              autoPlay
              loop
              muted
              playsInline
              className="absolute inset-0 w-full h-full object-contain"
              onError={onMediaError}
            />
          ) : !hasMediaError ? (
            <img
              key={mediaUrl}
              ref={sourceVideoRef}
              src={mediaUrl}
              alt={t('estudio.altPreview')}
              className="absolute inset-0 w-full h-full object-contain bg-black"
              onError={onMediaError}
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
          {mediaReady && !hasMediaError && larguraMoldura < 100 && (
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
          {ativo && (
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
    </>
  );
}
