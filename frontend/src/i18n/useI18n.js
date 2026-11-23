import { createContext, useContext, useEffect, useRef } from 'react';

export const I18nContext = createContext(null);

/** { idioma, setIdioma, t } — t('chave', { variavel }) devolve o texto no idioma da interface. */
export const useI18n = () => useContext(I18nContext);

/**
 * Referência ao t atual, para efeitos de longa duração (polling, buscas) que não
 * devem reiniciar quando o idioma muda: use tAtual.current('chave').
 */
export function useTAtual() {
  const { t } = useI18n();
  const ref = useRef(t);
  useEffect(() => { ref.current = t; }, [t]);
  return ref;
}
