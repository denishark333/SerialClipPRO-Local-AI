import React, { useEffect, useRef, useState } from 'react';
import { apiFetch, API_BASE_URL, MEDIA_BASE_URL } from '../../api';
import { ClipThumbnail } from '../layout/ClipThumbnail';
import { clipIdentity } from '../../clipIdentity';
import { useDialog } from '../layout/useDialog';

function TempoLegenda({ label, value, onChange }) {
  const [draft, setDraft] = useState(null);
  return <input aria-label={label} type="number" min="0" step="0.01"
    value={draft ?? value.toFixed(2)}
    onFocus={() => setDraft(value.toFixed(2))}
    onChange={e => {
      setDraft(e.target.value);
      if (e.target.value !== '' && Number.isFinite(e.target.valueAsNumber) && e.target.valueAsNumber >= 0) {
        onChange(Number(e.target.valueAsNumber.toFixed(2)));
      }
    }}
    onBlur={() => setDraft(null)}
    className="mt-1 block w-28 rounded-lg border border-purple-500/60 bg-[#090612] px-3 py-2 text-sm font-semibold text-cyan-200 outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30" />;
}

export function ReviewTab() {
  const [clips, setClips] = useState([]);
  const [corte, setCorte] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [time, setTime] = useState(0);
  const [origem, setOrigem] = useState('salvos');
  const modal = useRef(null);
  const player = useRef(null);
  const estavaExecutando = useRef(false);
  const { ask } = useDialog();
  async function carregar() {
    try { setClips(await (await apiFetch('/revisao/clips')).json()); }
    catch (e) { setMessage(e.message); }
  }
  useEffect(() => { const timer = setTimeout(carregar, 0); return () => clearTimeout(timer); }, []);
  useEffect(() => {
    if (corte && !modal.current.open) modal.current.showModal();
    if (!corte && modal.current.open) modal.current.close();
  }, [corte]);
  useEffect(() => {
    let active = true;
    let timer;
    async function poll() {
      try {
        const status = await (await apiFetch('/revisao/status')).json();
        if (!active) return;
        setBusy(status.executando);
        if (status.executando) setMessage('Reaplicando composição e legendas. Aguarde para iniciar outro pipeline.');
        else if (estavaExecutando.current && !status.erro) setMessage('Revisão concluída. Confira o vídeo atualizado na galeria. Para atualizar uma exportação, exporte novamente.');
        estavaExecutando.current = status.executando;
        if (status.erro) setMessage(`Revisão não concluída: ${status.erro}`);
      } catch (e) { if (active) setMessage(e.message); }
      finally { if (active) timer = setTimeout(poll, 1500); }
    }
    poll();
    return () => { active = false; clearTimeout(timer); };
  }, []);
  async function abrir(id) {
    try {
      setCorte(await (await apiFetch(`/revisao/clips/${id}`)).json());
      setTime(0); setMessage('');
    } catch (e) { setMessage(e.message); }
  }
  async function fechar() {
    if (await ask('Fechar a edição? Alterações não aplicadas serão descartadas.', 'Revisão de legendas')) {
      player.current?.pause(); setCorte(null);
    }
  }
  function alterar(i, chave, valor) {
    setCorte(prev => ({ ...prev, legendas: prev.legendas.map((g, n) => n === i ? { ...g, [chave]: valor } : g) }));
  }
  async function aplicar() {
    if (!await ask('Gerar novamente este corte com as legendas corrigidas? O vídeo salvo será substituído; cópias exportadas permanecem iguais.', 'Aplicar revisão')) return;
    try {
      player.current?.pause();
      await apiFetch(`/revisao/clips/${corte.id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ revisao: corte.revisao, legendas: corte.legendas }) });
      setBusy(true); setCorte(null); setMessage('Revisão iniciada. Ao terminar, confira o corte na galeria e exporte novamente se desejar.');
    } catch (e) { setMessage(e.message); }
  }
  const atual = corte?.legendas.find(g => time >= g.start && time < g.end);
  return <section className="rounded-2xl border border-purple-700/60 bg-gradient-to-br from-purple-950/30 via-[#0a0712] to-cyan-950/20 p-6">
    <h2 className="text-center text-2xl font-bold text-purple-100">Revisão de legendas</h2>
    <p className="text-center text-slate-300 my-4 leading-relaxed">Opcional: corrija o texto e os tempos, depois reaplique ao corte original. Vídeos antigos sem base de revisão continuam disponíveis na galeria.</p>
    <p role="status" className="text-cyan-300 mb-3">{message}</p>
    <button onClick={carregar} className="rounded-xl border border-purple-400/60 bg-gradient-to-r from-purple-600 to-cyan-700 px-5 py-3 mb-5 font-bold hover:brightness-110 focus-visible:outline-2 focus-visible:outline-cyan-400">Atualizar lista</button>
    {busy && <p role="status">Renderização da revisão em andamento…</p>}
    {!clips.length && <p>Nenhum corte salvo ou exportado encontrado.</p>}
    <label className="block mb-4 text-sm">Exibir: <select value={origem} onChange={e => setOrigem(e.target.value)} className="bg-[#0e0a1a] border border-purple-900 rounded p-2">
      <option value="salvos">Salvos — mesma ordem da galeria</option>
      <option value="exportados">Somente em Exportados</option>
    </select></label>
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
      {clips.filter(c => origem === 'salvos' ? c.origens.includes('salvo') : !c.origens.includes('salvo')).map(c => <article key={c.nome} className="overflow-hidden rounded-xl border border-[#1f1633] bg-[#0e0a1a] transition-colors hover:border-purple-500/60">
        <button disabled={!c.id || busy} onClick={() => abrir(c.id)} aria-label={`Revisar legendas de ${c.nome}`} className="block w-full focus-visible:outline-2 focus-visible:outline-cyan-400 focus-visible:outline-offset-[-2px]">
          <ClipThumbnail src={`${MEDIA_BASE_URL}/${c.origens.includes('salvo') ? 'videos' : 'exportados'}/${encodeURIComponent(c.nome)}`} />
        </button>
        <div className="p-3">
          <p className="text-sm font-bold text-cyan-300">{clipIdentity(c.nome).titulo}</p>
          <p className="text-[10px] text-slate-400">{clipIdentity(c.nome).sessao}</p>
          <p className="mt-1 truncate text-[10px] text-slate-400" title={c.nome}>{c.nome}</p>
          <p className="text-xs text-slate-400 my-2">{c.origens.join(' • ')}</p>
          <button disabled={!c.id || busy} onClick={() => abrir(c.id)} className="w-full bg-purple-700 hover:bg-purple-600 rounded-lg px-2 py-2 text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed">{c.id ? 'Revisar legendas' : 'Base indisponível'}</button>
        </div>
      </article>)}
    </div>
    <dialog ref={modal} onCancel={e => { e.preventDefault(); fechar(); }} aria-labelledby="titulo-revisao"
      className="m-auto w-[97vw] max-w-[1440px] max-h-[95vh] overflow-y-auto rounded-2xl border border-purple-500 bg-[#0e0a1a] text-white p-4 sm:p-6 shadow-2xl shadow-purple-950/60 backdrop:bg-black/80">
      {corte && <>
        <div className="flex items-center justify-between gap-3 mb-5 border-b border-purple-800/60 pb-4"><h3 id="titulo-revisao" className="text-xl font-bold">Editar legendas</h3><button onClick={fechar} className="rounded-lg border border-purple-500/60 bg-purple-950 px-4 py-2 text-sm font-semibold hover:bg-purple-900 focus-visible:outline-2 focus-visible:outline-cyan-400">Fechar</button></div>
        <p role="status" className="text-cyan-300">{message}</p>
        <div className="grid lg:grid-cols-2 gap-6 items-start">
          <div className="min-w-0"><div className="relative overflow-hidden rounded-xl border border-purple-800/60 bg-black">
            <video ref={player} controls preload="metadata" className="w-full" src={`${API_BASE_URL}/revisao/clips/${corte.id}/original`} onTimeUpdate={e => setTime(e.currentTarget.currentTime)} />
            <p className="pointer-events-none absolute bottom-14 left-2 right-2 text-center text-yellow-300 font-bold text-xl" style={{ textShadow: '1px 1px 3px black' }}>{atual?.text}</p>
          </div><p className="text-xs text-slate-400 mt-3">Original horizontal para conferir a fala. A aplicação mantém webcam, marca e enquadramento salvos. O texto sobreposto é uma prévia de edição.</p>
            <p className="text-sm text-cyan-300 mt-2">Posição atual: {time.toFixed(2)} s</p>
            <p className="text-xs text-slate-400 mt-2">Tempos exibidos em centésimos de segundo. Pause na fala desejada e use a posição atual como início ou fim. Tempos não editados mantêm a precisão original.</p>
          </div>
          <div className="min-w-0 rounded-xl border border-purple-500/50 bg-purple-950/20 p-3 sm:p-4">
            <h4 className="mb-1 text-base font-bold text-purple-200">Texto e sincronização</h4>
            <p className="mb-4 text-xs text-slate-300">Ajuste os tempos e o texto de cada legenda.</p>
            <div className="max-h-[62vh] overflow-y-auto space-y-4 pr-2">
            {corte.legendas.map((g,i) => <div key={i} className={`rounded-xl border p-4 ${atual === g ? 'border-cyan-400 bg-cyan-950/30' : 'border-purple-700/60 bg-[#151024]'}`}>
              <p className="mb-3 text-xs font-bold uppercase tracking-wide text-cyan-300">Legenda {i+1}</p>
              <div className="flex flex-wrap items-end gap-3 text-xs text-slate-200 mb-3">
                <label>Início (s)<TempoLegenda label={`Início da legenda ${i+1}`} value={g.start} onChange={value => alterar(i,'start',value)} /></label>
                <label>Fim (s)<TempoLegenda label={`Fim da legenda ${i+1}`} value={g.end} onChange={value => alterar(i,'end',value)} /></label>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                <button className="rounded-lg border border-purple-400/60 bg-purple-900 px-3 py-2 text-xs font-semibold hover:bg-purple-700 focus-visible:outline-2 focus-visible:outline-cyan-400" onClick={() => alterar(i, 'start', Number(player.current.currentTime.toFixed(2)))}>Início na posição atual</button>
                <button className="rounded-lg border border-purple-400/60 bg-purple-900 px-3 py-2 text-xs font-semibold hover:bg-purple-700 focus-visible:outline-2 focus-visible:outline-cyan-400" onClick={() => alterar(i, 'end', Number(player.current.currentTime.toFixed(2)))}>Fim na posição atual</button>
                <button className="rounded-lg border border-cyan-400/60 bg-cyan-950 px-3 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-900 focus-visible:outline-2 focus-visible:outline-cyan-400" onClick={() => { player.current.currentTime = g.start; player.current.play().catch(() => {}); }}>Ouvir trecho</button>
                <button className="rounded-lg border border-rose-400/50 bg-rose-950/60 px-3 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-900 focus-visible:outline-2 focus-visible:outline-rose-400" onClick={() => setCorte(prev => ({ ...prev, legendas: prev.legendas.filter((_,n) => n !== i) }))}>Excluir</button>
              </div>
              <label className="block text-xs font-semibold text-purple-200">Texto da legenda
                <textarea rows={2} aria-label={`Texto da legenda ${i+1}`} maxLength={500} value={g.text} onChange={e => alterar(i,'text',e.target.value.replace(/[\r\n]+/g, ' '))} className="mt-2 w-full resize-y rounded-lg border border-purple-500/60 bg-[#090612] p-3 text-base text-white outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30" />
              </label>
            </div>)}
            <button className="w-full rounded-lg border border-dashed border-cyan-400/70 bg-cyan-950/40 px-4 py-3 text-sm font-semibold text-cyan-200 hover:bg-cyan-900/50 focus-visible:outline-2 focus-visible:outline-cyan-400" onClick={() => setCorte(prev => ({ ...prev, legendas: [...prev.legendas, { start: time, end: Math.min(prev.duracao,time+1), text: 'Nova legenda' }].sort((a,b) => a.start-b.start) }))}>+ Adicionar legenda no tempo atual</button>
            </div>
          </div>
        </div>
        <div className="mt-5 border-t border-purple-800/60 pt-4"><button disabled={busy} onClick={aplicar} className="w-full sm:w-auto bg-purple-600 hover:bg-purple-500 border border-purple-400/60 rounded-xl px-6 py-3 text-sm font-bold shadow-lg shadow-purple-950/50 focus-visible:outline-2 focus-visible:outline-cyan-400 disabled:opacity-40">Aplicar e gerar corte corrigido</button></div>
      </>}
    </dialog>
  </section>;
}
