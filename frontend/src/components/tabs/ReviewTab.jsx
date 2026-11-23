import React, { useEffect, useRef, useState } from 'react';
import { apiFetch, API_BASE_URL, MEDIA_BASE_URL } from '../../api';
import { ClipThumbnail } from '../layout/ClipThumbnail';
import { clipIdentity } from '../../clipIdentity';
import { useDialog } from '../layout/useDialog';
import { useI18n, useTAtual } from '../../i18n/useI18n';
import { EditorEnquadramento } from '../studio/EditorEnquadramento';
import { configParaEnquadramento, enquadramentoParaConfig } from '../studio/enquadramento';

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
  // Enquadramento individual do corte aberto; só vai no pedido se for alterado.
  const [enquadramento, setEnquadramento] = useState(null);
  const [enquadramentoAlterado, setEnquadramentoAlterado] = useState(false);
  const [erroOriginal, setErroOriginal] = useState(false);
  const modal = useRef(null);
  const player = useRef(null);
  const estavaExecutando = useRef(false);
  const { ask } = useDialog();
  const { t } = useI18n();
  const tAtual = useTAtual();
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
        if (status.executando) setMessage(tAtual.current('revisao.reaplicando'));
        else if (estavaExecutando.current && !status.erro) setMessage(tAtual.current('revisao.concluida'));
        estavaExecutando.current = status.executando;
        if (status.erro) setMessage(tAtual.current('revisao.naoConcluida', { erro: status.erro }));
      } catch (e) { if (active) setMessage(e.message); }
      finally { if (active) timer = setTimeout(poll, 1500); }
    }
    poll();
    return () => { active = false; clearTimeout(timer); };
  }, [tAtual]);
  async function abrir(id) {
    try {
      const dados = await (await apiFetch(`/revisao/clips/${id}`)).json();
      setCorte(dados);
      setEnquadramento(configParaEnquadramento(dados.config));
      setEnquadramentoAlterado(false); setErroOriginal(false);
      setTime(0); setMessage('');
    } catch (e) { setMessage(e.message); }
  }
  async function fechar() {
    if (await ask(t('revisao.fecharPergunta'), t('revisao.titulo'))) {
      player.current?.pause(); setCorte(null);
    }
  }
  function alterar(i, chave, valor) {
    setCorte(prev => ({ ...prev, legendas: prev.legendas.map((g, n) => n === i ? { ...g, [chave]: valor } : g) }));
  }
  function alterarEnquadramento(valor) {
    setEnquadramento(valor); setEnquadramentoAlterado(true);
  }
  async function aplicar() {
    const pergunta = enquadramentoAlterado ? 'revisao.aplicarPerguntaEnquadramento' : 'revisao.aplicarPergunta';
    if (!await ask(t(pergunta), t('revisao.aplicarTitulo'))) return;
    try {
      player.current?.pause();
      await apiFetch(`/revisao/clips/${corte.id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ revisao: corte.revisao, legendas: corte.legendas,
          ...(enquadramentoAlterado && { enquadramento: enquadramentoParaConfig(enquadramento) }) }) });
      setBusy(true); setCorte(null); setMessage(t('revisao.iniciada'));
    } catch (e) { setMessage(e.message); }
  }
  const atual = corte?.legendas.find(g => time >= g.start && time < g.end);
  return <section className="rounded-2xl border border-purple-700/60 bg-gradient-to-br from-purple-950/30 via-[#0a0712] to-cyan-950/20 p-6">
    <h2 className="text-center text-2xl font-bold text-purple-100">{t('revisao.titulo')}</h2>
    <p className="text-center text-slate-300 my-4 leading-relaxed">{t('revisao.descricao')}</p>
    <p role="status" className="text-cyan-300 mb-3">{message}</p>
    <button onClick={carregar} className="rounded-xl border border-purple-400/60 bg-gradient-to-r from-purple-600 to-cyan-700 px-5 py-3 mb-5 font-bold hover:brightness-110 focus-visible:outline-2 focus-visible:outline-cyan-400">{t('revisao.atualizarLista')}</button>
    {busy && <p role="status">{t('revisao.emAndamento')}</p>}
    {!clips.length && <p>{t('revisao.nenhum')}</p>}
    <label className="block mb-4 text-sm">{t('revisao.exibir')} <select value={origem} onChange={e => setOrigem(e.target.value)} className="bg-[#0e0a1a] border border-purple-900 rounded p-2">
      <option value="salvos">{t('revisao.filtroSalvos')}</option>
      <option value="exportados">{t('revisao.filtroExportados')}</option>
    </select></label>
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
      {clips.filter(c => origem === 'salvos' ? c.origens.includes('salvo') : !c.origens.includes('salvo')).map(c => <article key={c.nome} className="overflow-hidden rounded-xl border border-[#1f1633] bg-[#0e0a1a] transition-colors hover:border-purple-500/60">
        <button disabled={!c.id || busy} onClick={() => abrir(c.id)} aria-label={t('revisao.revisarDe', { nome: c.nome })} className="block w-full focus-visible:outline-2 focus-visible:outline-cyan-400 focus-visible:outline-offset-[-2px]">
          <ClipThumbnail src={`${MEDIA_BASE_URL}/${c.origens.includes('salvo') ? 'videos' : 'exportados'}/${encodeURIComponent(c.nome)}`} />
        </button>
        <div className="p-3">
          <p className="text-sm font-bold text-cyan-300">{clipIdentity(c.nome, t).titulo}</p>
          <p className="text-[10px] text-slate-400">{clipIdentity(c.nome, t).sessao}</p>
          <p className="mt-1 truncate text-[10px] text-slate-400" title={c.nome}>{c.nome}</p>
          <p className="text-xs text-slate-400 my-2">{c.origens.map(o => t(`revisao.origens.${o}`)).join(' • ')}</p>
          <button disabled={!c.id || busy} onClick={() => abrir(c.id)} className="w-full bg-purple-700 hover:bg-purple-600 rounded-lg px-2 py-2 text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed">{c.id ? t('revisao.revisar') : t('revisao.semBase')}</button>
        </div>
      </article>)}
    </div>
    <dialog ref={modal} onCancel={e => { e.preventDefault(); fechar(); }} aria-labelledby="titulo-revisao"
      className="m-auto w-[97vw] max-w-[1440px] max-h-[95vh] overflow-y-auto rounded-2xl border border-purple-500 bg-[#0e0a1a] text-white p-4 sm:p-6 shadow-2xl shadow-purple-950/60 backdrop:bg-black/80">
      {corte && <>
        <div className="flex items-center justify-between gap-3 mb-5 border-b border-purple-800/60 pb-4"><h3 id="titulo-revisao" className="text-xl font-bold">{t('revisao.editar')}</h3><button onClick={fechar} className="rounded-lg border border-purple-500/60 bg-purple-950 px-4 py-2 text-sm font-semibold hover:bg-purple-900 focus-visible:outline-2 focus-visible:outline-cyan-400">{t('revisao.fechar')}</button></div>
        <p role="status" className="text-cyan-300">{message}</p>
        <div className="grid lg:grid-cols-2 gap-6 items-start">
          <div className="min-w-0"><div className="relative overflow-hidden rounded-xl border border-purple-800/60 bg-black">
            <video ref={player} controls preload="metadata" className="w-full" src={`${API_BASE_URL}/revisao/clips/${corte.id}/original`} onTimeUpdate={e => setTime(e.currentTarget.currentTime)} />
            <p className="pointer-events-none absolute bottom-14 left-2 right-2 text-center text-yellow-300 font-bold text-xl" style={{ textShadow: '1px 1px 3px black' }}>{atual?.text}</p>
          </div><p className="text-xs text-slate-400 mt-3">{t('revisao.dicaOriginal')}</p>
            <p className="text-sm text-cyan-300 mt-2">{t('revisao.posicaoAtual', { tempo: time.toFixed(2) })}</p>
            <p className="text-xs text-slate-400 mt-2">{t('revisao.dicaTempos')}</p>
            <details className="mt-4 rounded-xl border border-purple-500/50 bg-purple-950/20 p-3 sm:p-4">
              <summary className="cursor-pointer text-base font-bold text-purple-200">
                {t('revisao.enquadramento')}
                {enquadramentoAlterado && <span className="ml-2 text-xs font-normal text-cyan-300">· {t('revisao.enquadramentoAlterado')}</span>}
              </summary>
              <div className="mt-3 flex flex-col gap-2 text-slate-200">
                <p className="text-xs text-slate-300">{t('revisao.dicaEnquadramento')}</p>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={enquadramento.ativo} className="accent-cyan-400 h-4 w-4"
                      onChange={e => alterarEnquadramento({ ...enquadramento, ativo: e.target.checked })} />
                    {t('revisao.webcamNoCorte')}
                  </label>
                  <button type="button" disabled={!enquadramentoAlterado}
                    onClick={() => { setEnquadramento(configParaEnquadramento(corte.config)); setEnquadramentoAlterado(false); }}
                    className="text-xs text-cyan-300 hover:text-cyan-200 disabled:opacity-40 disabled:cursor-default">{t('revisao.desfazerEnquadramento')}</button>
                </div>
                <EditorEnquadramento value={enquadramento} onChange={alterarEnquadramento}
                  mediaUrl={`${API_BASE_URL}/revisao/clips/${corte.id}/original`} isVideo
                  hasMediaError={erroOriginal} onMediaError={() => setErroOriginal(true)} />
              </div>
            </details>
          </div>
          <div className="min-w-0 rounded-xl border border-purple-500/50 bg-purple-950/20 p-3 sm:p-4">
            <h4 className="mb-1 text-base font-bold text-purple-200">{t('revisao.textoSincronizacao')}</h4>
            <p className="mb-4 text-xs text-slate-300">{t('revisao.dicaLegendas')}</p>
            <div className="max-h-[62vh] overflow-y-auto space-y-4 pr-2">
            {corte.legendas.map((g,i) => <div key={i} className={`rounded-xl border p-4 ${atual === g ? 'border-cyan-400 bg-cyan-950/30' : 'border-purple-700/60 bg-[#151024]'}`}>
              <p className="mb-3 text-xs font-bold uppercase tracking-wide text-cyan-300">{t('revisao.legenda', { numero: i + 1 })}</p>
              <div className="flex flex-wrap items-end gap-3 text-xs text-slate-200 mb-3">
                <label>{t('revisao.inicio')}<TempoLegenda label={t('revisao.inicioDe', { numero: i + 1 })} value={g.start} onChange={value => alterar(i,'start',value)} /></label>
                <label>{t('revisao.fim')}<TempoLegenda label={t('revisao.fimDe', { numero: i + 1 })} value={g.end} onChange={value => alterar(i,'end',value)} /></label>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                <button className="rounded-lg border border-purple-400/60 bg-purple-900 px-3 py-2 text-xs font-semibold hover:bg-purple-700 focus-visible:outline-2 focus-visible:outline-cyan-400" onClick={() => alterar(i, 'start', Number(player.current.currentTime.toFixed(2)))}>{t('revisao.inicioAqui')}</button>
                <button className="rounded-lg border border-purple-400/60 bg-purple-900 px-3 py-2 text-xs font-semibold hover:bg-purple-700 focus-visible:outline-2 focus-visible:outline-cyan-400" onClick={() => alterar(i, 'end', Number(player.current.currentTime.toFixed(2)))}>{t('revisao.fimAqui')}</button>
                <button className="rounded-lg border border-cyan-400/60 bg-cyan-950 px-3 py-2 text-xs font-semibold text-cyan-200 hover:bg-cyan-900 focus-visible:outline-2 focus-visible:outline-cyan-400" onClick={() => { player.current.currentTime = g.start; player.current.play().catch(() => {}); }}>{t('revisao.ouvir')}</button>
                <button className="rounded-lg border border-rose-400/50 bg-rose-950/60 px-3 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-900 focus-visible:outline-2 focus-visible:outline-rose-400" onClick={() => setCorte(prev => ({ ...prev, legendas: prev.legendas.filter((_,n) => n !== i) }))}>{t('revisao.excluir')}</button>
              </div>
              <label className="block text-xs font-semibold text-purple-200">{t('revisao.texto')}
                <textarea rows={2} aria-label={t('revisao.textoDe', { numero: i + 1 })} maxLength={500} value={g.text} onChange={e => alterar(i,'text',e.target.value.replace(/[\r\n]+/g, ' '))} className="mt-2 w-full resize-y rounded-lg border border-purple-500/60 bg-[#090612] p-3 text-base text-white outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30" />
              </label>
            </div>)}
            <button className="w-full rounded-lg border border-dashed border-cyan-400/70 bg-cyan-950/40 px-4 py-3 text-sm font-semibold text-cyan-200 hover:bg-cyan-900/50 focus-visible:outline-2 focus-visible:outline-cyan-400" onClick={() => setCorte(prev => ({ ...prev, legendas: [...prev.legendas, { start: time, end: Math.min(prev.duracao,time+1), text: t('revisao.novaLegenda') }].sort((a,b) => a.start-b.start) }))}>+ {t('revisao.adicionar')}</button>
            </div>
          </div>
        </div>
        <div className="mt-5 border-t border-purple-800/60 pt-4"><button disabled={busy} onClick={aplicar} className="w-full sm:w-auto bg-purple-600 hover:bg-purple-500 border border-purple-400/60 rounded-xl px-6 py-3 text-sm font-bold shadow-lg shadow-purple-950/50 focus-visible:outline-2 focus-visible:outline-cyan-400 disabled:opacity-40">{t('revisao.aplicar')}</button></div>
      </>}
    </dialog>
  </section>;
}
