import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Palette} from '../lib/theme';

/** Flat plate: soft vertical gradient + a subtle dashed texture that drifts slowly (never fully still). */
export const Background: React.FC<{p: Palette; tint?: string; drift?: number}> = ({p, tint, drift = 0.25}) => {
  const f = useCurrentFrame();
  const off = (f * drift) % 48;
  return (
    <AbsoluteFill style={{background: `linear-gradient(180deg, ${tint ?? p.bg2} 0%, ${p.bg} 78%)`}}>
      <svg width="100%" height="100%" style={{position: 'absolute', inset: 0}}>
        <defs>
          <pattern id="dash" width="48" height="48" patternUnits="userSpaceOnUse"
                   patternTransform={`translate(${off} ${off * 0.5}) rotate(-24)`}>
            <line x1="6" y1="24" x2="26" y2="24" stroke={p.texture} strokeWidth="5" strokeLinecap="round" />
          </pattern>
          <radialGradient id="vig" cx="50%" cy="45%" r="75%">
            <stop offset="60%" stopColor="rgba(0,0,0,0)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.35)" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#dash)" />
        <rect width="100%" height="100%" fill="url(#vig)" />
      </svg>
    </AbsoluteFill>
  );
};

/** The floor the props stand on: a soft line + glow. */
export const Floor: React.FC<{p: Palette; y: number}> = ({p, y}) => (
  <div style={{position: 'absolute', left: 0, right: 0, top: y, height: 6, borderRadius: 3,
    background: `linear-gradient(90deg, transparent, ${p.ink}22 20%, ${p.ink}33 50%, ${p.ink}22 80%, transparent)`}} />
);
