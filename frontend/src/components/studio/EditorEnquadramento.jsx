import React, { useState, useRef, useEffect } from 'react';

import { API_BASE_URL } from '../../api';
import { useI18n } from '../../i18n/useI18n';
import { PROPORCAO_PESSOA } from './enquadramento';

// Trecho da mídia recortado numa área: usado pela lupa da webcam e pela prévia do Podcast.
function RecorteMidia({ box, mediaUrl, videoRef, onError }) {
  return (
    <video
      ref={videoRef}
      src={mediaUrl}
      autoPlay loop muted playsInline
      className="absolute max-w-none"
      style={{
        width: `${100 * (100 / box.width)}%`,
        height: `${100 * (100 / box.height)}%`,
        left: `-${box.x * (100 / box.width)}%`,
        top: `-${box.y * (100 / box.height)}%`,
      }}
      onError={onError}
    />
  );
}

// Editor controlado do enquadramento: retângulo da webcam, lupa PIP e posição do recorte
// vertical do conteúdo, ou as duas pessoas do Modo Podcast. Não carrega nem salva nada;
// quem usa decide onde guardar `value`.
// Usado pelo Modo Estúdio (preset global) e pela revisão (ajuste de um corte).
export function EditorEnquadramento({ value, onChange, mediaUrl, isVideo, hasMediaError, onMediaError, onReadyChange }) {
  const { t } = useI18n();
  const { ativo, webcam: webcamBox, foco, layout = 'webcam', esquerda, direita, direitaEmCima = false } = value;
  const podcast = ativo && layout === 'podcast';
  // Perfis do Podcast: 1 = tela dividida (duas pessoas), 2 = um corte vertical único, como o modo normal,
  // ou automático: o perfil 1 nos planos parecidos com o plano aberto de referência e o 2 nos closes.
  // As abas só escolhem o que se edita; o Podcast sempre sai no automático (salvo como 'automatico').
  const [perfil, setAba] = useState('dividido');
  const automatico = podcast && perfil === 'automatico';
  // O automático usa os enquadramentos salvos nas outras duas abas: lá o vídeo só serve para
  // escolher os quadros de referência, sem áreas de recorte por cima.
  const dividido = podcast && perfil === 'dividido';
  const centralizado = podcast && perfil === 'centralizado';
  const [marcandoReferencia, setMarcandoReferencia] = useState(false);
  const [erroReferencia, setErroReferencia] = useState('');
  const podcastVideo1Ref = useRef(null);
  const podcastVideo2Ref = useRef(null);
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
    for (const pipVideo of [pipVideoRef.current, podcastVideo1Ref.current, podcastVideo2Ref.current]) {
      if (sourceVideo && pipVideo && Math.abs(sourceVideo.currentTime - pipVideo.currentTime) > 0.12) {
        pipVideo.currentTime = sourceVideo.currentTime;
      }
    }
  };

  // Mesma conta de core/composition.py: com webcam, o conteúdo ocupa 1080 x (1920 - altura da webcam).
  const proporcaoConteudo = (() => {
    if (!ativo || podcast || webcamBox.width <= 0) return 1080 / 1920;
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

  // `chave`: 'webcam' (16:9) ou 'esquerda'/'direita' do Podcast (9:8, a proporção de cada metade do corte).
  // Cada lado do Podcast fica preso à sua metade do vídeo: as duas áreas nunca se sobrepõem.
  const initDragOrResize = (e, mode, chave = 'webcam') => {
    if (!ativo || !containerRef.current) return;
    e.stopPropagation();
    e.preventDefault();

    setIsInteracting(true);
    const containerRect = containerRef.current.getBoundingClientRect();
    const startX = e.clientX;
    const startY = e.clientY;
    const inicial = value[chave];
    // Altura / largura da área em pixels da imagem original.
    const proporcao = chave === 'webcam' ? 9 / 16 : PROPORCAO_PESSOA;
    const larguraMaxima = chave === 'webcam' ? 80 : 50;
    const [minX, maxX] = chave === 'esquerda' ? [0, 50] : chave === 'direita' ? [50, 100] : [0, 100];

    let currentX = inicial.x;
    let currentY = inicial.y;
    let currentW = inicial.width;
    let currentH = inicial.height;

    const onMouseMove = (moveEvent) => {
      const dxPercent = ((moveEvent.clientX - startX) / containerRect.width) * 100;
      const dyPercent = ((moveEvent.clientY - startY) / containerRect.height) * 100;

      if (mode === 'drag') {
        currentX = Math.max(minX, Math.min(maxX - currentW, inicial.x + dxPercent));
        currentY = Math.max(0, Math.min(100 - currentH, inicial.y + dyPercent));
      } else if (mode === 'resize') {
        currentW = Math.max(10, Math.min(larguraMaxima, inicial.width + dxPercent));
        currentH = currentW * proporcao * (containerRect.width / containerRect.height);

        if (currentX + currentW > maxX) {
          currentW = maxX - currentX;
          currentH = currentW * proporcao * (containerRect.width / containerRect.height);
        }
        if (currentY + currentH > 100) {
          currentH = 100 - currentY;
          currentW = currentH / proporcao * (containerRect.height / containerRect.width);
        }
      }

      atualizar({ [chave]: {
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

  const trocarLayout = (novo) => atualizar({ layout: novo });

  // O quadro mostrado agora vira a referência do plano aberto ('aberto') ou de um close ('close');
  // o backend calcula com o mesmo FFmpeg do render.
  const marcarReferencia = async (tipo) => {
    const midia = sourceVideoRef.current;
    if (!midia || !isVideo) return;
    setMarcandoReferencia(tipo);
    setErroReferencia('');
    try {
      const resposta = await fetch(`${API_BASE_URL}/studio/referencia`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ midia: mediaUrl, tempo: midia.currentTime || 0 }),
      });
      const dados = await resposta.json().catch(() => ({}));
      if (!resposta.ok) throw new Error(typeof dados.detail === 'string' ? dados.detail : t('estudio.referenciaErro'));
      atualizar({ referenciaOrigem: dados.origem || null, ...(tipo === 'close'
        ? { referenciaClose: dados.referencia, referenciaCloseMiniatura: dados.miniatura }
        : { referencia: dados.referencia, referenciaMiniatura: dados.miniatura }) });
    } catch (erro) {
      setErroReferencia(erro.message);
    } finally {
      setMarcandoReferencia(false);
    }
  };
  const inverterPessoas = () => atualizar({ direitaEmCima: !direitaEmCima });
  const rotuloLado = (lado) => t(lado === 'esquerda' ? 'estudio.ladoEsquerdo' : 'estudio.ladoDireito', {
    posicao: t((lado === 'direita') === direitaEmCima ? 'estudio.emCima' : 'estudio.embaixo'),
  });
  // Ordem no corte vertical: a metade de cima primeiro.
  const ordemCorte = direitaEmCima ? [['direita', direita], ['esquerda', esquerda]] : [['esquerda', esquerda], ['direita', direita]];

  return (
    <>
      {/* Seletor do tipo de enquadramento */}
      {ativo && (
        <div role="radiogroup" aria-label={t('estudio.layout')} className="flex items-center justify-center gap-1 rounded-xl border border-[#1b1528] bg-[#05070b]/80 p-1">
          {['webcam', 'podcast'].map(opcao => (
            <button key={opcao} type="button" role="radio" aria-checked={layout === opcao} onClick={() => trocarLayout(opcao)}
              className={`flex-1 rounded-lg px-3 py-1.5 text-xs font-bold transition ${layout === opcao
                ? 'bg-gradient-to-r from-[#9333ea]/40 to-[#00ffff]/25 text-white shadow'
                : 'text-slate-400 hover:bg-[#0e0a1a] hover:text-slate-200'}`}>
              {t(opcao === 'webcam' ? 'estudio.layoutWebcam' : 'estudio.layoutPodcast')}
            </button>
          ))}
        </div>
      )}

      {/* Prévia do Podcast: as duas metades do corte vertical, com a legenda na emenda */}
      {podcast && (
        <div className="flex flex-col items-center gap-2 bg-gradient-to-b from-[#070512] to-[#040308] border border-[#1b1528] p-2 rounded-2xl shadow-2xl">
          <button type="button" onClick={() => window.dispatchEvent(new CustomEvent('clippro:como-usar', { detail: 'podcast' }))}
            className="self-end rounded-full border border-cyan-400/50 px-2.5 py-0.5 text-[11px] font-bold text-cyan-300 hover:bg-cyan-950/40">
            ? {t('estudio.comoFuncionaPodcast')}
          </button>
          <div role="radiogroup" aria-label={t('estudio.perfilPodcast')} className="flex w-full items-center gap-1 rounded-lg bg-[#05070b]/80 p-1">
            {['dividido', 'centralizado', 'automatico'].map(opcao => (
              <button key={opcao} type="button" role="radio" aria-checked={perfil === opcao} onClick={() => setAba(opcao)}
                className={`flex-1 rounded-md px-2 py-1 text-[11px] font-bold transition ${perfil === opcao
                  ? 'bg-[#1b1528] text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'}`}>
                {t({ dividido: 'estudio.perfilDividido', centralizado: 'estudio.perfilCentralizado', automatico: 'estudio.perfilAutomatico' }[opcao])}
              </button>
            ))}
          </div>
          {/* No automático o corte alterna entre os perfis: uma prévia fixa só mostraria metade da história. */}
          {!automatico && <>
          <span className="text-[10px] font-mono text-slate-300 font-bold uppercase tracking-wider">{t('estudio.previaPodcast')}</span>
          <div className="relative w-32 overflow-hidden rounded-[10px] bg-black outline outline-1 outline-[#221838]" style={{ aspectRatio: 9 / 16 }}>
            {dividido && ordemCorte.map(([lado, box], indice) => (
              <div key={lado} className="relative h-1/2 w-full overflow-hidden">
                {isVideo && mediaReady && !hasMediaError
                  ? <RecorteMidia box={box} mediaUrl={mediaUrl}
                      videoRef={indice ? podcastVideo2Ref : podcastVideo1Ref} onError={onMediaError} />
                  : <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono text-slate-500">{rotuloLado(lado)}</span>}
              </div>
            ))}
            {centralizado && isVideo && mediaReady && !hasMediaError && (
              <RecorteMidia box={{ x: esquerdaMoldura, y: 0, width: larguraMoldura, height: 100 }}
                mediaUrl={mediaUrl} videoRef={podcastVideo1Ref} onError={onMediaError} />
            )}
            <span className={`absolute left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-black/60 px-1.5 py-0.5 text-[9px] font-bold text-yellow-300 ${dividido ? 'top-1/2 -translate-y-1/2' : 'bottom-3'}`}>{t('estudio.legendaAqui')}</span>
          </div>
          </>}
          {dividido && (
            <button type="button" onClick={inverterPessoas}
              className="text-[11px] text-cyan-300 hover:text-cyan-200">⇅ {t('estudio.inverterPessoas')}</button>
          )}
          <span className="text-center text-[11px] text-slate-500">{t(automatico ? 'estudio.dicaPodcastAutomatico' : dividido ? 'estudio.dicaPodcast' : 'estudio.dicaPodcastCentralizado')}</span>
          {automatico && (
            <div className="flex w-full flex-col items-center gap-2 rounded-xl border border-[#1b1528] bg-[#05070b]/80 p-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-300">{t('estudio.referenciaTitulo')}</span>
              <div className="grid w-full grid-cols-2 gap-2">
                {[['aberto', value.referenciaMiniatura, 'estudio.referenciaAberto', 'estudio.referenciaUsarAberto', 'outline-lime-400/60 border-lime-400/50 text-lime-300 hover:bg-lime-950/40'],
                  ['close', value.referenciaCloseMiniatura, 'estudio.referenciaClose', 'estudio.referenciaUsarClose', 'outline-amber-400/60 border-amber-400/50 text-amber-300 hover:bg-amber-950/40']]
                  .map(([tipo, miniatura, titulo, botao, cores]) => (
                  <div key={tipo} className="flex flex-col items-center gap-1.5">
                    <span className="text-[10px] font-bold text-slate-300">{t(titulo)}</span>
                    <span className="text-[10px] text-slate-500">→ {t(tipo === 'close' ? 'estudio.referenciaUsaClose' : 'estudio.referenciaUsaAberto')}</span>
                    {miniatura
                      ? <img src={miniatura} alt={t(titulo)} className={`w-full rounded-md outline outline-1 ${cores.split(' ')[0]}`} />
                      : <div className="flex aspect-video w-full items-center justify-center rounded-md border border-dashed border-slate-700 text-[10px] text-slate-500">{t('estudio.referenciaVazia')}</div>}
                    <button type="button" onClick={() => marcarReferencia(tipo)} disabled={!isVideo || !mediaReady || hasMediaError || Boolean(marcandoReferencia)}
                      className={`w-full rounded-lg border px-2 py-1 text-[11px] font-bold disabled:opacity-40 disabled:cursor-default ${cores.split(' ').slice(1).join(' ')}`}>
                      {marcandoReferencia === tipo ? t('estudio.referenciaMarcando') : t(botao)}
                    </button>
                    {miniatura && (
                      <button type="button" disabled={Boolean(marcandoReferencia)}
                        onClick={() => atualizar(tipo === 'close'
                          ? { referenciaClose: null, referenciaCloseMiniatura: null }
                          : { referencia: null, referenciaMiniatura: null })}
                        className="w-full rounded-lg border border-rose-400/50 px-2 py-1 text-[11px] font-bold text-rose-300 hover:bg-rose-950/40 disabled:opacity-40 disabled:cursor-default">✕ {t('estudio.referenciaLimpar')}</button>
                    )}
                  </div>
                ))}
              </div>
              <span className={`text-center text-[11px] ${value.referenciaMiniatura ? 'text-slate-500' : 'text-amber-300'}`}>
                {t(value.referenciaMiniatura ? 'estudio.referenciaDica' : 'estudio.referenciaSem')}
              </span>
              {erroReferencia && <span className="text-center text-[11px] text-rose-300">{erroReferencia}</span>}
            </div>
          )}
        </div>
      )}

      {/* 🔍 LUPA PIP */}
      {ativo && !podcast && (
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

      {ativo && !podcast && (
        <label className="block text-xs text-slate-300">{t('estudio.larguraWebcam', { valor: webcamBox.width.toFixed(1) })}
          <input type="range" min="5" max="80" step="0.1" value={webcamBox.width} disabled={!mediaReady}
            onChange={e => {
              const width = Math.min(Number(e.target.value), 100 - webcamBox.x, (100 - webcamBox.y) * 16 / 9 / mediaAspect);
              atualizar({ webcam: { ...webcamBox, width, height: width * 9 / 16 * mediaAspect } });
            }} className="mt-2 block w-full accent-cyan-400 disabled:opacity-40" />
        </label>
      )}

      {mediaReady && !hasMediaError && !dividido && !automatico && (
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
          {mediaReady && !hasMediaError && larguraMoldura < 100 && !dividido && !automatico && (
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

          {/* Lados do Podcast: áreas 9:8, cada uma presa à sua metade do vídeo */}
          {dividido && [['esquerda', esquerda, 'border-cyan-300/90 bg-cyan-400/5', 'from-cyan-300 to-sky-600'],
                       ['direita', direita, 'border-amber-300/90 bg-amber-400/5', 'from-amber-300 to-orange-600']]
            .map(([chave, box, borda, alca]) => (
            <div
              key={chave}
              onMouseDown={(e) => initDragOrResize(e, 'drag', chave)}
              style={{ left: `${box.x}%`, top: `${box.y}%`, width: `${box.width}%`, height: `${box.height}%` }}
              className={`absolute border-2 ${borda} rounded-lg cursor-move flex items-start justify-center z-10 box-border will-change-[left,top,width,height]`}
            >
              <span className="mt-1 bg-black/60 px-2 py-0.5 rounded text-[10px] font-mono text-white font-bold pointer-events-none truncate">{rotuloLado(chave)}</span>
              <div
                onMouseDown={(e) => initDragOrResize(e, 'resize', chave)}
                className={`absolute bottom-0 right-0 w-6 h-6 bg-gradient-to-br ${alca} rounded-tl-md cursor-se-resize hover:brightness-125 transition shadow-md`}
                title={t('estudio.dicaRedimensionarPessoa')}
              />
            </div>
          ))}

          {/* 🎯 QUADRADO ROSA EM GRADIENTE */}
          {ativo && !podcast && (
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
