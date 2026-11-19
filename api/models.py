from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Literal

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
            raise ValueError("Informe um caminho de vídeo ou URL.")
        return valor

class CropBox(BaseModel):
    w: float = Field(gt=0, le=100, allow_inf_nan=False)
    h: float = Field(gt=0, le=100, allow_inf_nan=False)
    x: float = Field(ge=0, le=100, allow_inf_nan=False)
    y: float = Field(ge=0, le=100, allow_inf_nan=False)

    @model_validator(mode="after")
    def validar_limites(self):
        if self.x + self.w > 100.001 or self.y + self.h > 100.001:
            raise ValueError("O enquadramento deve ficar dentro do vídeo (0 a 100%).")
        return self

class StudioConfigRequest(BaseModel):
    modo_estudio_ativo: bool
    crop_jogo: CropBox
    crop_webcam: CropBox

class ExportRequest(BaseModel):
    videos: List[str]
