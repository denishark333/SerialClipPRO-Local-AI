import pt from './pt';
import en from './en';

export const DICIONARIOS = { 'pt-BR': pt, en };
export const IDIOMAS = [
  { id: 'pt-BR', sigla: 'PT', nome: 'Português' },
  { id: 'en', sigla: 'EN', nome: 'English' },
];
const PADRAO = 'pt-BR';

function buscar(dicionario, chave) {
  return chave.split('.').reduce((no, parte) => (no == null ? undefined : no[parte]), dicionario);
}

/**
 * Texto da chave no idioma pedido. Sem tradução, cai no português e, por fim,
 * na própria chave, para o buraco aparecer na tela em vez de sumir.
 * Variáveis entram como {nome}: t('cabecalho.versao', { versao: '3.0.0' }).
 */
export function traduzir(idioma, chave, variaveis) {
  let texto = buscar(DICIONARIOS[idioma], chave);
  if (typeof texto !== 'string') {
    if (import.meta.env.DEV) console.warn(`[i18n] sem tradução "${chave}" em ${idioma}`);
    texto = buscar(DICIONARIOS[PADRAO], chave);
  }
  if (typeof texto !== 'string') return chave;
  if (!variaveis) return texto;
  return texto.replace(/\{(\w+)\}/g, (trecho, nome) => (nome in variaveis ? String(variaveis[nome]) : trecho));
}

/** Idioma provisório enquanto o backend não responde: o do navegador (no app, o do Windows). */
export function idiomaDoNavegador() {
  const codigo = (typeof navigator !== 'undefined' && navigator.language) || '';
  return codigo.toLowerCase().startsWith('pt') ? 'pt-BR' : 'en';
}
