import React from 'react';
import {useCurrentFrame} from 'remotion';
import {FONT, Palette} from '../lib/theme';
import {Word} from './types';

/** Word-by-word captions drawn in the picture (the classic look: short phrases, the spoken word in amber).
 *  Used until a scene has a headline pill (phase 3 makes headlines the default). Absolute frames. */
const groups = (words: Word[]) => {
  const out: Word[][] = [];
  let cur: Word[] = [];
  words.forEach((w, i) => {
    const prev = cur[cur.length - 1];
    const chars = cur.reduce((n, x) => n + x.w.length + 1, 0) + w.w.length;
    if (prev && (cur.length >= 6 || chars > 34 || w.s - prev.e > 0.45 || w.seg !== prev.seg || /[.?!:;]$/.test(prev.w))) {
      out.push(cur); cur = [];
    }
    cur.push(w);
  });
  if (cur.length) out.push(cur);
  return out;
};

export const Captions: React.FC<{p: Palette; words: Word[]; fps: number}> = ({p, words, fps}) => {
  const f = useCurrentFrame();
  const gs = React.useMemo(() => groups(words), [words]);
  const t = f / fps;
  const gi = gs.findIndex((g, i) => t >= g[0].s - 0.02 && t < Math.min(g[g.length - 1].e + 0.35, gs[i + 1]?.[0].s ?? 1e9));
  if (gi < 0) return null;
  const g = gs[gi];
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 80, display: 'flex', justifyContent: 'center', zIndex: 50}}>
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 64, color: '#fff', letterSpacing: 0.5,
        textShadow: '0 4px 0 rgba(0,0,0,0.55), 0 0 18px rgba(0,0,0,0.45)', WebkitTextStroke: '2px rgba(0,0,0,0.35)'}}>
        {g.map((w, i) => {
          const on = t >= w.s && (i + 1 >= g.length || t < g[i + 1].s);
          return <span key={i} style={{color: on ? p.accent : '#fff', marginRight: 16}}>{w.w}</span>;
        })}
      </div>
    </div>
  );
};
