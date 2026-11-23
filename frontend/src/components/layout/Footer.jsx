import { TwitchIcon, KickIcon, YouTubeIcon } from '../icons/Icons';
import { useI18n } from '../../i18n/useI18n';

function GitHubIcon({ className }) {
  return <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true"><path d="M12 .8a11.2 11.2 0 0 0-3.54 21.83c.56.1.77-.24.77-.54v-2.1c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.73 1.16 1.73 1.16 1 1.72 2.63 1.22 3.27.93.1-.73.39-1.22.71-1.5-2.5-.28-5.13-1.25-5.13-5.54 0-1.22.44-2.22 1.16-3-.12-.28-.5-1.42.11-2.96 0 0 .95-.3 3.08 1.15A10.7 10.7 0 0 1 12 6.18c.95 0 1.9.13 2.8.38 2.14-1.45 3.08-1.15 3.08-1.15.61 1.54.23 2.68.11 2.96.72.78 1.16 1.78 1.16 3.01 0 4.3-2.63 5.25-5.14 5.53.4.35.76 1.03.76 2.08v3.1c0 .3.2.65.77.54A11.2 11.2 0 0 0 12 .8Z" /></svg>;
}

const canais = [
  { nome: 'Twitch', url: 'https://twitch.tv/serialhealer_', Icon: TwitchIcon, cor: 'text-[#b58aff]' },
  { nome: 'Kick', url: 'https://kick.com/SerialHealer', Icon: KickIcon, cor: 'text-[#53fc18]' },
  { nome: 'YouTube', url: 'https://youtube.com/@serialhealer', Icon: YouTubeIcon, cor: 'text-[#ff6068]' },
  { nome: 'GitHub', url: 'https://github.com/denishark333/SerialClipPRO-Local-AI', Icon: GitHubIcon, cor: 'text-slate-200' },
];

export function Footer() {
  const { t } = useI18n();
  return (
    <footer className="mt-10 w-full text-center bg-[radial-gradient(ellipse_at_top_right,rgba(88,28,135,0.14),transparent_65%)]">
      <div className="h-px bg-gradient-to-r from-[#b3ff33]/50 via-purple-700/60 to-cyan-500/70" />
      <div className="px-4 pt-9 pb-10">
        <div className="flex items-center justify-center gap-4">
          <div className="w-10 h-10 rounded-full p-[2px] bg-gradient-to-tr from-[#b3ff33] via-[#9333ea] to-[#00ffff] shadow-[0_0_16px_rgba(147,51,234,0.4)]">
            <img src="https://static-cdn.jtvnw.net/jtv_user_pictures/96fca220-b708-41a9-aef9-79acd713e459-profile_image-70x70.png" alt="SerialHealer" className="w-full h-full rounded-full object-cover bg-black" />
          </div>
          <span className="text-xl font-black tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-[#b3ff33] via-[#9333ea] to-[#00ffff]">Serial ClipPRO</span>
        </div>
        <p className="mt-4 text-xs text-gray-400">{t('rodape.slogan')}</p>
        <p className="mt-7 text-xs font-bold tracking-wider text-gray-300">{t('rodape.acompanhe')}</p>
        <nav aria-label={t('rodape.canais')} className="mt-6 flex flex-wrap items-center justify-center gap-x-7 gap-y-4">
          {canais.map(({ nome, url, Icon, cor }) => (
            <a key={nome} href={url} target="_blank" rel="noopener noreferrer" className={`flex items-center gap-2.5 font-semibold ${cor} transition hover:brightness-125 focus-visible:outline-2 focus-visible:outline-cyan-400 rounded`}>
              <Icon className="w-5 h-5" /><span>{nome}</span>
            </a>
          ))}
        </nav>
      </div>
      <div className="border-t border-white/5 pt-5 pb-2 text-xs text-gray-400">
        <p>Powered by <strong className="text-gray-300">Serial Healer</strong> © {new Date().getFullYear()}</p>
        <p className="mt-3">{t('rodape.desenvolvimento')}</p>
      </div>
    </footer>
  );
}
