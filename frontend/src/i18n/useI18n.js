import { createContext, useContext } from 'react';

export const I18nContext = createContext(null);

/** { idioma, setIdioma, t } — t('chave', { variavel }) devolve o texto no idioma da interface. */
export const useI18n = () => useContext(I18nContext);
