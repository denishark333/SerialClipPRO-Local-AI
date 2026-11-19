import React, { useState } from 'react';
import { apiFetch } from '../../api';

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
            <li>Modelo Llama 3.1 disponível</li>
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
