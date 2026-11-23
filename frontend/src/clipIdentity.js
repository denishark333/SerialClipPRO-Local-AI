// A identidade vem do arquivo, nunca da posição do card na lista.
// t é o tradutor de useI18n(); os textos ficam em corte.* nos dicionários.
export function clipIdentity(path, t) {
  const nome = path.split('/').pop();
  const match = /^corte_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(?:_([0-9a-f]+))?_(\d+)\.mp4$/i.exec(nome);
  if (!match) return { titulo: nome, sessao: t('corte.arquivoSalvo'), numero: null };
  const [, ano, mes, dia, hora, minuto, segundo, id, numero] = match;
  return { titulo: t('corte.titulo', { numero: Number(numero) }), numero: Number(numero),
    sessao: `${t('corte.data', { dia, mes, ano, hora, minuto, segundo })}${id ? ` · ${id}` : ''}` };
}
