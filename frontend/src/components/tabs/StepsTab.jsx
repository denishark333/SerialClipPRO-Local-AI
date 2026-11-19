import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../api';

function ModelCard() {
  const [info, setInfo] = useState(null);
  const [escolhido, setEscolhido] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState('');

  async function carregar() {
    try {
      const dados = await (await apiFetch('/ia')).json();
      setInfo(dados);
      setEscolhido(dados.modelo_id);
    } catch (e) { setMensagem(e.message); }
  }
  useEffect(() => { const timer = setTimeout(carregar, 0); return () => clearTimeout(timer); }, []);

  async function salvar() {
    setSalvando(true); setMensagem('');
    try {
      const dados = await (await apiFetch('/ia', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ modelo: escolhido }),
      })).json();
      setInfo(dados);
      setEscolhido(dados.modelo_id);
      const salvo = dados.instalados.find(m => m.id === dados.modelo_id);
      setMensagem(`Modelo salvo: ${salvo?.nome || dados.modelo}. Vale para as próximas execuções.`);
    } catch (e) { setMensagem(e.message); }
    finally { setSalvando(false); }
  }

  const instalados = info?.instalados || [];
  const selecionado = instalados.find(m => m.id === escolhido);
  const atual = instalados.find(m => m.id === info?.modelo_id);
  const rotulo = m => [
    m.nome,
    m.perfil,
    m.memoria_gb ? `~${String(m.memoria_gb).replace('.', ',')} GB de vídeo` : `${String(m.tamanho_gb).replace('.', ',')} GB em disco`,
    m.cabe_na_gpu === false ? 'não cabe na sua placa' : '',
  ].filter(Boolean).join(' · ');
  return (
    <div className="p-4 border border-slate-800 rounded-xl text-sm flex flex-col gap-2">
      <h3 className="text-base font-bold text-slate-200">Modelo de IA da curadoria</h3>
      {!info && !mensagem && <p className="text-slate-400">Consultando o Ollama...</p>}
      {info && !info.ollama_online && <p className="text-amber-400">O Ollama não respondeu. Abra o Ollama e clique em Atualizar.</p>}
      {info && info.ollama_online && !info.modelo_instalado && (
        <p className="text-amber-400">O modelo configurado ({info.modelo}) não está instalado. Escolha outro abaixo.</p>
      )}
      {instalados.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <select value={escolhido} onChange={e => setEscolhido(e.target.value)}
            className="bg-[#0e0a1a] border border-[#1f1633] rounded px-3 py-2 text-slate-200">
            {!selecionado && <option value={escolhido}>{escolhido}</option>}
            {instalados.map(m => <option key={m.id} value={m.id}>{rotulo(m)}</option>)}
          </select>
          <button disabled={salvando || escolhido === info?.modelo_id} onClick={salvar}
            className="bg-purple-700 rounded px-4 py-2 disabled:opacity-50">{salvando ? 'Salvando...' : 'Usar este modelo'}</button>
          <button onClick={carregar} className="border border-slate-700 rounded px-3 py-2">Atualizar</button>
        </div>
      )}
      {selecionado && (
        <p className="text-slate-300">
          {selecionado.descricao}
          {selecionado.cabe_na_gpu === false && (
            <span className="block text-amber-400 mt-1">
              Este modelo precisa de mais memória de vídeo do que sua placa tem ({String(info.memoria_gpu_gb).replace('.', ',')} GB).
              Ele vai rodar, mas parte dele usará a CPU e a curadoria ficará bem mais lenta.
            </span>
          )}
        </p>
      )}
      <p className="text-slate-400">
        Em uso: <span className="text-slate-200">{atual?.nome || info?.modelo || '—'}</span>
        {info?.memoria_gpu_gb ? ` · sua placa tem ${String(info.memoria_gpu_gb).replace('.', ',')} GB de memória de vídeo` : ''}.
        Para instalar outro modelo, use <code>ollama pull nome-do-modelo</code> e clique em Atualizar.
      </p>
      <p role="status" className="text-slate-300">{mensagem}</p>
    </div>
  );
}

export function StepsTab() {
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
      <div className="border-b border-[#1b1528] pb-3">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span className="text-[#9333ea]">📖</span> Primeiros Passos com o Serial ClipPRO
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Guia rápido para trabalhar com VODs, streams e conteúdo de longa duração sem perder tempo na configuração.
        </p>
      </div>

      <div className="p-4 border border-slate-800 rounded-xl text-sm">
        <button disabled={checking} onClick={check} className="bg-purple-700 rounded px-4 py-2">{checking ? 'Verificando...' : 'Verificar dependências'}</button>
        <p className="text-slate-400 mt-2">Na versão 2.0, o instalador prepara os componentes e baixa os modelos automaticamente. Depois, abra o ClipPRO pelo atalho. Para retomar uma preparação interrompida, use “Preparar ou reparar Serial ClipPRO” no menu Iniciar.</p>
        <p role="status">{error}</p>
        {environment && <div className="mt-3">
          {Object.entries(environment.dependencias).map(([name, status]) => <p key={name}>{name}: {status}</p>)}
          <p className="mt-2 break-all">Seus arquivos: {environment.pasta_dados}</p>
          <p>{environment.observacao}</p>
        </div>}
      </div>
      <ModelCard />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#0e0a1a] border border-[#1f1633] p-4 rounded-xl flex flex-col gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#9333ea]/20 text-[#9333ea] font-mono font-bold flex items-center justify-center text-sm">01</div>
          <h3 className="text-base font-bold text-slate-200">Defina a fonte</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Cole uma URL de YouTube, Twitch ou Kick ou escolha um vídeo local. Em seguida, selecione o modo ideal:
            <span className="block mt-1 text-purple-400 font-medium">Híbrido</span>
            <span className="block text-cyan-400 font-medium">Contexto completo</span>
            <span className="block text-emerald-400 font-medium">Picos de áudio</span>
          </p>
        </div>

        <div className="bg-[#0e0a1a] border border-[#1f1633] p-4 rounded-xl flex flex-col gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#b3ff33]/20 text-[#b3ff33] font-mono font-bold flex items-center justify-center text-sm">02</div>
          <h3 className="text-base font-bold text-slate-200">IA e curadoria</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            Whisper e Ollama analisam o material, montam o raciocínio da curadoria e geram relatórios em JSON para revisão antes da renderização final.
          </p>
        </div>

        <div className="bg-[#0e0a1a] border border-[#1f1633] p-4 rounded-xl flex flex-col gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#00ffff]/20 text-[#00ffff] font-mono font-bold flex items-center justify-center text-sm">03</div>
          <h3 className="text-base font-bold text-slate-200">Render e exportação</h3>
          <p className="text-sm text-slate-400 leading-relaxed">
            O sistema renderiza versões verticais 9:16 em alta velocidade e salva os clipes na galeria para você revisar, exportar ou excluir com segurança.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-[#0e0a1a]/70 border border-[#1f1633] p-4 rounded-xl">
          <div className="flex items-center gap-2 text-slate-200 font-bold text-base mb-3">
            <span className="text-[#00ffff]">✅</span> Checklist rápido
          </div>
          <ul className="space-y-2 text-sm text-slate-400 list-disc list-inside">
            <li>FFmpeg instalado e no PATH</li>
            <li>Ollama em execução</li>
            <li>Modelo de IA escolhido instalado no Ollama</li>
            <li>Entrada válida e modo de curadoria selecionado</li>
            <li>Preview gerado antes do pipeline principal</li>
          </ul>
        </div>

        <div className="bg-[#0e0a1a]/70 border border-[#1f1633] p-4 rounded-xl">
          <div className="flex items-center gap-2 text-slate-200 font-bold text-base mb-3">
            <span className="text-[#b3ff33]">💡</span> Dicas úteis
          </div>
          <ul className="space-y-2 text-sm text-slate-400 list-disc list-inside">
            <li>Use o modo Híbrido para VODs longas e grandes volumes de conteúdo.</li>
            <li>O modo Contexto completo é melhor para curadoria aprofundada e análise narrativa.</li>
            <li>O botão Stop encerra o processamento com segurança e evita etapas pendentes.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
