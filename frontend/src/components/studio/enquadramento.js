// Conversão entre a config de enquadramento do backend (studio-config e bases de revisão)
// e o estado do EditorEnquadramento. Tudo em porcentagem da imagem original.

export const ENQUADRAMENTO_PADRAO = { ativo: false, webcam: { x: 60, y: 55, width: 35, height: 35 }, foco: 50 };

export function configParaEnquadramento(config) {
  const resultado = { ...ENQUADRAMENTO_PADRAO, ativo: Boolean(config?.modo_estudio_ativo) };
  const foco = Number(config?.foco_conteudo);
  if (Number.isFinite(foco)) resultado.foco = Math.max(0, Math.min(100, foco));
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
  return resultado;
}

export function enquadramentoParaConfig({ ativo, webcam, foco }) {
  return {
    modo_estudio_ativo: ativo,
    enquadramento_feito: ativo,
    foco_conteudo: Number(foco.toFixed(2)),
    crop_jogo: { x: 0, y: 0, w: 100, h: 100 },
    crop_webcam: {
      x: Number(webcam.x.toFixed(4)),
      y: Number(webcam.y.toFixed(4)),
      w: Number(webcam.width.toFixed(4)),
      h: Number(webcam.height.toFixed(4)),
    },
  };
}
