import React, { useEffect, useRef, useState } from 'react';
import { apiFetch } from '../../api';
import { useI18n } from '../../i18n/useI18n';

// Verificação de atualização sob demanda: nada é consultado nem instalado sem o clique do usuário.
export function AtualizacaoDialog({ aberto, onFechar }) {
  const { t } = useI18n();
  const dialogo = useRef(null);
  const [info, setInfo] = useState(null);
  const [estado, setEstado] = useState({ fase: 'ocioso' });
  const [erro, setErro] = useState('');
  const [verificando, setVerificando] = useState(false);

  async function verificar() {
    setVerificando(true); setErro(''); setInfo(null);
    try {
      setInfo(await (await apiFetch('/atualizacao/verificar')).json());
      setEstado(await (await apiFetch('/atualizacao/status')).json());
    } catch (e) { setErro(e.message); }
    finally { setVerificando(false); }
  }

  useEffect(() => {
    if (aberto && !dialogo.current.open) { dialogo.current.showModal(); verificar(); }
    if (!aberto && dialogo.current.open) dialogo.current.close();
  }, [aberto]);

  // Acompanha o download enquanto ele roda no backend.
  useEffect(() => {
    if (estado.fase !== 'baixando') return undefined;
    const timer = setInterval(async () => {
      try { setEstado(await (await apiFetch('/atualizacao/status')).json()); }
      catch (e) { setErro(e.message); }
    }, 700);
    return () => clearInterval(timer);
  }, [estado.fase]);

  async function acao(caminho) {
    setErro('');
    try {
      const resposta = await (await apiFetch(caminho, { method: 'POST' })).json();
      if (resposta.fase) setEstado(resposta);
      if (resposta.mensagem) setEstado({ fase: 'instalando', mensagem: resposta.mensagem });
    } catch (e) { setErro(e.message); }
  }

  async function abrirPagina() {
    const url = info?.pagina;
    if (window.pywebview?.api?.abrir_releases) {
      try { await window.pywebview.api.abrir_releases(url || ''); } catch (e) { setErro(e.message); }
    } else window.open(url || 'https://github.com/denishark333/SerialClipPRO-Local-AI/releases', '_blank', 'noopener');
  }

  const pct = estado.total ? Math.min(100, Math.round(estado.baixado / estado.total * 100)) : 0;
  const botao = 'rounded-xl px-5 py-2.5 text-sm font-bold focus-visible:outline-2 focus-visible:outline-cyan-400 disabled:opacity-40';
  const primario = `${botao} bg-purple-600 hover:bg-purple-500 border border-purple-400/60`;
  const secundario = `${botao} border border-purple-500/60 bg-purple-950 hover:bg-purple-900`;

  return (
    <dialog ref={dialogo} onCancel={e => { e.preventDefault(); if (estado.fase !== 'instalando') onFechar(); }}
      aria-labelledby="titulo-atualizacao"
      className="m-auto w-[94vw] max-w-[640px] max-h-[90vh] overflow-y-auto rounded-2xl border border-purple-500 bg-[#0e0a1a] text-white p-5 sm:p-6 shadow-2xl shadow-purple-950/60 backdrop:bg-black/80">
      <div className="flex items-center justify-between gap-3 mb-4 border-b border-purple-800/60 pb-3">
        <h3 id="titulo-atualizacao" className="text-lg font-bold">{t('atualizacao.titulo')}</h3>
        {estado.fase !== 'instalando' && <button onClick={onFechar} className={secundario}>{t('atualizacao.fechar')}</button>}
      </div>

      {verificando && <p role="status" className="text-cyan-300">{t('atualizacao.verificando')}</p>}
      {erro && <p role="alert" className="mb-3 rounded-lg border border-rose-500/40 bg-rose-950/40 p-3 text-sm text-rose-200">{erro}</p>}

      {info && !info.disponivel && estado.fase !== 'instalando' && (
        <p role="status" className="text-lime-300">{t('atualizacao.atualizado', { versao: info.atual })}</p>
      )}

      {info?.disponivel && estado.fase !== 'instalando' && <>
        <p className="text-xl font-bold text-cyan-300">{t('atualizacao.disponivel', { versao: info.ultima })}</p>
        <p className="mb-3 text-xs text-slate-400">{t('atualizacao.instalada', { versao: info.atual })}</p>
        {info.notas && <>
          <p className="text-sm font-semibold text-purple-200">{t('atualizacao.novidades')}</p>
          <div className="mt-1 mb-4 max-h-[38vh] overflow-y-auto whitespace-pre-wrap rounded-lg border border-purple-800/60 bg-[#090612] p-3 text-xs text-slate-200">{info.notas}</div>
        </>}

        {!info.assinada || !info.pode_instalar ? <>
          <p className="mb-3 text-sm text-amber-200">{t(info.pode_instalar ? 'atualizacao.manual' : 'atualizacao.soInstalado')}</p>
          <button onClick={abrirPagina} className={primario}>{t('atualizacao.abrirPagina')}</button>
        </> : estado.fase === 'baixando' ? <>
          <p role="status" className="text-sm text-cyan-300">{t('atualizacao.baixando', { pct })}</p>
          <div className="my-2 h-2 overflow-hidden rounded-full bg-[#1b1528]">
            <div className="h-full bg-gradient-to-r from-[#b3ff33] to-[#00ffcc] transition-all" style={{ width: `${pct}%` }} />
          </div>
          <button onClick={() => acao('/atualizacao/cancelar')} className={secundario}>{t('atualizacao.cancelar')}</button>
        </> : estado.fase === 'pronto' ? <>
          <p className="text-sm text-lime-300">{t('atualizacao.pronta')}</p>
          <p className="my-2 text-xs text-slate-300">{t('atualizacao.dicaInstalar')}</p>
          <button onClick={() => acao('/atualizacao/instalar')} className={primario}>{t('atualizacao.instalarAgora')}</button>
        </> : <>
          {estado.fase === 'erro' && <p role="alert" className="mb-3 text-sm text-rose-200">{estado.erro}</p>}
          <p className="mb-3 text-xs text-slate-300">{t('atualizacao.dicaBaixar', { mb: Math.round((info.tamanho || 0) / 1048576) })}</p>
          <button onClick={() => acao('/atualizacao/baixar')} className={primario}>{t('atualizacao.baixar')}</button>
        </>}
      </>}

      {estado.fase === 'instalando' && <p role="status" className="text-cyan-300">{estado.mensagem || t('atualizacao.instalando')}</p>}

      {!verificando && estado.fase !== 'baixando' && estado.fase !== 'instalando' && (
        <div className="mt-5 border-t border-purple-800/60 pt-3">
          <button onClick={verificar} className="text-xs text-cyan-300 hover:text-cyan-200">{t('atualizacao.verificarDeNovo')}</button>
        </div>
      )}
    </dialog>
  );
}
