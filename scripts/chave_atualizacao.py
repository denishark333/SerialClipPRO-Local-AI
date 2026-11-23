"""Chave de assinatura dos instaladores (uso do mantenedor).

    python scripts/chave_atualizacao.py gerar
        Cria o par de chaves. A privada fica fora do repositório; a pública vai
        para CHAVE_PUBLICA em core/atualizacao.py. Faça backup da privada: sem
        ela, versões novas não podem ser instaladas pelo atualizador do app.

    python scripts/chave_atualizacao.py assinar <instalador.exe> <versao>
        Grava <instalador.exe>.sig, que deve ser anexado à Release junto do .exe.

A chave privada é lida de CLIPPRO_CHAVE_ATUALIZACAO ou do caminho padrão abaixo.
"""
import base64
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

PADRAO = Path(os.environ.get('USERPROFILE', str(Path.home()))) / '.serialclippro' / 'chave-atualizacao.pem'


def caminho_chave():
    return Path(os.environ.get('CLIPPRO_CHAVE_ATUALIZACAO', str(PADRAO)))


def publica_b64(privada):
    bruta = privada.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(bruta).decode('ascii')


def gerar():
    destino = caminho_chave()
    if destino.exists():
        sys.exit(f'Já existe uma chave em {destino}. Não sobrescrevo: apague-a manualmente se for mesmo trocar.')
    privada = Ed25519PrivateKey.generate()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(privada.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption()))
    print(f'Chave privada: {destino}  (faça backup em local seguro; nunca envie ao Git)')
    print(f'Chave pública para core/atualizacao.py: {publica_b64(privada)}')


def assinar(instalador, versao):
    from core.atualizacao import CHAVE_PUBLICA, assinatura_valida, mensagem_assinada
    instalador = Path(instalador)
    privada = serialization.load_pem_private_key(caminho_chave().read_bytes(), password=None)
    if publica_b64(privada) != CHAVE_PUBLICA:
        sys.exit('A chave privada não corresponde a CHAVE_PUBLICA em core/atualizacao.py.')
    resumo = hashlib.sha256()
    with open(instalador, 'rb') as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b''):
            resumo.update(bloco)
    assinatura = base64.b64encode(privada.sign(mensagem_assinada(versao, instalador.name, resumo.hexdigest()))).decode()
    if not assinatura_valida(versao, instalador.name, resumo.hexdigest(), assinatura):
        sys.exit('A assinatura gerada não confere.')
    saida = instalador.with_name(instalador.name + '.sig')
    saida.write_text(assinatura + '\n', encoding='ascii')
    print(f'Assinatura: {saida}')


if __name__ == '__main__':
    if sys.argv[1:2] == ['gerar']:
        gerar()
    elif sys.argv[1:2] == ['assinar'] and len(sys.argv) == 4:
        assinar(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
