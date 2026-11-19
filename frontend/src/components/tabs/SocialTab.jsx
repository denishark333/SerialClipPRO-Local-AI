import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../api';
import { BiliBiliIcon, KickIcon, TwitchIcon, TikTokIcon, InstagramIcon, YouTubeIcon } from '../icons/Icons';
const colors = { kick: 'text-[#53fc18]', twitch: 'text-[#a970ff]', youtube: 'text-red-500', instagram: 'text-pink-400', tiktok: 'text-cyan-300' };
const orientacoes = {
  youtube: 'Envie o MP4 vertical pelo YouTube Studio no computador. Shorts também podem ser enviados pelo fluxo de upload desktop.',
  twitch: 'A Twitch trabalha com clipes das transmissões e VODs da plataforma. Abrir o painel não equivale a publicar um MP4 local como clipe.',
  instagram: 'Use as opções de criação disponíveis na sua conta. Se a função desejada exigir o aplicativo móvel, conclua a publicação nele.',
  tiktok: 'Abra o TikTok Studio e selecione o corte exportado no fluxo de envio disponível para sua conta.',
  kick: 'Use o painel oficial para os recursos disponíveis na sua conta. O ClipPRO não oferece upload automático para a Kick.',
};
const icons = { kick: KickIcon, twitch: TwitchIcon, tiktok: TikTokIcon, instagram: InstagramIcon, youtube: YouTubeIcon };

export function SocialTab() {
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
      setMessage('Nome salvo. Faça login diretamente no site para escolher a conta que publicará.');
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
    } catch (e) { setMessage(`Não foi possível abrir: ${e.message}. Use Abrir no navegador.`); }
  }
  return <section className="w-full lg:w-[94%] mx-auto bg-[#0a0712] border border-[#1b1528] p-6 rounded-2xl flex flex-col gap-5">
    <h2 className="text-lg font-bold">Social • Gestão dos canais</h2>
    <p className="text-sm text-slate-400">Salve o nome do canal como referência e abra o site oficial para entrar e publicar. Exporte os cortes na galeria e selecione os arquivos no site.</p>
    <p className="text-xs text-slate-400">No desktop, “Abrir site” usa uma janela do aplicativo. Se o login não funcionar, use o navegador. O nome salvo não confirma login nem seleciona a conta no site.</p>
    <p className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 text-sm text-amber-200 leading-relaxed">A janela integrada usa a versão web. Simular um celular não garante recursos do aplicativo móvel. Se uma função ou login não estiver disponível, use o navegador ou o aplicativo oficial.</p>
    <p role="status" className="text-sm text-cyan-300">{message}</p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {platforms.map(platform => {
        const Icon = icons[platform.id];
        return <div key={platform.id} className="bg-[#0e0a1a] border border-[#1f1633] p-5 rounded-xl flex flex-col gap-3">
          <h3 className="font-bold flex items-center gap-2">{Icon && <Icon className={`w-8 h-8 shrink-0 ${colors[platform.id]}`} />}{platform.titulo}</h3>
          <p className="text-sm text-slate-300 leading-relaxed">{orientacoes[platform.id]}</p>
          <label className="text-xs text-slate-400">Nome do canal (referência)
            <input className="block mt-1 w-full bg-slate-900 rounded p-2 text-slate-100" maxLength={100} value={platform.canal} placeholder="@seucanal" onChange={e => setPlatforms(previous => previous.map(p => p.id === platform.id ? { ...p, canal: e.target.value } : p))} />
          </label>
          <div className="flex gap-3 flex-wrap text-xs">
            <button disabled={busy} className="rounded bg-slate-800 px-3 py-2" onClick={() => save(platform)}>Salvar nome</button>
            <button className="rounded bg-purple-700 px-3 py-2" onClick={() => open(platform)}>Abrir site</button>
            <button className="text-cyan-300 underline" onClick={() => open(platform, true)}>Abrir no navegador</button>
          </div>
        </div>;
      })}
      <div className="bg-[#0e0a1a] border border-[#1f1633] p-5 rounded-xl"><h3 className="font-bold flex items-center gap-2"><BiliBiliIcon className="w-8 h-8 text-[#00a1d6]" />BiliBili</h3><p className="text-slate-400 text-sm mt-2">Em breve</p></div>
    </div>
    <p className="text-xs text-slate-500">As sessões das janelas desktop ficam no perfil local do WebView2. Para sair da conta, use o próprio site. Senhas não são solicitadas pelo ClipPRO.</p>
  </section>;
}
