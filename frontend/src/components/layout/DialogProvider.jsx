import { useRef, useState } from 'react';
import { GalleryDialog } from './GalleryDialog';
import { DialogContext } from './useDialog';
import { useI18n } from '../../i18n/useI18n';

export function DialogProvider({ children }) {
  const { t } = useI18n();
  const [dialog, setDialog] = useState(null);
  const pending = useRef(null);
  const close = (answer = false) => {
    pending.current?.(answer);
    pending.current = null;
    setDialog(null);
  };
  const notify = (message, title = t('comum.aviso')) => {
    pending.current?.(false);
    pending.current = null;
    setDialog({ message, title, section: t('dialogo.secaoAvisos') });
  };
  const ask = (message, title = t('comum.confirmarAcao')) => new Promise(resolve => {
    pending.current?.(false);
    pending.current = resolve;
    setDialog({ message, title, section: t('dialogo.secaoConfirmacao'), confirm: true, confirmLabel: t('comum.confirmar') });
  });
  return <DialogContext.Provider value={{ notify, ask }}>
    {children}
    <GalleryDialog dialog={dialog} busy={false} onClose={() => close(false)} onConfirm={() => close(true)} />
  </DialogContext.Provider>;
}
