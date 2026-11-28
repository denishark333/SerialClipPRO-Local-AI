# Como contribuir com o Serial ClipPRO

[English](CONTRIBUTING.md) | **Português**

Obrigado pelo interesse no Serial ClipPRO! Ele é um app local, gratuito e de código aberto, e toda contribuição é bem-vinda, de qualquer tamanho: relatos de bug, ideias, traduções, testes em outros hardwares e código.

Ao participar, você concorda em seguir o nosso [Código de Conduta](CODE_OF_CONDUCT.md).

Você pode escrever em **português ou inglês**. Os dois idiomas são bem-vindos em Issues, Pull Requests e revisões.

## Como ajudar

- **Relatar bugs** com detalhes suficientes para reproduzir (veja abaixo).
- **Sugerir melhorias** explicando o problema que você quer resolver, não só a solução.
- **Testar em outros hardwares**, principalmente placas AMD e Intel, e contar o resultado.
- **Testar VODs de outras plataformas, idiomas e tipos de conteúdo** e contar como a curadoria e as legendas se comportaram.
- **Melhorar as traduções** da interface (`frontend/src/i18n/`).
- **Enviar código**: correções, desempenho ou funcionalidades combinadas numa Issue.

## Relatando um bug

Abra uma Issue pelo formulário **Bug report**. Ele pede:

- Versão do Serial ClipPRO, versão do Windows, processador, RAM e placa de vídeo.
- O modelo de IA usado no Ollama.
- A origem do vídeo (Twitch, YouTube, Kick ou arquivo local) e o modo de análise.
- A etapa em que o problema aconteceu e a mensagem de erro, com print se possível.
- Os logs relevantes:
  - Instalação: `%LOCALAPPDATA%\Serial ClipPRO\instalacao.log`
  - Atualização pelo app: `%LOCALAPPDATA%\Serial ClipPRO\logs\atualizacao.log`

**Revise os logs antes de publicar** e remova informações pessoais, tokens e URLs privadas.

Encontrou um problema de segurança? **Não** abra uma Issue pública. Siga a [Política de Segurança](SECURITY.md).

## Preparando o ambiente de desenvolvimento

Requisitos: Windows, Python, Node, FFmpeg/ffprobe no PATH e o [Ollama](https://ollama.com) com pelo menos um modelo (`gemma4:12b` recomendado). Com placa NVIDIA, instale `nvidia-cublas-cu12` no ambiente para transcrever na GPU.

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
venv\Scripts\python.exe main.py
```

Abra http://127.0.0.1:8765. Para recarregar a interface automaticamente, deixe o backend rodando e execute `npm run dev` em `frontend`. Reinicie o `main.py` depois de mudar o código do backend.

Você pode gerar o seu próprio instalador com `scripts/build_installer.ps1 -SemAssinatura` (veja a seção Desenvolvimento do README). As versões oficiais são assinadas pelo mantenedor, e o atualizador do app só aceita instaladores com essa assinatura.

## Pull Requests

1. **Abra uma Issue antes** para qualquer coisa maior que uma correção pequena, assim combinamos a abordagem antes de você investir tempo.
2. Faça um fork do repositório e crie uma branch a partir da `main`.
3. **Um assunto por PR.** PRs pequenos e focados são revisados mais rápido.
4. Teste a mudança no app rodando, com mídia real.
5. Antes de abrir o PR, rode em `frontend/`:
   ```powershell
   npm run lint
   npm run check:i18n
   npm run build
   ```
6. Preencha o modelo de Pull Request.

O mantenedor roda a suíte de testes interna do projeto e testa a mudança no app antes do merge. Um PR pode ser aceito, devolvido com pedidos de ajuste ou recusado com explicação.

## Regras do projeto

- **Texto da interface nos dois idiomas.** Nunca escreva texto fixo nos componentes: adicione a chave em `frontend/src/i18n/pt.js` **e** em `frontend/src/i18n/en.js`. O `npm run check:i18n` confere se os dois batem. Mensagens do backend para o usuário passam por `core/textos.py`.
- **Nada de dados reais de terceiros.** Não envie links de VODs reais, nomes de canais, transcrições, logs de usuários ou vídeos que não são seus. Use exemplos fictícios.
- **Nada de arquivos locais.** Configurações (`config_*.json`), cortes gerados, caches, logs e marca pessoal ficam fora do git. O `.gitignore` já cobre isso.
- **Nada de segredos.** Nunca envie chaves, tokens ou arquivos `.env`.
- **Tudo local.** O Serial ClipPRO processa tudo na máquina do usuário. Mudanças que enviem dados do usuário para serviços externos não serão aceitas.

## Licença

O Serial ClipPRO é distribuído sob a [Licença MIT](../LICENSE). Ao contribuir, você concorda que a sua contribuição será licenciada sob a mesma licença.
