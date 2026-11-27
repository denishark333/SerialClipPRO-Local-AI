import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../api';
import { BiliBiliIcon, KickIcon, TwitchIcon, TikTokIcon, InstagramIcon, YouTubeIcon } from '../icons/Icons';
import { useI18n } from '../../i18n/useI18n';
const colors = { kick: 'text-[#53fc18]', twitch: 'text-[#a970ff]', youtube: 'text-red-500', instagram: 'text-pink-400', tiktok: 'text-cyan-300' };
const icons = { kick: KickIcon, twitch: TwitchIcon, tiktok: TikTokIcon, instagram: InstagramIcon, youtube: YouTubeIcon };

export function SocialTab() {
  const { t } = useI18n();
  const [platforms, setPlatforms] = useState([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    apiFetch('/social').then(r => r.json()).then(data => { if (active) setPlatforms(data.plataformas); })
      .catch(e => { if (active) setMessage(e.message); });
    return () => { active = false; };
  }, []);
  async function save(platform) {
    setBusy(true);
    try {
      await apiFetch('/social', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plataforma: platform.id, nome: platform.canal }) });
      setMessage(t('social.nomeSalvo'));
    } catch (e) { setMessage(e.message); }
    finally { setBusy(false); }
  }
  async function open(platform, external = false) {
    try {
      if (window.pywebview?.api?.abrir_rede) {
        await window.pywebview.api.abrir_rede(platform.id, external);
      } else {
        window.open(platform.url, '_blank', 'noopener,noreferrer');
      }
    } catch (e) { setMessage(t('social.erroAbrir', { erro: e.message })); }
  }
  return <section className="w-full lg:w-[94%] mx-auto bg-[#0a0712] border border-[#1b1528] p-6 rounded-2xl flex flex-col gap-5">
    <h2 className="text-lg font-bold text-center">{t('social.titulo')}</h2>
    <p className="text-sm text-slate-400 text-center">{t('social.descricao')}</p>
    <p className="text-xs text-slate-400 text-center">{t('social.dicaJanela')}</p>
    <p className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-sm text-amber-200 leading-relaxed text-center">{t('social.avisoWeb')}</p>
    <p role="status" className="text-sm text-cyan-300">{message}</p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {platforms.map(platform => {
        const Icon = icons[platform.id];
        return <div key={platform.id} className="bg-[#0e0a1a] border border-[#1f1633] p-5 rounded-xl flex flex-col gap-3">
          <h3 className="font-bold flex items-center gap-2">{Icon && <Icon className={`w-8 h-8 shrink-0 ${colors[platform.id]}`} />}{platform.titulo}</h3>
          <p className="text-sm text-slate-300 leading-relaxed">{t(`social.orientacoes.${platform.id}`)}</p>
          <label className="text-xs text-slate-400">{t('social.nomeCanal')}
            <input className="block mt-1 w-full bg-slate-900 rounded p-2 text-slate-100" maxLength={100} value={platform.canal} placeholder={t('social.placeholderCanal')} onChange={e => setPlatforms(previous => previous.map(p => p.id === platform.id ? { ...p, canal: e.target.value } : p))} />
          </label>
          <div className="flex gap-3 flex-wrap text-xs">
            <button disabled={busy} className="rounded bg-slate-800 px-3 py-2" onClick={() => save(platform)}>{t('social.salvarNome')}</button>
            <button className="rounded bg-purple-700 px-3 py-2" onClick={() => open(platform)}>{t('social.abrirSite')}</button>
            <button className="text-cyan-300 underline" onClick={() => open(platform, true)}>{t('social.abrirNavegador')}</button>
          </div>
        </div>;
      })}
      <div className="bg-[#0e0a1a] border border-[#1f1633] p-5 rounded-xl"><h3 className="font-bold flex items-center gap-2"><BiliBiliIcon className="w-8 h-8 text-[#00a1d6]" />BiliBili</h3><p className="text-slate-400 text-sm mt-2">{t('social.emBreve')}</p></div>
    </div>
    <p className="text-xs text-slate-500">{t('social.sessoes')}</p>
  </section>;
}
