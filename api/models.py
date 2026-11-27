from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Literal
from core.textos import tr

class PipelineRequest(BaseModel):
    entrada: str = Field(min_length=1)
    max_cortes: int = Field(default=50, ge=1, le=50)
    ignorar_inicio_segundos: float = Field(default=0, ge=0, allow_inf_nan=False)
    modo_curadoria: Literal["hibrido", "contexto", "picos"] = "hibrido"
    limite_amostras: int = Field(default=40, ge=10, le=80)
    termos_jogo: str = Field(default="", max_length=500)
    idioma: Literal["pt", "en", "es", "fr", "de", "it", "ja", "ko", "auto"] = "pt"
    foco: str = Field(default="", max_length=500)

    @field_validator("entrada")
    @classmethod
    def limpar_entrada(cls, valor):
        valor = valor.strip().strip('\"').strip("'")
        if not valor:
            raise ValueError(tr('entrada.vazia'))
        return valor

class CropBox(BaseModel):
    w: float = Field(gt=0, le=100, allow_inf_nan=False)
    h: float = Field(gt=0, le=100, allow_inf_nan=False)
    x: float = Field(ge=0, le=100, allow_inf_nan=False)
    y: float = Field(ge=0, le=100, allow_inf_nan=False)

    @model_validator(mode="after")
    def validar_limites(self):
        if self.x + self.w > 100.001 or self.y + self.h > 100.001:
            raise ValueError(tr('estudio.fora_do_video'))
        return self

class StudioConfigRequest(BaseModel):
    modo_estudio_ativo: bool
    crop_jogo: CropBox
    crop_webcam: CropBox
    #: Posição horizontal do recorte vertical do conteúdo: 0 = esquerda, 50 = centro, 100 = direita.
    foco_conteudo: float = Field(50, ge=0, le=100, allow_inf_nan=False)
    #: "webcam": webcam em cima e conteúdo embaixo; "podcast": duas pessoas, metade do corte cada.
    layout_estudio: Literal["webcam", "podcast"] = "webcam"
    #: Perfil do Podcast: "dividido" (duas pessoas), "centralizado" (um corte vertical único) ou
    #: "automatico" (um ou outro em cada plano, comparando com o plano aberto de referência).
    perfil_podcast: Literal["dividido", "centralizado", "automatico"] = "dividido"
    #: Miniaturas 48x27 RGB (base64) do plano aberto e de um close, marcadas no editor para o modo automático.
    referencia_plano_aberto: str | None = Field(None, max_length=6000)
    #: Chave do vídeo em que as referências foram marcadas (a do preview do estúdio).
    referencia_origem: str | None = Field(None, max_length=200, pattern=r"^[A-Za-z0-9_]+$")
    referencia_close: str | None = Field(None, max_length=6000)
    #: Imagens pequenas das referências, só para mostrar no editor.
    referencia_miniatura: str | None = Field(None, max_length=60000, pattern=r'^data:image/jpeg;base64,[A-Za-z0-9+/=]+$')
    referencia_close_miniatura: str | None = Field(None, max_length=60000, pattern=r'^data:image/jpeg;base64,[A-Za-z0-9+/=]+$')
    #: Lados do plano aberto no Podcast: cada um preso à sua metade do vídeo.
    crop_esquerda: CropBox | None = None
    crop_direita: CropBox | None = None
    #: No corte vertical, o lado esquerdo fica em cima, a menos que este campo seja verdadeiro.
    podcast_direita_em_cima: bool = False

    @model_validator(mode="after")
    def validar_lados(self):
        if (self.crop_esquerda and self.crop_esquerda.x + self.crop_esquerda.w > 50.001) or \
                (self.crop_direita and self.crop_direita.x < 49.999):
            raise ValueError(tr('estudio.fora_do_lado'))
        from core.planos import referencia
        for campo in ('referencia_plano_aberto', 'referencia_close'):
            valor = getattr(self, campo)
            if valor is not None and referencia({campo: valor}, campo) is None:
                raise ValueError(tr('estudio.referencia_invalida'))
        return self

class ReferenciaRequest(BaseModel):
    #: URL da mídia aberta no editor: o preview do estúdio ou o original de um corte da revisão.
    midia: str = Field(min_length=1, max_length=500)
    #: Instante (s) do quadro mostrado no editor.
    tempo: float = Field(ge=0, le=86400, allow_inf_nan=False)

class ExportRequest(BaseModel):
    videos: List[str]
