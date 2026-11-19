"""Alternativas de codificação final, compartilhadas pelo pipeline e revisão."""


def codecs_renderizacao():
    return (
        ('NVIDIA NVENC', ['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '20']),
        ('AMD AMF', ['-c:v', 'h264_amf', '-quality', 'balanced', '-rc', 'cqp', '-qp_i', '20', '-qp_p', '20']),
        ('CPU libx264', ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23']),
    )
