# Serial ClipPRO

**Sua live continua em cada corte.**

Lives longas, pouco tempo para editar? O Serial ClipPRO analisa suas VODs e prepara cortes verticais enquanto você está longe do PC. Depois, você revisa e escolhe o que publicar.

Este repositório reúne os pacotes de instalação e as versões públicas do aplicativo para Windows.

## Download

Acesse **Releases**, neste repositório, e baixe o ZIP anexado à versão desejada.

> Baixe o pacote **Serial ClipPRO**. Os arquivos automáticos “Source code (zip)” e “Source code (tar.gz)” não são o aplicativo.

## O que o aplicativo faz

- Processa VODs de Twitch, YouTube e Kick, além de vídeos locais.
- Seleciona momentos por picos de áudio, contexto ou modo híbrido.
- Gera cortes verticais em formato 9:16 com legendas.
- Permite ajustar o enquadramento da webcam e incluir sua marca em PNG.
- Oferece uma galeria para revisar, baixar, exportar e excluir cortes.
- Reúne atalhos para acessar as plataformas e publicar manualmente.

A IA auxilia na seleção. Revise os cortes e as legendas antes de publicar.

## Instalação e primeiro uso

1. Baixe o ZIP disponível em **Releases**.
2. Extraia **todo o conteúdo** para uma pasta no computador.
3. Abra a pasta extraída e execute **Instalar dependencias.bat**.
4. Aguarde a preparação dos pré-requisitos e o download dos modelos.
5. Se aparecer a janela inicial do **Ollama**, prossiga com o **uso local**. Não é necessário usar modelos cloud.
6. Ao aparecer **SUCESSO**, a preparação terminou. Pressione uma tecla para fechar o console.
7. A abertura do aplicativo será solicitada automaticamente. Caso a janela não apareça, execute **Serial ClipPRO.exe**.

Nos próximos usos, basta abrir **Serial ClipPRO.exe**.

**Mantenha a pasta `_internal` e os demais arquivos junto do executável.** Não execute o aplicativo de dentro do ZIP nem copie apenas o EXE.

### Durante a preparação

- É necessária conexão com a internet.
- Os modelos exigem downloads de vários GB e espaço disponível em disco.
- O Windows pode solicitar permissão para instalar componentes.
- Se houver solicitação de reinício, reinicie o computador e execute o BAT novamente.
- A preparação do Whisper pode levar alguns minutos. O console informa periodicamente que o processo continua em execução.

Python e Node.js não precisam estar instalados no computador de destino.

## Primeiro teste

Comece com um vídeo curto antes de processar uma VOD longa:

1. Informe uma URL compatível ou o caminho completo de um arquivo local.
2. Escolha o modo de análise.
3. Ajuste o enquadramento e a marca, se desejar.
4. Inicie o processamento.
5. Revise os vídeos na galeria e exporte seus favoritos.

Mantenha o computador ligado e sem entrar em suspensão durante o processamento.

## Modos de análise

| Modo | Como funciona |
|---|---|
| **Picos de áudio** | Busca candidatos a partir da intensidade sonora e analisa os trechos selecionados. |
| **Híbrido** | Combina picos de áudio com amostras distribuídas ao longo do conteúdo. |
| **Contexto completo** | Transcreve e analisa toda a fonte, exigindo mais tempo de processamento. |

Nenhum modo garante encontrar todos os momentos interessantes. O tempo varia conforme a duração da VOD, a conexão, o hardware e as configurações escolhidas.

## Processamento local e hardware

A transcrição e a análise por IA utilizam **Whisper e Ollama no computador**.

- O Whisper usa CPU por compatibilidade.
- A renderização tenta utilizar NVENC em GPUs NVIDIA compatíveis.
- Quando NVENC não está disponível, a renderização utiliza CPU.
- A versão atual não utiliza AMD AMF para renderização.

O processamento local não elimina a necessidade de internet para baixar modelos, acessar VODs e abrir as plataformas sociais.

## Onde ficam os arquivos?

Por padrão, os dados são armazenados em:

`%LOCALAPPDATA%\Serial ClipPRO\`

Cole esse caminho na barra de endereços do Explorador de Arquivos.

| Pasta | Conteúdo |
|---|---|
| `Cortes_Prontos` | Vídeos disponíveis na galeria. |
| `Cortes_Exportados` | Cópias dos cortes exportados em lote. |
| `transcricoes` | Cache de transcrições. |
| `relatorios_curadoria` | Relatórios da análise. |
| `marca` | Imagem e configuração da marca do canal. |
| `logs` | Registros de diagnóstico. |

Excluir um corte da galeria não apaga as cópias já exportadas. O botão **Descarregar** permite escolher onde salvar um vídeo individual.

## Redes sociais

A aba Social reúne atalhos para Instagram, TikTok, YouTube, Twitch e Kick. BiliBili aparece como **Em breve**.

Login e publicação são feitos manualmente nos sites das plataformas. O aplicativo não publica automaticamente.

Se uma plataforma recusar o login na janela integrada, utilize **Abrir no navegador**.

## Atualização

1. Aguarde o processamento terminar e feche o aplicativo.
2. Baixe o ZIP da nova versão.
3. Extraia o pacote completo em uma nova pasta.
4. Execute **Instalar dependencias.bat** para verificar o ambiente.
5. Abra o novo executável.

Os dados normalmente permanecem na pasta do usuário, separada da instalação. Consulte as notas da Release para eventuais instruções específicas de atualização.

## Problemas e sugestões

O projeto está em desenvolvimento. Para relatar um problema, abra uma **Issue** neste repositório e informe:

- Versão do Serial ClipPRO.
- Versão do Windows, processador, memória RAM e GPU.
- Origem do vídeo e modo de análise utilizado.
- Etapa em que ocorreu o problema.
- Mensagem de erro e, se possível, uma captura de tela.

Para problemas de instalação, consulte:

`%LOCALAPPDATA%\Serial ClipPRO\instalacao.log`

Revise os logs antes de publicá-los e remova informações pessoais, tokens ou URLs privadas.

## Apoie o projeto

Se o Serial ClipPRO ajudar na sua rotina, você pode contribuir com seu desenvolvimento:

- [Apoiar via Pix — LivePix](https://livepix.gg/serialhealer)
- [Apoiar via PayPal](https://www.paypal.com/donate/?business=6KXEQHVYHLLQ8&no_recurring=0&item_name=Host%2FVPS&currency_code=BRL)

O apoio é voluntário.

## Uso e distribuição

O Serial ClipPRO é disponibilizado para uso pessoal gratuito. Este repositório distribui o aplicativo e não representa uma publicação do código-fonte sob licença de código aberto.

Redistribuição, reutilização e uso comercial devem ser discutidos com o autor. Componentes de terceiros permanecem sujeitos às respectivas licenças.

---

Desenvolvido por **SerialHealer**.
