// Conversão entre a config de enquadramento do backend (studio-config e bases de revisão)
// e o estado do EditorEnquadramento. Tudo em porcentagem da imagem original.

// Cada pessoa do Modo Podcast (perfil 1) vira metade do corte: 1080 x 960, ou seja,
// altura = largura * 8/9 em pixels. A área é exatamente o que aparece na metade.
export const PROPORCAO_PESSOA = 8 / 9;

// Padrão do plano aberto: as duas metades do vídeo lado a lado, cada uma com a maior altura que a proporção permite, centralizada. Cobre a cena
// inteira sem uma área invadir a outra.
export function pessoasPadrao(aspecto = 16 / 9) {
  let width = 50;
  let height = width * PROPORCAO_PESSOA * aspecto;
  if (height > 100) {
    height = 100;
    width = height / PROPORCAO_PESSOA / aspecto;
  }
  const y = (100 - height) / 2;
  return [
    { x: 50 - width, y, width, height },
    { x: 50, y, width, height },
  ];
}

const [ESQUERDA_PADRAO, DIREITA_PADRAO] = pessoasPadrao();

export const ENQUADRAMENTO_PADRAO = {
  ativo: false, layout: 'webcam', webcam: { x: 60, y: 55, width: 35, height: 35 }, foco: 50,
  esquerda: ESQUERDA_PADRAO, direita: DIREITA_PADRAO, direitaEmCima: false, referencia: null, referenciaMiniatura: null,
  referenciaClose: null, referenciaCloseMiniatura: null, referenciaOrigem: null,
};

// Área de um lado do Podcast, só se couber inteira na sua metade do vídeo (como o backend exige).
function caixaLado(box, minX, maxX) {
  if (!(box?.w > 0 && box?.h > 0)) return null;
  if (box.x < minX - 0.001 || box.x + box.w > maxX + 0.001 || box.y < 0 || box.y + box.h > 100.001) return null;
  return { x: box.x, y: box.y, width: box.w, height: box.h };
}

function paraBox(valor) {
  return {
    x: Number(valor.x.toFixed(4)),
    y: Number(valor.y.toFixed(4)),
    w: Number(valor.width.toFixed(4)),
    h: Number(valor.height.toFixed(4)),
  };
}

export function configParaEnquadramento(config) {
  const resultado = { ...ENQUADRAMENTO_PADRAO, ativo: Boolean(config?.modo_estudio_ativo) };
  const foco = Number(config?.foco_conteudo);
  if (Number.isFinite(foco)) resultado.foco = Math.max(0, Math.min(100, foco));
  if (config?.layout_estudio === 'podcast') resultado.layout = 'podcast';
  resultado.referencia = config?.referencia_plano_aberto || null;
  resultado.referenciaMiniatura = config?.referencia_miniatura || null;
  resultado.referenciaClose = config?.referencia_close || null;
  resultado.referenciaCloseMiniatura = config?.referencia_close_miniatura || null;
  resultado.referenciaOrigem = config?.referencia_origem || null;
  const box = config?.crop_webcam;
  if (box?.w > 0 && box?.h > 0) {
    // Presets muito antigos guardavam pixels de uma fonte 1920x1080.
    const pixels = box.w > 100 || box.h > 100;
    resultado.webcam = {
      x: pixels ? box.x / 1920 * 100 : box.x,
      y: pixels ? box.y / 1080 * 100 : box.y,
      width: pixels ? box.w / 1920 * 100 : box.w,
      height: pixels ? box.h / 1080 * 100 : box.h,
    };
  }
  resultado.esquerda = caixaLado(config?.crop_esquerda, 0, 50) || ESQUERDA_PADRAO;
  resultado.direita = caixaLado(config?.crop_direita, 50, 100) || DIREITA_PADRAO;
  resultado.direitaEmCima = Boolean(config?.podcast_direita_em_cima);
  return resultado;
}

export function enquadramentoParaConfig({ ativo, layout = 'webcam', webcam, foco, esquerda, direita, direitaEmCima = false, referencia = null, referenciaMiniatura = null,
  referenciaClose = null, referenciaCloseMiniatura = null, referenciaOrigem = null }) {
  return {
    modo_estudio_ativo: ativo,
    enquadramento_feito: ativo,
    foco_conteudo: Number(foco.toFixed(2)),
    crop_jogo: { x: 0, y: 0, w: 100, h: 100 },
    crop_webcam: paraBox(webcam),
    layout_estudio: layout,
    // O Podcast troca sozinho a cada plano; sem o plano aberto marcado, o corte inteiro sai em tela dividida.
    perfil_podcast: 'automatico',
    crop_esquerda: paraBox(esquerda || ESQUERDA_PADRAO),
    crop_direita: paraBox(direita || DIREITA_PADRAO),
    podcast_direita_em_cima: direitaEmCima,
    referencia_plano_aberto: referencia,
    referencia_miniatura: referenciaMiniatura,
    referencia_close: referenciaClose,
    referencia_close_miniatura: referenciaCloseMiniatura,
    referencia_origem: referenciaOrigem,
  };
}
