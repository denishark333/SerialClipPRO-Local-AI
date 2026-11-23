// Confere se pt.js e en.js têm as mesmas chaves e as mesmas variáveis {nome}.
import pt from '../src/i18n/pt.js';
import en from '../src/i18n/en.js';

function achatar(objeto, prefixo = '') {
  return Object.entries(objeto).flatMap(([chave, valor]) =>
    typeof valor === 'object' && valor !== null ? achatar(valor, `${prefixo}${chave}.`) : [[`${prefixo}${chave}`, valor]]);
}

const variaveis = texto => [...String(texto).matchAll(/\{(\w+)\}/g)].map(m => m[1]).sort().join(',');
const a = new Map(achatar(pt));
const b = new Map(achatar(en));
const problemas = [
  ...[...a.keys()].filter(k => !b.has(k)).map(k => `falta em en.js: ${k}`),
  ...[...b.keys()].filter(k => !a.has(k)).map(k => `falta em pt.js: ${k}`),
  ...[...a.keys()].filter(k => b.has(k) && variaveis(a.get(k)) !== variaveis(b.get(k)))
    .map(k => `variáveis diferentes em ${k}: {${variaveis(a.get(k))}} x {${variaveis(b.get(k))}}`),
];
if (problemas.length) {
  console.error(problemas.join('\n'));
  process.exit(1);
}
console.log(`i18n ok: ${a.size} textos em pt-BR e en.`);
