import React, { useState } from 'react';
import { useDialog } from './useDialog';
import { version } from '../../../../version.json';
import { useI18n } from '../../i18n/useI18n';
import { AtualizacaoDialog } from './AtualizacaoDialog';

export function Header() {
  const { notify } = useDialog();
  const { t } = useI18n();
  const [atualizacaoAberta, setAtualizacaoAberta] = useState(false);
  const donations = [
    ['pix', t('cabecalho.doarPix'), 'https://livepix.gg/serialhealer'],
    ['paypal', t('cabecalho.doarPaypal'), 'https://www.paypal.com/donate/?business=6KXEQHVYHLLQ8&no_recurring=0&item_name=Host%2FVPS&currency_code=BRL'],
  ];
  return (
    <header className="mb-3 border-b border-[#1b1528] pb-4 flex flex-wrap gap-4 items-center justify-between w-full mx-auto">
      <div className="flex items-center gap-4">
        <div className="relative w-12 h-12 rounded-full p-[2px] bg-gradient-to-tr from-[#b3ff33] via-[#9333ea] to-[#00ffff] shadow-[0_0_15px_rgba(147,51,234,0.4)] flex-shrink-0">
          <img 
            src="https://static-cdn.jtvnw.net/jtv_user_pictures/96fca220-b708-41a9-aef9-79acd713e459-profile_image-70x70.png" 
            alt="SerialHealer Logo" 
            className="w-full h-full object-cover rounded-full bg-black"
          />
        </div>
        <div>
          <h1 className="text-2xl font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-[#b3ff33] via-[#9333ea] to-[#00ffff] drop-shadow-[0_2px_10px_rgba(147,51,234,0.3)]">
            Serial ClipPRO - LOCAL AI
          </h1>
          <span className="mt-1 flex flex-wrap items-center gap-2">
            <span className="inline-block rounded-full border border-purple-500/40 bg-purple-950/40 px-2 py-0.5 text-xs font-mono text-cyan-300">{t('cabecalho.versao', { versao: version })}</span>
            <button type="button" onClick={() => setAtualizacaoAberta(true)}
              className="text-[11px] text-slate-400 underline decoration-dotted underline-offset-2 hover:text-cyan-300 focus-visible:outline focus-visible:outline-cyan-300">{t('cabecalho.verificarAtualizacoes')}</button>
          </span>
          <p className="text-slate-400 text-xs font-mono mt-0.5">{t('cabecalho.subtitulo')}</p>
        </div>
      </div>

      <div className="flex flex-col gap-3 items-end">
      <div className="flex items-center gap-2 bg-[#0a0712] px-4 py-2 rounded-xl border border-[#1b1528] text-xs font-mono">
        <span className="w-2.5 h-2.5 rounded-full bg-[#b3ff33] animate-pulse"></span>
        <span className="text-slate-300">{t('cabecalho.motorAtivo')}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {donations.map(([id, label, url]) => <a key={id} href={url} target="_blank" rel="noopener noreferrer"
          onClick={async event => {
            if (!window.pywebview?.api?.abrir_doacao) return;
            event.preventDefault();
            try {
              if (!await window.pywebview.api.abrir_doacao(id)) notify(t('cabecalho.navegadorFalhou'), t('cabecalho.doacao'));
            } catch (error) { notify(error.message, t('cabecalho.doacao')); }
          }}
          className="rounded-xl p-[1px] bg-gradient-to-r from-[#b3ff33] via-[#9333ea] to-[#00ffff] shadow-[0_0_12px_rgba(147,51,234,0.35)] hover:shadow-[0_0_20px_rgba(0,255,255,0.35)] transition-shadow focus-visible:outline focus-visible:outline-cyan-300">
          <span className="block rounded-xl bg-[#0a0712] px-4 py-2 text-xs font-bold text-slate-100">{label}</span>
        </a>)}
      </div>
      </div>
      <AtualizacaoDialog aberto={atualizacaoAberta} onFechar={() => setAtualizacaoAberta(false)} />
    </header>
  );
}
