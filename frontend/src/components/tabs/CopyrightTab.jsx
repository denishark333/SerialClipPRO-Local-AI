import React from 'react';
import { YouTubeIcon, KickIcon, TwitchIcon, InstagramIcon, TikTokIcon } from '../icons/Icons';
import { version } from '../../../../version.json';

const ECOSSISTEMA = [
  { nome: 'Serial ClipPRO', url: 'https://serialclip.pro', dominio: 'serialclip.pro', descricao: 'Página oficial e downloads.' },
  { nome: 'SerialHealer', url: 'https://serialhealer.com.br', dominio: 'serialhealer.com.br', descricao: 'Site do criador e da comunidade.' },
  { nome: 'Creator Studio', url: 'https://creatorstudio.serialhealer.com.br', dominio: 'creatorstudio.serialhealer.com.br', descricao: 'Métricas e planejamento de conteúdo do canal.' },
  { nome: 'Chrono Odyssey', url: 'https://chronoodyssey.com.br', dominio: 'chronoodyssey.com.br', descricao: 'Projeto da comunidade.' },
];

const LINK = 'text-cyan-300 underline decoration-cyan-700 underline-offset-2 hover:text-cyan-200';

const CANAIS = [
  { nome: 'YouTube', usuario: '@serialhealer', url: 'https://youtube.com/@serialhealer', cor: '#FF0000', Icone: YouTubeIcon },
  { nome: 'Twitch', usuario: 'serialhealer_', url: 'https://twitch.tv/serialhealer_', cor: '#9146FF', Icone: TwitchIcon },
  { nome: 'Kick', usuario: 'SerialHealer', url: 'https://kick.com/SerialHealer', cor: '#53FC18', Icone: KickIcon },
  { nome: 'Instagram', usuario: '@serialhealer_', url: 'https://instagram.com/serialhealer_', cor: '#E1306C', Icone: InstagramIcon },
  { nome: 'TikTok', usuario: '@serialhealer_', url: 'https://www.tiktok.com/@serialhealer_', cor: '#ff0050', Icone: TikTokIcon },
];

export function CopyrightTab() {
  return (
    <div className="bg-[#0a0712] border border-[#1b1528] p-8 rounded-2xl shadow-xl w-full lg:w-[94%] mx-auto flex flex-col gap-6">
      
      {/* Cabeçalho */}
      <div className="border-b border-[#1b1528] pb-4 text-center">
        <h2 className="text-xl font-bold text-slate-100">Serial ClipPRO</h2>
        <p className="text-sm text-slate-400 mt-1">
          Versão {version} · Gratuito e de código aberto (licença MIT) · Desenvolvido e mantido por{' '}
          <span className="text-[#b3ff33] font-semibold">SerialHealer</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <article className="rounded-xl border border-purple-800/60 bg-[#0e0a1a] p-5 space-y-3 text-sm text-slate-300 leading-relaxed">
          <h3 className="font-bold text-purple-200">Licença e créditos</h3>
          <p>
            © 2026 SerialHealer. Distribuído sob a licença MIT: use, modifique e compartilhe livremente,
            mantendo este aviso. O software é fornecido sem garantia.
          </p>
          <ul className="space-y-2">
            <li>
              <a href="https://github.com/artbyjazi/autoclip" target="_blank" rel="noreferrer" className={LINK}>AutoClip</a>
              {' '}— © 2026 Jad Ghazi, licença MIT. Base do ajuste das bordas dos cortes, do Whisper na GPU e de ideias de codificação e áudio.
            </li>
            <li>
              <a href="https://github.com/googlefonts/bangers" target="_blank" rel="noreferrer" className={LINK}>Fonte Bangers</a>
              {' '}— © 2010 The Bangers Project Authors, SIL Open Font License 1.1.
            </li>
          </ul>
        </article>
        <article className="rounded-xl border border-amber-600/30 bg-[#0e0a1a] p-5 space-y-3 text-sm text-slate-300 leading-relaxed">
          <h3 className="font-bold text-amber-200">Antes de publicar</h3>
          <p>O ClipPRO não identifica músicas protegidas: um corte pode conter áudio de terceiros. Assista antes de postar.</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>YouTube, TikTok e Instagram podem silenciar ou bloquear cortes com música de terceiros.</li>
            <li>No OBS, mande a música para uma faixa de áudio separada da faixa da VOD: assim ela não chega aos cortes.</li>
          </ul>
        </article>
        <article className="rounded-xl border border-cyan-500/40 bg-gradient-to-br from-purple-950/40 to-cyan-950/20 p-5 space-y-3 text-sm">
          <h3 className="font-bold text-cyan-200">Ecossistema</h3>
          <ul className="space-y-2.5">
            {ECOSSISTEMA.map(({ nome, url, dominio, descricao }) => (
              <li key={nome}>
                <a href={url} target="_blank" rel="noreferrer" className="font-semibold text-slate-100 hover:text-cyan-200">{nome}</a>
                <span className="block text-xs text-slate-400">{descricao} <span className="font-mono text-slate-500">{dominio}</span></span>
              </li>
            ))}
          </ul>
        </article>
      </div>

      <div className="flex flex-col gap-3">
        <span className="text-sm font-mono text-slate-400 uppercase tracking-wider text-center">Canais oficiais</span>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {CANAIS.map(({ nome, usuario, url, cor, Icone }) => (
            <a key={nome} href={url} target="_blank" rel="noreferrer"
              className="group bg-[#0e0a1a] border border-[#1f1633] rounded-xl p-4 flex flex-col items-center gap-2 text-center transition hover:border-[var(--cor)]"
              style={{ '--cor': `${cor}66` }}>
              <span className="w-10 h-10 rounded-lg flex items-center justify-center border"
                style={{ color: cor, backgroundColor: `${cor}1a`, borderColor: `${cor}33` }}>
                <Icone className="w-5 h-5" />
              </span>
              <span className="text-sm font-semibold text-slate-200">{nome}</span>
              <span className="text-xs font-mono text-slate-400 group-hover:text-slate-200 transition">{usuario}</span>
            </a>
          ))}
        </div>
      </div>

    </div>
  );
}
