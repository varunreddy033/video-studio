import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {clamp, ease, pop} from '../lib/anim';
import {FONT, Palette} from '../lib/theme';

export type HeadWord = {text: string; at: number};   // at = scene-local frame the word is spoken

/** Rounded pill at the top: appears empty, then every word lights up as it is spoken (unspoken words grey). */
export const HeadlinePill: React.FC<{p: Palette; words: HeadWord[]; appear: number; top?: number; size?: number}> = (
  {p, words, appear, top = 74, size = 54}) => {
  const f = useCurrentFrame();
  const s = pop(f, appear, 30, 14, 160);
  const fill = ease(f, appear + 6, 8);                       // words fade in grey after the empty pill
  return (
    <div style={{position: 'absolute', top, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
      <div style={{
        transform: `scale(${0.55 + 0.45 * s})`, opacity: Math.min(1, s * 1.4), padding: `${size * 0.32}px ${size * 0.7}px`,
        borderRadius: 999, background: p.panel, boxShadow: `0 ${size * 0.18}px 0 ${p.shadow}`, display: 'flex',
        gap: size * 0.3, fontFamily: FONT, fontWeight: 900, fontSize: size, letterSpacing: 0.5, lineHeight: 1,
      }}>
        {words.map((w, i) => {
          const lit = interpolate(f, [w.at - 2, w.at + 3], [0, 1], clamp);
          const bump = pop(f, w.at - 1, 30, 9, 260);
          return (
            <span key={i} style={{
              color: lit > 0.5 ? p.onPanel : '#B7BDC8', opacity: fill,
              transform: `translateY(${(1 - Math.min(1, bump)) * 4}px) scale(${1 + 0.12 * Math.sin(Math.min(1, bump) * Math.PI)})`,
              display: 'inline-block',
            }}>{w.text}</span>
          );
        })}
      </div>
    </div>
  );
};
