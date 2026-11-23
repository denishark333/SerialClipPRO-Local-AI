import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiFetch } from '../api';
import { DICIONARIOS, idiomaDoNavegador, traduzir } from './traduzir';
import { I18nContext } from './useI18n';

const CHAVE_LOCAL = 'clippro_idioma_interface';

function lembrado() {
  try {
    const valor = window.localStorage.getItem(CHAVE_LOCAL);
    return valor in DICIONARIOS ? valor : null;
  } catch { return null; }
}

function lembrar(idioma) {
  try { window.localStorage.setItem(CHAVE_LOCAL, idioma); } catch { /* armazenamento indisponível */ }
}

/**
 * O idioma vale de verdade no backend (config_interface.json), que também o
 * usa nas mensagens e o recebe do instalador. A cópia local só evita que a
 * tela pisque no idioma errado enquanto o backend responde.
 */
export function I18nProvider({ children }) {
  const [idioma, setIdiomaLocal] = useState(() => lembrado() || idiomaDoNavegador());

  useEffect(() => {
    let cancelado = false;
    apiFetch('/interface')
      .then(resposta => resposta.json())
      .then(dados => {
        if (cancelado || !(dados.idioma in DICIONARIOS)) return;
        setIdiomaLocal(dados.idioma);
        lembrar(dados.idioma);
      })
      .catch(() => { /* backend fora do ar: fica o idioma provisório */ });
    return () => { cancelado = true; };
  }, []);

  useEffect(() => { document.documentElement.lang = idioma; }, [idioma]);

  const setIdioma = useCallback(async novo => {
    if (!(novo in DICIONARIOS)) return;
    // Salva no backend antes de trocar a tela: o que for recarregado já vem no idioma novo.
    try {
      await apiFetch('/interface', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ idioma: novo }),
      });
    } catch { /* backend fora do ar: a escolha vale nesta sessão */ }
    setIdiomaLocal(novo);
    lembrar(novo);
  }, []);

  const t = useCallback((chave, variaveis) => traduzir(idioma, chave, variaveis), [idioma]);
  const valor = useMemo(() => ({ idioma, setIdioma, t }), [idioma, setIdioma, t]);
  return <I18nContext.Provider value={valor}>{children}</I18nContext.Provider>;
}
