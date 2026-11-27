import { useDialog } from './components/layout/useDialog';
import React, { useState, useEffect, useRef } from 'react';

import { apiFetch } from './api';
import { useI18n, useTAtual } from './i18n/useI18n';

import { GalleryDialog } from './components/layout/GalleryDialog';
import { Header } from './components/layout/Header';
import { SeletorIdioma } from './components/layout/SeletorIdioma';
import { Footer } from './components/layout/Footer';
import { Tabs } from './components/layout/Tabs';
import { PipelineTab } from './components/tabs/PipelineTab';
import { StepsTab } from './components/tabs/StepsTab';
import { SocialTab } from './components/tabs/SocialTab';
import { BrandTab } from './components/tabs/BrandTab';
import { ReviewTab } from './components/tabs/ReviewTab';
import { CopyrightTab } from './components/tabs/CopyrightTab';
import { GuideTab } from './components/tabs/GuideTab';

function lerPreferencia(chave, padrao) {
  try { return window.localStorage.getItem(chave) ?? padrao; } catch { return padrao; }
}

function salvarPreferencia(chave, valor) {
  try { window.localStorage.setItem(chave, valor); } catch { /* armazenamento indisponível */ }
}

function App() {
  const { notify, ask } = useDialog();
  const { t } = useI18n();
  const tAtual = useTAtual();
  async function limparCache() {
    try {
      const dados = await (await apiFetch('/revisao/cache')).json();
      if (!await ask(t('app.limparCachePergunta', { bases: dados.bases, mb: (dados.bytes/1024/1024).toFixed(1) }), t('app.limparCacheTitulo'))) return;
      const resultado = await (await apiFetch('/revisao/cache', { method: 'DELETE' })).json();
      notify(resultado.mensagem);
    } catch (e) { notify(e.message); }
  }
  const [entrada, setEntrada] = useState('');
  const [maxCortes, setMaxCortes] = useState(50);
  const [ignorarInicio, setIgnorarInicio] = useState(0);
  const [modoCuradoria, setModoCuradoria] = useState('hibrido');
  const [limiteAmostras, setLimiteAmostras] = useState(40);
  const [termosJogo, setTermosJogo] = useState('');
  // Idioma e foco costumam se repetir entre lives; ficam lembrados neste navegador.
  const [idioma, setIdioma] = useState(() => lerPreferencia('clippro_idioma', 'pt'));
  const [foco, setFoco] = useState(() => lerPreferencia('clippro_foco', ''));
  useEffect(() => { salvarPreferencia('clippro_idioma', idioma); }, [idioma]);
  useEffect(() => { salvarPreferencia('clippro_foco', foco); }, [foco]);
  const [detalhesClips, setDetalhesClips] = useState({});
  const executandoRef = useRef(false);
  const [statusInfo, setStatusInfo] = useState({ 
    status: 'Awaiting', 
    progresso_pct: 0, 
    videos: [],
    tempo_decorrido: '00:00',
    tempo_total: '00:00'
  });
  const [carregando, setCarregando] = useState(false);
  const [modoInput, setModoInput] = useState('arquivo');
  const [abaAtiva, setAbaAtiva] = useState('pipeline');
  // Seção do Como usar pedida por um botão "?"; o contador força rolar de novo ao repetir o clique.
  const [secaoGuia, setSecaoGuia] = useState(null);
  useEffect(() => {
    const abrir = (evento) => { setAbaAtiva('comoUsar'); setSecaoGuia({ id: evento.detail, vez: Date.now() }); };
    window.addEventListener('clippro:como-usar', abrir);
    return () => window.removeEventListener('clippro:como-usar', abrir);
  }, []);

  const [dialog, setDialog] = useState(null);
  const [excluindo, setExcluindo] = useState(false);
  const exclusaoRef = useRef(false);
  const [selecionados, setSelecionados] = useState({});

  // 📂 Função para buscar os clipes físicos salvos na pasta (com sincronização instantânea em tempo real)
  const carregarClipsSalvos = async () => {
    try {
      const res = await apiFetch('/clips');
      const data = await res.json();
      
      const listaClips = data.clips || [];
      setDetalhesClips(Object.fromEntries(listaClips.map(c => [`/videos/${c.nome}`, c.curadoria])));
      const pathsClips = listaClips.map(c => {
        const nomeArquivo = typeof c === 'string' ? c : (c.nome || c.filename);
        if (nomeArquivo.startsWith('/videos/')) return nomeArquivo;
        return `/videos/${nomeArquivo.replace(/^\/+/, '')}`;
      });

      setStatusInfo(prev => ({
        ...prev,
        videos: pathsClips
      }));
    } catch (e) {
      console.error("Erro ao carregar clipes salvos da pasta:", e);
    }
  };

  // Carrega os clipes salvos assim que a aplicação é montada
  useEffect(() => {
    const timer = setTimeout(carregarClipsSalvos, 0);
    return () => clearTimeout(timer);
  }, [abaAtiva]);

  // Recupera também execuções iniciadas antes de recarregar a página.
  useEffect(() => {
    let disposed = false;
    let timer;
    const consultar = async () => {
      try {
        const res = await apiFetch('/status');
        const data = await res.json();
        if (disposed) return;
        const terminou = executandoRef.current && !data.executando;
        executandoRef.current = Boolean(data.executando);
        setCarregando(Boolean(data.executando));
        setStatusInfo(prev => ({ ...data, videos: prev.videos }));
        if (terminou) await carregarClipsSalvos();
      } catch (e) {
        if (!disposed) setStatusInfo(prev => ({ ...prev, status: tAtual.current('app.semComunicacao', { erro: e.message }), semComunicacao: true }));
      } finally {
        if (!disposed) timer = setTimeout(consultar, 1000);
      }
    };
    consultar();
    return () => { disposed = true; clearTimeout(timer); };
  }, [tAtual]);

  const iniciarGeracao = async () => {
    if (!entrada) {
      notify(t('app.semEntrada'));
      return;
    }
    setCarregando(true);
    try {
      await apiFetch('/iniciar-pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entrada, max_cortes: Number(maxCortes), ignorar_inicio_segundos: Number(ignorarInicio),
          modo_curadoria: modoCuradoria, termos_jogo: termosJogo, limite_amostras: Number(limiteAmostras),
          idioma, foco })
      });
      executandoRef.current = true;
    } catch (e) {
      notify(t('app.erroIniciar', { erro: e.message }));
      setCarregando(false);
    }
  };

  const toggleCheckbox = (vidUrl) => {
    setSelecionados(prev => ({
      ...prev,
      [vidUrl]: !prev[vidUrl]
    }));
  };

  const selecionarTodos = () => {
    setSelecionados(Object.fromEntries(statusInfo.videos.map(url => [url, true])));
  };

  const limparSelecao = () => setSelecionados({});

  const exportarSelecionados = async () => {
    const listaParaExportar = Object.keys(selecionados).filter(k => selecionados[k] === true);
    if (listaParaExportar.length === 0) {
      notify(t('app.semSelecaoExportar'));
      return;
    }

    try {
      const res = await apiFetch('/exportar-selecionados', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ videos: listaParaExportar })
      });
      const data = await res.json();
      notify(t('app.exportado', { mensagem: data.mensagem, pasta: data.pasta_destino }), t('app.exportacaoConcluida'));
    } catch (e) {
      notify(t('app.erroExportar', { erro: e.message }));
    }
  };

  // 🗑️ Exclui os cortes selecionados com proteção client-side para libertação de streams
  const deletarSelecionados = () => {
    const videos = statusInfo.videos.filter(url => selecionados[url]);
    setDialog(videos.length ? {
      title: t('app.excluirTitulo'),
      message: t('app.excluirPergunta', { total: videos.length }),
      confirm: true, videos,
    } : { title: t('app.nenhumSelecionado'), message: t('app.marqueParaExcluir') });
  };

  const confirmarExclusao = async () => {
    if (exclusaoRef.current || !dialog?.confirm) return;
    exclusaoRef.current = true;
    setExcluindo(true);
    const videos = dialog.videos;
    document.querySelectorAll('video[data-clip-url]').forEach(player => {
      if (!videos.includes(player.dataset.clipUrl)) return;
      player.pause();
      player.removeAttribute('src');
      player.querySelectorAll('source').forEach(source => source.removeAttribute('src'));
      player.load();
    });
    setStatusInfo(prev => ({ ...prev, videos: prev.videos.filter(url => !videos.includes(url)) }));
    try {
      await new Promise(resolve => setTimeout(resolve, 150));
      const res = await apiFetch('/deletar-selecionados', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ videos }),
      });
      const data = await res.json();
      const removidos = new Set([...(data.arquivos || []), ...(data.ausentes || [])]);
      setSelecionados(prev => Object.fromEntries(Object.entries(prev).filter(([url]) => !removidos.has(url.split('/').pop()))));
      const problemas = [...(data.falhas || []), ...(data.avisos || [])];
      setDialog({ title: problemas.length ? t('app.exclusaoPendencias') : t('app.galeriaAtualizada'),
        message: data.mensagem, details: problemas });
    } catch (e) {
      setDialog({ title: t('app.erroExcluir'), message: e.message });
    } finally {
      await carregarClipsSalvos();
      setExcluindo(false);
      exclusaoRef.current = false;
    }
  };

  return (
    <div className="min-h-screen bg-[#05070b] text-slate-100 p-3 sm:p-5 font-sans selection:bg-[#9333ea] selection:text-white flex flex-col justify-between">
      
      <div>
        <Header />
        <div className="mb-4 flex justify-start"><SeletorIdioma /></div>

        <div className="w-full mx-auto flex flex-col gap-6">
          
          <Tabs abaAtiva={abaAtiva} setAbaAtiva={setAbaAtiva} limparCache={limparCache} />

          <main className="flex flex-col gap-6">
            
            {abaAtiva === 'pipeline' && (
              <PipelineTab 
                abrirRevisao={() => setAbaAtiva('revisao')}
                modoInput={modoInput} setModoInput={setModoInput}
                entrada={entrada} setEntrada={setEntrada}
                maxCortes={maxCortes} setMaxCortes={setMaxCortes}
                ignorarInicio={ignorarInicio} setIgnorarInicio={setIgnorarInicio}
                modoCuradoria={modoCuradoria} setModoCuradoria={setModoCuradoria}
                limiteAmostras={limiteAmostras} setLimiteAmostras={setLimiteAmostras}
                termosJogo={termosJogo} setTermosJogo={setTermosJogo} detalhesClips={detalhesClips}
                idioma={idioma} setIdioma={setIdioma} foco={foco} setFoco={setFoco}
                carregando={carregando} iniciarGeracao={iniciarGeracao}
                statusInfo={statusInfo}
                selecionados={selecionados} toggleCheckbox={toggleCheckbox} 
                selecionarTodos={selecionarTodos} limparSelecao={limparSelecao}
                exportarSelecionados={exportarSelecionados}
                deletarSelecionados={deletarSelecionados}
              />
            )}

            {abaAtiva === 'passos' && <StepsTab />}

            {abaAtiva === 'social' && <SocialTab />}

            {abaAtiva === 'marca' && <BrandTab />}
            {abaAtiva === 'revisao' && <ReviewTab />}

            {abaAtiva === 'copyright' && <CopyrightTab />}
            {abaAtiva === 'comoUsar' && <GuideTab secao={secaoGuia} />}

          </main>
        </div>
      </div>

      <GalleryDialog dialog={dialog} busy={excluindo} onClose={() => setDialog(null)} onConfirm={confirmarExclusao} />

      <Footer />

    </div>
  );
}

export default App;
