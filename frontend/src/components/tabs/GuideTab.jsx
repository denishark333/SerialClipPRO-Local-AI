import React, { useEffect, useRef } from 'react';
import { useI18n } from '../../i18n/useI18n';

// Como usar: uma seção por recurso, com texto, vídeo curto de exemplo e dúvidas comuns.
// Novas seções entram em SECOES e ganham as chaves guia.<id>.* nos dicionários.
const SECOES = [
  {
    id: 'podcast',
    etapas: [
      { chave: 'dividida', cor: 'text-cyan-300 border-cyan-400/40 bg-cyan-400/10' },
      { chave: 'close', cor: 'text-amber-300 border-amber-400/40 bg-amber-400/10' },
      { chave: 'automatico', cor: 'text-lime-300 border-lime-400/40 bg-lime-400/10' },
    ],
    duvidas: ['soClose', 'semAberto', 'closeDividido', 'outroVideo', 'trechosCurtos', 'legenda'],
  },
];

export function GuideTab({ secao }) {
  const { t } = useI18n();
  const refs = useRef({});

  // Aberta por um botão "?" de um recurso: rola até a seção dele.
  useEffect(() => {
    if (secao?.id) refs.current[secao.id]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [secao]);

  return (
    <div className="bg-[#0a0712] border border-[#1b1528] p-6 rounded-2xl shadow-2xl flex flex-col gap-6 text-slate-300">
      <div>
        <h2 className="text-lg font-bold text-slate-100">{t('guia.titulo')}</h2>
        <p className="text-sm text-slate-400 mt-1">{t('guia.subtitulo')}</p>
      </div>

      <nav aria-label={t('guia.indice')} className="flex flex-wrap gap-2">
        {SECOES.map(({ id }) => (
          <button key={id} type="button" onClick={() => refs.current[id]?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            className="rounded-lg border border-[#1f1633] bg-[#0e0a1a] px-3 py-1.5 text-xs font-bold text-slate-300 hover:text-white">
            {t(`guia.${id}.titulo`)}
          </button>
        ))}
      </nav>

      {SECOES.map(({ id, etapas, duvidas }) => (
        <section key={id} ref={elemento => { refs.current[id] = elemento; }} className="scroll-mt-4 flex flex-col gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-100">{t(`guia.${id}.titulo`)}</h3>
            <p className="text-sm text-slate-400 mt-1 leading-relaxed">{t(`guia.${id}.resumo`)}</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] gap-4">
            {/* Vídeo de exemplo: curto, sem som e em loop, gerado pelo próprio app. */}
            <div className="flex aspect-video items-center justify-center rounded-xl border border-dashed border-[#2a2140] bg-[#0e0a1a] p-4 text-center text-xs text-slate-500">
              {t('guia.videoEmBreve')}
            </div>
            <ol className="flex flex-col gap-3">
              {etapas.map(({ chave, cor }) => (
                <li key={chave} className={`rounded-xl border p-3 ${cor}`}>
                  <p className="text-sm font-bold">{t(`guia.${id}.etapas.${chave}.titulo`)}</p>
                  <p className="text-sm text-slate-300 mt-1 leading-relaxed">{t(`guia.${id}.etapas.${chave}.texto`)}</p>
                </li>
              ))}
            </ol>
          </div>

          <div className="flex flex-col gap-2">
            <h4 className="text-sm font-bold text-slate-200">{t('guia.duvidas')}</h4>
            {duvidas.map(chave => (
              <details key={chave} className="rounded-lg border border-[#1f1633] bg-[#0e0a1a]/70 p-3 text-sm">
                <summary className="cursor-pointer font-medium text-slate-200">{t(`guia.${id}.duvidas.${chave}.pergunta`)}</summary>
                <p className="mt-2 text-slate-400 leading-relaxed">{t(`guia.${id}.duvidas.${chave}.resposta`)}</p>
              </details>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
