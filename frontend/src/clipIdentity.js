// A identidade vem do arquivo, nunca da posição do card na lista.
export function clipIdentity(path) {
  const nome = path.split('/').pop();
  const match = /^corte_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(?:_([0-9a-f]+))?_(\d+)\.mp4$/i.exec(nome);
  if (!match) return { titulo: nome, sessao: 'Arquivo salvo', numero: null };
  const [, ano, mes, dia, hora, minuto, segundo, id, numero] = match;
  return { titulo: `Corte #${Number(numero)}`, numero: Number(numero),
    sessao: `${dia}/${mes}/${ano} ${hora}:${minuto}:${segundo}${id ? ` · ${id}` : ''}` };
}
