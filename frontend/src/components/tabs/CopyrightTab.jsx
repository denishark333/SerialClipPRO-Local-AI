import React from 'react';
import { YouTubeIcon, KickIcon, TwitchIcon, InstagramIcon, TikTokIcon } from '../icons/Icons';
import { version } from '../../../../version.json';
import { useI18n } from '../../i18n/useI18n';

// Cada projeto com a própria identidade no nome; os projetos Serial dividem a logo do SerialHealer.
const GRADIENTE = 'text-transparent bg-clip-text bg-gradient-to-r';
const LOGO_SERIAL = '/serial-healer.png';
const ECOSSISTEMA = [
  { chave: 'serialhealer', url: 'https://serialhealer.com.br', logo: LOGO_SERIAL,
    nome: <span className={`${GRADIENTE} from-[#b3ff33] to-[#ff5fd2]`}>Serial Healer</span> },
  { chave: 'clippro', url: 'https://serialclip.pro', logo: LOGO_SERIAL, aviso: 'desenvolvimento',
    nome: <span className={`${GRADIENTE} from-[#b3ff33] via-[#9333ea] to-[#00ffff]`}>Serial ClipPRO</span> },
  { chave: 'creatorstudio', url: 'https://creatorstudio.serialhealer.com.br', logo: LOGO_SERIAL, aviso: 'desenvolvimento',
    nome: <><span className="text-[#ff1f4f]">Serial</span> <span className="text-[#a78bfa]">Creator</span> <span className="text-[#53fc18]">Studio</span></> },
  { chave: 'chronoodyssey', url: 'https://chronoodyssey.com.br', logo: '/ecossistema/chronoodyssey.png',
    aviso: 'aguardandoDados',
    nome: <span className="text-[#d4af37]">Chrono Odyssey | Interactive Map</span> },
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
  const { t } = useI18n();
  return (
    <div className="bg-[#0a0712] border border-[#1b1528] p-8 rounded-2xl shadow-xl w-full lg:w-[94%] mx-auto flex flex-col gap-6">
      
      {/* Cabeçalho */}
      <div className="border-b border-[#1b1528] pb-4 text-center">
        <h2 className="text-xl font-bold text-slate-100">Serial ClipPRO</h2>
        <p className="text-sm text-slate-400 mt-1">
          {t('copyright.versao', { versao: version })}{' '}
          <span className="text-[#b3ff33] font-semibold">SerialHealer</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <article className="rounded-xl border border-purple-800/60 bg-[#0e0a1a] p-5 space-y-3 text-sm text-slate-300 leading-relaxed">
          <h3 className="font-bold text-purple-200">{t('copyright.licencaTitulo')}</h3>
          <p>
            {t('copyright.licencaTexto')}
          </p>
          <ul className="space-y-2">
            <li>
              <a href="https://github.com/artbyjazi/autoclip" target="_blank" rel="noreferrer" className={LINK}>AutoClip</a>
              {' '}— {t('copyright.creditoAutoclip')}
            </li>
            <li>
              <a href="https://github.com/googlefonts/bangers" target="_blank" rel="noreferrer" className={LINK}>{t('copyright.fonteBangers')}</a>
              {' '}— © 2010 The Bangers Project Authors, SIL Open Font License 1.1.
            </li>
          </ul>
        </article>
        <article className="rounded-xl border border-amber-600/30 bg-[#0e0a1a] p-5 space-y-3 text-sm text-slate-300 leading-relaxed">
          <h3 className="font-bold text-amber-200">{t('copyright.antesTitulo')}</h3>
          <p>{t('copyright.antesTexto')}</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>{t('copyright.antesPlataformas')}</li>
            <li>{t('copyright.antesObs')}</li>
          </ul>
        </article>
        <article className="rounded-xl border border-cyan-500/40 bg-gradient-to-br from-purple-950/40 to-cyan-950/20 p-5 space-y-3 text-sm">
          <h3 className="font-bold text-cyan-200">{t('copyright.ecossistema')}</h3>
          <ul className="space-y-3">
            {ECOSSISTEMA.map(({ chave, nome, url, logo, aviso }) => (
              <li key={chave}>
                <a href={url} target="_blank" rel="noreferrer" className="group flex items-center gap-3">
                  <img src={logo} alt="" className="w-9 h-9 shrink-0 rounded-full bg-black object-cover" />
                  <span>
                    <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                      <span className="font-bold group-hover:brightness-125 transition">{nome}</span>
                      {aviso && <span className="rounded-full border border-amber-500/40 bg-amber-950/30 px-2 py-0.5 text-[10px] font-medium text-amber-200">{t(`copyright.avisos.${aviso}`)}</span>}
                    </span>
                    <span className="block text-xs text-slate-400">{t(`copyright.projetos.${chave}`)}</span>
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </article>
      </div>

      <div className="flex flex-col gap-3">
        <span className="text-sm font-mono text-slate-400 uppercase tracking-wider text-center">{t('copyright.canaisOficiais')}</span>
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
