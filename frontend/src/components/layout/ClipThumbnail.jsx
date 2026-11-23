import { useEffect, useRef, useState } from 'react';
import { useI18n } from '../../i18n/useI18n';

// Carrega apenas um quadro quando o card se aproxima da área visível.
export function ClipThumbnail({ src }) {
  const { t } = useI18n();
  const container = useRef(null);
  const [visible, setVisible] = useState(false);
  const [state, setState] = useState('loading');
  useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        setVisible(true);
        observer.disconnect();
      }
    }, { rootMargin: '200px' });
    observer.observe(container.current);
    return () => observer.disconnect();
  }, []);
  return <div ref={container} className="relative aspect-[9/16] w-full overflow-hidden bg-black">
    {visible && <video src={`${src}#t=0.1`} muted playsInline preload="metadata" aria-hidden="true" tabIndex={-1}
      onLoadedData={() => setState('ready')} onSeeked={() => setState('ready')} onError={() => setState('error')}
      className="pointer-events-none h-full w-full object-contain" />}
    {state !== 'ready' && <span className="absolute inset-0 flex items-center justify-center p-4 text-center text-xs text-slate-400">
      {state === 'error' ? t('corte.miniaturaIndisponivel') : t('corte.carregandoMiniatura')}
    </span>}
  </div>;
}
