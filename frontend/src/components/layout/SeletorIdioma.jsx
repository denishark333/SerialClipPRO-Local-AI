import { useI18n } from '../../i18n/useI18n';
import { IDIOMAS } from '../../i18n/traduzir';

// Fica entre o cabeçalho e as abas, à esquerda.
export function SeletorIdioma() {
  const { idioma, setIdioma, t } = useI18n();
  return (
    <div role="group" aria-label={t('cabecalho.idiomaInterface')} title={t('cabecalho.idiomaInterface')}
      className="flex items-center gap-1 rounded-xl border border-[#1b1528] bg-[#0a0712] p-1 text-xs font-mono">
      <svg viewBox="0 0 24 24" className="ml-1.5 mr-0.5 h-4 w-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="1.8"
        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
      </svg>
      {IDIOMAS.map(({ id, sigla, nome }) => (
        <button key={id} type="button" lang={id} aria-pressed={idioma === id} title={nome} onClick={() => setIdioma(id)}
          className={`rounded-lg px-2.5 py-1 font-bold transition focus-visible:outline-2 focus-visible:outline-cyan-400 ${idioma === id ? 'bg-gradient-to-r from-[#9333ea]/60 to-[#00ffff]/30 text-white' : 'text-slate-400 hover:text-slate-200'}`}>
          {sigla}
        </button>
      ))}
    </div>
  );
}
