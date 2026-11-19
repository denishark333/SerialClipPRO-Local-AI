import React from 'react';
import { YouTubeIcon, KickIcon, TwitchIcon, InstagramIcon, TikTokIcon } from '../icons/Icons';

export function CopyrightTab({ abrirMarca }) {
  return (
    <div className="bg-[#0a0712] border border-[#1b1528] p-8 rounded-2xl shadow-xl w-full lg:w-[94%] mx-auto flex flex-col gap-6">
      
      {/* Cabeçalho */}
      <div className="border-b border-[#1b1528] pb-4 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="text-[#00ffff]">⚖️</span> Copyrights & Canais Oficiais
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Informações de autoria, diretrizes e canais oficiais vinculados a  SerialHealer.
          </p>
        </div>
        <span className="bg-[#53FC18]/10 border border-[#53FC18]/20 text-[#53FC18] text-xs font-mono px-3 py-1 rounded-lg">
          Recursos e canais
        </span>
      </div>

      {/* Caixa de Aviso de Direitos Autorais */}
      <div className="bg-[#0e0a1a] border border-[#1f1633] p-4 rounded-xl text-sm font-mono text-slate-300 leading-relaxed">
        © 2026 Serial ClipPRO • Desenvolvido e mantido por <span className="text-[#b3ff33] font-bold">SerialHealer</span>. Todos os direitos reservados. Software de uso pessoal focado em automação de conteúdo para Live Streams.
      </div>

      {/* Controles de Automação & Proteção (Fusão com a parte funcional) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <article className="rounded-xl border border-amber-600/30 bg-[#0e0a1a] p-5 space-y-3">
          <h3 className="font-bold text-amber-200">Música e direitos autorais</h3>
          <p className="text-sm text-slate-300 leading-relaxed">O ClipPRO não identifica músicas protegidas nem silencia trechos automaticamente. Um corte gerado pode conter áudio de terceiros.</p>
          <span className="inline-block rounded-full border border-amber-600/40 px-3 py-1 text-xs text-amber-200">Filtro automático não implementado</span>
        </article>
        <article className="rounded-xl border border-cyan-500/40 bg-gradient-to-br from-purple-950/40 to-cyan-950/20 p-5 space-y-3">
          <h3 className="font-bold text-cyan-200">Marca do canal</h3>
          <p className="text-sm text-slate-300 leading-relaxed">Envie seu PNG e configure a aplicação da marca nas novas execuções.</p>
          <button onClick={abrirMarca} className="rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 px-4 py-3 text-sm font-bold hover:brightness-110 focus-visible:outline-2 focus-visible:outline-cyan-400">Configurar minha marca</button>
        </article>
        <article className="rounded-xl border border-purple-800/60 bg-[#0e0a1a] p-5 space-y-3">
          <h3 className="font-bold text-purple-200">Isolamento de voz</h3>
          <p className="text-sm text-slate-300 leading-relaxed">Whisper transcreve a fala para gerar legendas. Ele não remove música do vídeo. Separação de voz e acompanhamento ainda não está integrada.</p>
          <span className="inline-block rounded-full border border-purple-600/40 px-3 py-1 text-xs text-purple-200">Separação de áudio não implementada</span>
        </article>
      </div>

      <div className="flex flex-col gap-3">
        <span className="text-sm font-mono text-slate-400 uppercase tracking-wider">Acesse os canais oficiais:</span>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          
          <a 
            href="https://youtube.com/@serialhealer" 
            target="_blank" 
            rel="noreferrer"
            className="bg-[#0e0a1a] border border-[#1f1633] hover:border-[#FF0000]/40 p-4 rounded-xl flex items-center gap-3 transition group"
          >
            <div className="w-8 h-8 rounded-lg bg-[#FF0000]/10 text-[#FF0000] flex items-center justify-center border border-[#FF0000]/20">
              <YouTubeIcon className="w-4 h-4" />
            </div>
            <span className="text-xs font-mono text-slate-200 group-hover:text-[#FF0000] transition">
              YouTube: @serialhealer
            </span>
          </a>

          <a 
            href="https://kick.com/SerialHealer" 
            target="_blank" 
            rel="noreferrer"
            className="bg-[#0e0a1a] border border-[#1f1633] hover:border-[#53FC18]/40 p-4 rounded-xl flex items-center gap-3 transition group"
          >
            <div className="w-8 h-8 rounded-lg bg-[#53FC18]/10 text-[#53FC18] flex items-center justify-center border border-[#53FC18]/20">
              <KickIcon className="w-4 h-4" />
            </div>
            <span className="text-xs font-mono text-slate-200 group-hover:text-[#53FC18] transition">
              Kick: SerialHealer
            </span>
          </a>

          <a 
            href="https://twitch.tv/serialhealer_" 
            target="_blank" 
            rel="noreferrer"
            className="bg-[#0e0a1a] border border-[#1f1633] hover:border-[#9146FF]/40 p-4 rounded-xl flex items-center gap-3 transition group"
          >
            <div className="w-8 h-8 rounded-lg bg-[#9146FF]/10 text-[#9146FF] flex items-center justify-center border border-[#9146FF]/20">
              <TwitchIcon className="w-4 h-4" />
            </div>
            <span className="text-xs font-mono text-slate-200 group-hover:text-[#9146FF] transition">
              Twitch: serialhealer_
            </span>
          </a>

          <a 
            href="https://instagram.com/serialhealer_" 
            target="_blank" 
            rel="noreferrer"
            className="bg-[#0e0a1a] border border-[#1f1633] hover:border-[#E1306C]/40 p-4 rounded-xl flex items-center gap-3 transition group"
          >
            <div className="w-8 h-8 rounded-lg bg-[#E1306C]/10 text-[#E1306C] flex items-center justify-center border border-[#E1306C]/20">
              <InstagramIcon className="w-4 h-4" />
            </div>
            <span className="text-xs font-mono text-slate-200 group-hover:text-[#E1306C] transition">
              Instagram: @serialhealer_
            </span>
          </a>

          <a href="https://www.tiktok.com/@serialhealer_" target="_blank" rel="noreferrer" className="bg-[#0e0a1a] border border-[#1f1633] hover:border-[#ff0050]/40 p-4 rounded-xl flex items-center gap-3 transition group md:col-span-2">
            <div className="w-8 h-8 rounded-lg bg-[#ff0050]/10 text-[#ff0050] flex items-center justify-center border border-[#ff0050]/20">
              <TikTokIcon className="w-4 h-4" />
            </div>
            <span className="text-xs font-mono text-slate-200 group-hover:text-[#ff0050] transition">
              TikTok: @serialhealer_
            </span>
          </a>

        </div>
      </div>

    </div>
  );
}
