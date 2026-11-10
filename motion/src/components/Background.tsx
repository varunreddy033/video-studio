import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from 'remotion';
import {Palette} from '../lib/theme';

/** A generated flat set plate behind the scene: slow drift, dimmed toward the palette so props stay readable. */
export const Plate: React.FC<{p: Palette; src: string}> = ({p, src}) => {
  const f = useCurrentFrame();
  const z = 1.04 + 0.03 * Math.sin(f / 240);
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover',
        filter: 'blur(2.5px) saturate(0.8)', transform: `scale(${z}) translateX(${Math.sin(f / 300) * 1.2}%)`}} />
      <AbsoluteFill style={{background: `linear-gradient(180deg, ${p.bg}C4 0%, ${p.bg}94 42%, ${p.bg}D0 100%)`}} />
    </AbsoluteFill>
  );
};

/** Flat plate: soft vertical gradient + a subtle dashed texture that drifts slowly (never fully still). */
export const Background: React.FC<{p: Palette; tint?: string; drift?: number; plate?: string}> = ({p, tint, drift = 0.25, plate}) => {
  const f = useCurrentFrame();
  const off = (f * drift) % 48;
  if (plate) return <Plate p={p} src={plate} />;
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
