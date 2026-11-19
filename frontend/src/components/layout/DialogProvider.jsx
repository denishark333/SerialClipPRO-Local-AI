import { useRef, useState } from 'react';
import { GalleryDialog } from './GalleryDialog';
import { DialogContext } from './useDialog';

export function DialogProvider({ children }) {
  const [dialog, setDialog] = useState(null);
  const pending = useRef(null);
  const close = (answer = false) => {
    pending.current?.(answer);
    pending.current = null;
    setDialog(null);
  };
  const notify = (message, title = 'Aviso') => {
    pending.current?.(false);
    pending.current = null;
    setDialog({ message, title, section: 'Avisos' });
  };
  const ask = (message, title = 'Confirmar ação') => new Promise(resolve => {
    pending.current?.(false);
    pending.current = resolve;
    setDialog({ message, title, section: 'Confirmação', confirm: true, confirmLabel: 'Confirmar' });
  });
  return <DialogContext.Provider value={{ notify, ask }}>
    {children}
    <GalleryDialog dialog={dialog} busy={false} onClose={() => close(false)} onConfirm={() => close(true)} />
  </DialogContext.Provider>;
}
