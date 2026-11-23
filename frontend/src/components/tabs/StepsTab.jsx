import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../api';
import { useI18n } from '../../i18n/useI18n';

// Os dois cartões do topo seguem o mesmo molde: título, ações e notas retráteis.
const CARTAO = 'bg-[#0e0a1a] border border-[#1f1633] p-5 rounded-xl text-sm flex flex-col gap-3';
const NOTAS = 'text-slate-400 border border-[#1f1633] rounded-lg p-3';

function ModelCard() {
  const { t, idioma } = useI18n();
  // Decimais com vírgula em português e ponto em inglês.
  const num = valor => (idioma === 'pt-BR' ? String(valor).replace('.', ',') : String(valor));
  const [info, setInfo] = useState(null);
  const [escolhido, setEscolhido] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState('');
  const [atualizando, setAtualizando] = useState(false);

  async function carregar() {
    setAtualizando(true);
    try {
      const dados = await (await apiFetch('/ia')).json();
      setInfo(dados);
      setEscolhido(dados.modelo_id);
    } catch (e) { setMensagem(e.message); }
    finally { setAtualizando(false); }
  }
  // Perfil e descrição dos modelos vêm do backend no idioma da interface: recarrega ao trocar.
  useEffect(() => { const timer = setTimeout(carregar, 0); return () => clearTimeout(timer); }, [idioma]);

  async function salvar() {
    setSalvando(true); setMensagem('');
    try {
      const dados = await (await apiFetch('/ia', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ modelo: escolhido }),
      })).json();
      setInfo(dados);
      setEscolhido(dados.modelo_id);
      const salvo = dados.instalados.find(m => m.id === dados.modelo_id);
      setMensagem(t('passos.modeloSalvo', { nome: salvo?.nome || dados.modelo }));
    } catch (e) { setMensagem(e.message); }
    finally { setSalvando(false); }
  }

  const instalados = info?.instalados || [];
  const selecionado = instalados.find(m => m.id === escolhido);
  const atual = instalados.find(m => m.id === info?.modelo_id);
  const rotulo = m => [
    m.nome,
    m.perfil,
    m.memoria_gb ? t('passos.gbVideo', { gb: num(m.memoria_gb) }) : t('passos.gbDisco', { gb: num(m.tamanho_gb) }),
    m.cabe_na_gpu === false ? t('passos.naoCabe') : '',
  ].filter(Boolean).join(' · ');
  const semMudanca = escolhido === info?.modelo_id;
  return (
    <div className={CARTAO}>
      <h3 className="text-base font-bold text-slate-200">{t('passos.modeloTitulo')}</h3>
      {!info && !mensagem && <p className="text-slate-400">{t('passos.consultandoOllama')}</p>}
      {info && !info.ollama_online && <p className="text-amber-400">{t('passos.ollamaOffline')}</p>}
      {info && info.ollama_online && !info.modelo_instalado && (
        <p className="text-amber-400">{t('passos.modeloAusente', { modelo: info.modelo })}</p>
      )}
      <div className="flex flex-wrap items-center gap-2">
        {instalados.length > 0 && <>
          <select value={escolhido} onChange={e => setEscolhido(e.target.value)}
            className="h-10 bg-[#0e0a1a] border border-[#1f1633] rounded px-3 text-slate-200">
            {!selecionado && <option value={escolhido}>{escolhido}</option>}
            {instalados.map(m => <option key={m.id} value={m.id}>{rotulo(m)}</option>)}
          </select>
          <button disabled={salvando || semMudanca} onClick={salvar}
            className="h-10 bg-purple-700 rounded px-4 disabled:opacity-50">
            {salvando ? t('passos.salvando') : semMudanca ? t('passos.selecionado') : t('passos.selecionar')}
          </button>
        </>}
        <button onClick={carregar} disabled={atualizando} aria-label={t('passos.atualizarModelos')} title={t('passos.atualizarModelos')}
          className="h-10 w-10 flex items-center justify-center border border-slate-700 rounded hover:border-purple-500 disabled:opacity-70">
          <svg viewBox="0 0 24 24" className={`w-5 h-5 ${atualizando ? 'animate-spin' : ''}`} fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M21 12a9 9 0 0 1-15.4 6.4L3 16" /><path d="M3 21v-5h5" />
            <path d="M3 12a9 9 0 0 1 15.4-6.4L21 8" /><path d="M21 3v5h-5" />
          </svg>
        </button>
      </div>
      {selecionado?.cabe_na_gpu === false && (
        <p className="text-amber-400">
          {t('passos.memoriaInsuficiente', { gb: num(info.memoria_gpu_gb) })}
        </p>
      )}
      <p role="status" className="text-slate-300 empty:hidden">{mensagem}</p>
      <details className={NOTAS}>
        <summary className="cursor-pointer font-medium text-slate-300">{t('passos.notas')}</summary>
        {selecionado && <p className="mt-2 text-slate-300">{selecionado.descricao}</p>}
        <p className="mt-2">
          {t('passos.emUso')} <span className="text-slate-200">{atual?.nome || info?.modelo || '—'}</span>
          {info?.memoria_gpu_gb ? ` · ${t('passos.suaPlaca', { gb: num(info.memoria_gpu_gb) })}` : ''}.
          {' '}{t('passos.instalarOutro')} <code>ollama pull {t('passos.nomeModelo')}</code> {t('passos.instalarOutroFim')}
        </p>
      </details>
    </div>
  );
}

export function StepsTab() {
  const { t } = useI18n();
  const [environment, setEnvironment] = useState(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState('');
  async function check() {
    setChecking(true); setError('');
    try { setEnvironment(await (await apiFetch('/ambiente')).json()); }
    catch (e) { setError(e.message); }
    finally { setChecking(false); }
  }
  return (
    <div className="w-full lg:w-[94%] mx-auto bg-[#0a0712] border border-[#1b1528] p-6 rounded-2xl shadow-xl flex flex-col gap-6">
      <div className="border-b border-[#1b1528] pb-4 text-center">
        <h2 className="text-xl font-bold text-white">{t('passos.titulo')}</h2>
        <p className="text-sm text-slate-400 mt-1">
          {t('passos.subtitulo')}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full max-w-6xl mx-auto items-start">
      <div className={CARTAO}>
        <h3 className="text-base font-bold text-slate-200">{t('passos.dependencias')}</h3>
        <button disabled={checking} onClick={check} className="self-start h-10 bg-purple-700 rounded px-4">{checking ? t('passos.verificando') : t('passos.verificar')}</button>
        <p role="status" className="empty:hidden">{error}</p>
        {environment && <div className="mt-3">
          {Object.entries(environment.dependencias).map(([name, status]) => <p key={name}>{name}: {status}</p>)}
          <p className="mt-2 break-all">{t('passos.seusArquivos', { pasta: environment.pasta_dados })}</p>
          <p>{environment.observacao}</p>
        </div>}
        <details className={NOTAS}>
          <summary className="cursor-pointer font-medium text-slate-300">{t('passos.notas')}</summary>
          <p className="mt-2">{t('passos.notasInstalador')}</p>
        </details>
      </div>
      <ModelCard />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#0e0a1a] border border-[#1f1633] p-4 rounded-xl flex flex-col gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#9333ea]/20 text-[#9333ea] font-mono font-bold flex items-center justify-center text-sm">01</div>
          <h3 className="text-base font-bold text-slate-200">{t('passos.passo1Titulo')}</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            {t('passos.passo1Texto')}
            <span className="block mt-1 text-purple-400 font-medium">{t('passos.modoHibrido')}</span>
            <span className="block text-cyan-400 font-medium">{t('passos.modoContexto')}</span>
            <span className="block text-emerald-400 font-medium">{t('passos.modoPicos')}</span>
          </p>
        </div>

        <div className="bg-[#0e0a1a] border border-[#1f1633] p-4 rounded-xl flex flex-col gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#b3ff33]/20 text-[#b3ff33] font-mono font-bold flex items-center justify-center text-sm">02</div>
          <h3 className="text-base font-bold text-slate-200">{t('passos.passo2Titulo')}</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            {t('passos.passo2Texto')}
          </p>
        </div>

        <div className="bg-[#0e0a1a] border border-[#1f1633] p-4 rounded-xl flex flex-col gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#00ffff]/20 text-[#00ffff] font-mono font-bold flex items-center justify-center text-sm">03</div>
          <h3 className="text-base font-bold text-slate-200">{t('passos.passo3Titulo')}</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            {t('passos.passo3Texto')}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-[#0e0a1a]/70 border border-[#1f1633] p-4 rounded-xl">
          <div className="flex items-center gap-2 text-slate-200 font-bold text-base mb-3">
            <span className="text-[#00ffff]">✅</span> {t('passos.checklist')}
          </div>
          <ul className="space-y-2 text-sm text-slate-400 list-disc list-inside">
            {['ffmpeg', 'ollama', 'modelo', 'entrada', 'preview'].map(item => <li key={item}>{t(`passos.itensChecklist.${item}`)}</li>)}
          </ul>
        </div>

        <div className="bg-[#0e0a1a]/70 border border-[#1f1633] p-4 rounded-xl">
          <div className="flex items-center gap-2 text-slate-200 font-bold text-base mb-3">
            <span className="text-[#b3ff33]">💡</span> {t('passos.dicas')}
          </div>
          <ul className="space-y-2 text-sm text-slate-400 list-disc list-inside">
            {['hibrido', 'contexto', 'parar'].map(item => <li key={item}>{t(`passos.itensDicas.${item}`)}</li>)}
          </ul>
        </div>
      </div>
    </div>
  );
}
