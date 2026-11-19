import React from 'react';

export function Tabs({ abaAtiva, setAbaAtiva, limparCache }) {
  return (
    <div className="bg-[#0a0712] border border-[#1b1528] p-3 rounded-2xl shadow-xl flex items-center gap-2 overflow-x-auto">
      <button 
        onClick={() => setAbaAtiva('pipeline')}
        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${abaAtiva === 'pipeline' ? 'bg-gradient-to-r from-[#9333ea]/30 to-[#00ffff]/20 border-b-2 border-[#9333ea] text-white shadow' : 'text-slate-400 hover:bg-[#0e0a1a] hover:text-slate-200'}`}
      >
        Pipeline VOD & Cortes
      </button>
      <button onClick={() => setAbaAtiva('marca')} className={`px-5 py-2.5 rounded-xl text-xs font-bold whitespace-nowrap ${abaAtiva === 'marca' ? 'bg-purple-900 text-white' : 'text-slate-400'}`}>Marca do canal</button>


      <button 
        onClick={() => setAbaAtiva('passos')}
        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${abaAtiva === 'passos' ? 'bg-gradient-to-r from-[#9333ea]/30 to-[#00ffff]/20 border-b-2 border-[#9333ea] text-white shadow' : 'text-slate-400 hover:bg-[#0e0a1a] hover:text-slate-200'}`}
      >
        Primeiros Passos
      </button>

      <button 
        onClick={() => setAbaAtiva('social')}
        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${abaAtiva === 'social' ? 'bg-gradient-to-r from-[#9333ea]/30 to-[#00ffff]/20 border-b-2 border-[#9333ea] text-white shadow' : 'text-slate-400 hover:bg-[#0e0a1a] hover:text-slate-200'}`}
      >
        Social • Publicar
      </button>

      <button 
        onClick={() => setAbaAtiva('copyright')}
        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${abaAtiva === 'copyright' ? 'bg-gradient-to-r from-[#9333ea]/30 to-[#00ffff]/20 border-b-2 border-[#9333ea] text-white shadow' : 'text-slate-400 hover:bg-[#0e0a1a] hover:text-slate-200'}`}
      >
        Copyrights & Canais
      </button>
      <button onClick={() => setAbaAtiva('revisao')} className={`px-5 py-2.5 rounded-xl text-xs font-bold whitespace-nowrap ${abaAtiva === 'revisao' ? 'bg-purple-900 text-white' : 'text-slate-400'}`}>Revisão de legendas</button>
      <button onClick={limparCache} className="ml-auto shrink-0 border border-cyan-400/60 bg-gradient-to-r from-purple-900 to-cyan-950 rounded-xl px-5 py-3 text-sm font-semibold text-cyan-100 hover:brightness-125 focus-visible:outline-2 focus-visible:outline-cyan-400">Limpar cache</button>
    </div>
  );
}

