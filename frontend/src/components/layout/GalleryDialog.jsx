import { useEffect, useRef, useId } from 'react';
import { useI18n } from '../../i18n/useI18n';

export function GalleryDialog({ dialog, busy, onClose, onConfirm }) {
  const { t } = useI18n();
  const ref = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const element = ref.current;
    if (dialog && !element.open) element.showModal();
    if (!dialog && element.open) element.close();
  }, [dialog]);
  return <dialog ref={ref} onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}
    aria-labelledby={titleId}
    className="m-auto w-[min(92vw,520px)] rounded-2xl border border-purple-500/40 bg-[#0e0a1a] p-6 text-slate-100 shadow-2xl backdrop:bg-black/75">
    <p className="mb-3 text-xs uppercase tracking-widest text-purple-400">Serial ClipPRO · {dialog?.section || t('dialogo.secaoGaleria')}</p>
    <h2 id={titleId} className="text-xl font-bold">{busy ? t('dialogo.excluindo') : dialog?.title}</h2>
    <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-300" role="status">{busy ? t('dialogo.excluindoDetalhe') : dialog?.message}</p>
    {!busy && dialog?.details?.length > 0 && <details className="mt-4 text-sm text-slate-400">
      <summary className="cursor-pointer text-purple-300">{t('dialogo.verDetalhes', { total: dialog.details.length })}</summary>
      <ul className="mt-2 max-h-[30vh] overflow-y-auto break-all space-y-2">
        {dialog.details.map((item, index) => <li key={index}>{item.nome}: {item.motivo}</li>)}
      </ul>
    </details>}
    <div className="mt-6 flex justify-end gap-3">
      <button autoFocus disabled={busy} onClick={onClose} className="rounded-xl bg-[#1b1528] px-4 py-2 disabled:opacity-40">{dialog?.confirm ? t('comum.cancelar') : t('comum.entendi')}</button>
      {dialog?.confirm && <button disabled={busy} onClick={onConfirm} className="rounded-xl bg-rose-600 px-4 py-2 font-semibold disabled:opacity-40">{dialog.confirmLabel || t('dialogo.excluirCortes')}</button>}
    </div>
  </dialog>;
}
