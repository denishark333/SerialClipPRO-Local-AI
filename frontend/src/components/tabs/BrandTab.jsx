import { useDialog } from '../layout/useDialog';
import React, { useEffect, useState } from 'react';
import { apiFetch, API_BASE_URL } from '../../api';
import { useI18n } from '../../i18n/useI18n';

// Textos em marca.estilos.*; o exemplo é "antes / palavra falada / depois" para destacar a do meio.
const ESTILOS_LEGENDA = ['destaque', 'classico'];

function ExemploLegenda({ id, t }) {
  const [antes, palavra, depois] = ['antes', 'palavra', 'depois'].map(parte => t(`marca.exemplo.${parte}`));
  if (id !== 'destaque') return `${antes} ${palavra} ${depois}`;
  return <>{antes} <span className="inline-block text-[1.3em] leading-none">{palavra}</span> {depois}</>;
}

export function BrandTab() {
  const { ask } = useDialog();
  const { t } = useI18n();
  const [config, setConfig] = useState(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [aspect, setAspect] = useState(1);
  useEffect(() => {
    let active = true;
    apiFetch('/marca').then(r => r.json()).then(data => { if (active) setConfig(data); })
      .catch(e => { if (active) setMessage(e.message); });
    return () => { active = false; };
  }, []);
  async function action(callback, success) {
    setBusy(true); setMessage('');
    try { setConfig(await (await callback()).json()); setRevision(Date.now()); setMessage(success); }
    catch (e) { setMessage(e.message); }
    finally { setBusy(false); }
  }
  // Salva só o estilo, sem gravar ajustes de posição da marca que ainda não foram salvos.
  async function salvarEstilo(estilo) {
    setBusy(true); setMessage('');
    try {
      const atual = await (await apiFetch('/marca')).json();
      const salvo = await (await apiFetch('/marca', { method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...atual, estilo_legenda: estilo }) })).json();
      setConfig(prev => ({ ...prev, estilo_legenda: salvo.estilo_legenda }));
      setMessage(t('marca.estiloSalvo'));
    } catch (e) { setMessage(e.message); }
    finally { setBusy(false); }
  }
  const width = config ? config.largura_pct : 35;
  const height = Math.min(100, width * 9 / 16 / aspect);
  const effectiveWidth = Math.min(width, height * 16 / 9 * aspect);
  const left = config ? (100 - effectiveWidth) * config.x_pct / 100 : 0;
  const top = config ? (config.posicao === 'divisao' ? Math.max(0, Math.min(100 - height, 31.640625 - height / 2)) : (100 - height) * config.y_pct / 100) : 0;
  return <section className="w-full lg:w-[94%] mx-auto bg-[#0a0712] border border-[#1b1528] p-6 rounded-2xl">
    <h2 className="text-lg font-bold">{t('marca.titulo')}</h2>
    <p className="text-sm text-slate-400 my-3">{t('marca.descricao')}</p>
    <p role="status" className="text-sm text-cyan-300">{message}</p>
    {config && <div className="grid gap-6 mt-6 items-start lg:grid-cols-2 xl:grid-cols-[minmax(220px,0.65fr)_minmax(190px,0.6fr)_minmax(230px,0.85fr)_minmax(280px,1.15fr)]">
      <fieldset disabled={busy} className="min-w-0 flex flex-col gap-5 rounded-xl border border-purple-800/60 bg-purple-950/20 p-5">
        <label>{t('marca.imagem')}
          <input aria-label={t('marca.selecionarImagem')} type="file" accept="image/png" className="block w-full mt-3 text-sm text-slate-300 file:mr-3 file:rounded-lg file:border file:border-cyan-400/50 file:bg-purple-700 file:px-4 file:py-3 file:font-bold file:text-white hover:file:bg-purple-600 cursor-pointer" onChange={event => {
            const file = event.target.files[0];
            if (!file) return;
            if (file.size > 5 * 1024 * 1024) { setMessage(t('marca.limite')); return; }
            action(() => apiFetch('/marca/imagem', { method: 'PUT', headers: { 'Content-Type': 'image/png' }, body: file }), t('marca.imagemEnviada'));
            event.target.value = '';
          }} />
        </label>
        <label><input type="checkbox" checked={config.ativo} disabled={!config.tem_imagem} onChange={e => setConfig({ ...config, ativo: e.target.checked })} /> {t('marca.aplicar')}</label>
        <label>{t('marca.posicao')} <select className="bg-slate-900 p-2" value={config.posicao} onChange={e => setConfig({ ...config, posicao: e.target.value })}>
          <option value="divisao">{t('marca.divisao')}</option><option value="manual">{t('marca.manual')}</option>
        </select></label>
        {[['largura_pct', 5, 80], ['x_pct', 0, 100], ['y_pct', 0, 100]].map(([key, min, max]) =>
          <label key={key}>{t(`marca.controles.${key}`)}: {config[key]}%<input className="block w-full" type="range" min={min} max={max} value={config[key]} onChange={e => setConfig({ ...config, [key]: Number(e.target.value) })} /></label>)}
        <button className="bg-gradient-to-r from-purple-600 to-cyan-600 rounded-xl p-3 font-bold hover:brightness-110" onClick={() => action(() => apiFetch('/marca', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config) }), config.ativo ? t('marca.salvaAtiva') : t('marca.salvaInativa'))}>{t('marca.salvar')}</button>
        <button disabled={!config.tem_imagem} onClick={async () => { if (await ask(t('marca.removerPergunta'), t('marca.titulo'))) action(() => apiFetch('/marca', { method: 'DELETE' }), t('marca.removida')); }}>{t('marca.remover')}</button>
      </fieldset>
      <div>
        <div className="relative w-full max-w-72 mx-auto aspect-[9/16] bg-slate-900 overflow-hidden rounded-xl border border-purple-500/40">
          {config.posicao === 'divisao' && <div className="absolute top-0 w-full aspect-video bg-slate-700 flex items-center justify-center text-xs">{t('marca.webcamIlustrativa')}</div>}
          <span className="absolute bottom-1/3 w-full text-center text-slate-500 text-xs">{t('marca.conteudoCorte')}</span>
          {config.tem_imagem && <img src={`${API_BASE_URL}/marca/imagem?t=${revision}`} alt={t('marca.altMarca')} onLoad={e => setAspect(e.currentTarget.naturalWidth / e.currentTarget.naturalHeight)} className="absolute" style={{ width: `${effectiveWidth}%`, height: `${height}%`, left: `${left}%`, top: `${top}%`, opacity: config.ativo ? 1 : 0.35 }} />}
        </div>
        <p className="text-xs text-slate-400 max-w-56 mt-2">{t('marca.simulacao')}</p>
      </div>
      <aside className="rounded-xl border border-cyan-800/50 bg-gradient-to-br from-purple-950/40 to-cyan-950/20 p-5 space-y-4 text-sm text-slate-300 leading-relaxed">
        <h3 className="text-lg font-bold text-cyan-200">{t('marca.identidade')}</h3>
        <p>{t('marca.identidadeTexto')}</p>
        <ol className="list-decimal pl-5 space-y-3"><li>{t('marca.passo1')}</li><li>{t('marca.passo2')}</li><li>{t('marca.passo3')}</li></ol>
        <p>{t('marca.automatica')}</p>
        <p className="rounded-lg border border-purple-600/40 bg-purple-950/40 p-3">{t('marca.mudancas')}</p>
      </aside>
      <fieldset disabled={busy} className="min-w-0 rounded-xl border border-purple-800/60 bg-purple-950/20 p-5">
        <legend className="px-2 text-lg font-bold">{t('marca.estiloTitulo')}</legend>
        <p className="text-xs text-slate-400 mb-4">{t('marca.estiloTexto')}</p>
        <div className="grid grid-cols-2 gap-3">
          {ESTILOS_LEGENDA.map(id =>
            <label key={id} className={`cursor-pointer rounded-lg border p-4 flex flex-col gap-3 ${config.estilo_legenda === id ? 'border-cyan-400 bg-cyan-950/30' : 'border-purple-700/60 bg-[#151024] hover:border-purple-500'}`}>
              <span className="flex items-center gap-2 text-sm font-semibold">
                <input type="radio" name="estilo_legenda" value={id} checked={config.estilo_legenda === id}
                  onChange={() => salvarEstilo(id)} />
                {t(`marca.estilos.${id}.nome`)}
              </span>
              <span aria-hidden="true" className="block rounded-md bg-slate-800 px-2 py-5 text-center text-xl leading-normal font-black uppercase tracking-wide text-[#ffff00]"
                style={{ WebkitTextStroke: '0.8px #000', textShadow: '2px 2px 0 #000' }}><ExemploLegenda id={id} t={t} /></span>
              <span className="text-xs text-slate-400 leading-snug">{t(`marca.estilos.${id}.descricao`)}</span>
            </label>)}
        </div>
      </fieldset>
    </div>}
  </section>;
}
