import React from 'react';
import {useCurrentFrame} from 'remotion';
import {FONT, Palette} from '../lib/theme';

// The prop library: flat, parametric SVG props in our palette (catalog.json lists them with their default sizes).
// Each draws into a 100x100 viewBox (sitting on the bottom edge), has its own small idle motion, and takes the
// element's colour `c`, optional `text`, and the palette. Anything not here falls back to a labelled placeholder.

export const shade = (hex: string, k: number) => {      // k < 0 darker, k > 0 lighter
  if (!hex.startsWith('#') || hex.length !== 7) return hex;
  const n = parseInt(hex.slice(1), 16);
  const ch = (v: number) => Math.max(0, Math.min(255, Math.round(k < 0 ? v * (1 + k) : v + (255 - v) * k)));
  return `rgb(${ch(n >> 16)},${ch((n >> 8) & 255)},${ch(n & 255)})`;
};

type Draw = (o: {p: Palette; c: string; f: number; text: string}) => React.ReactNode;
const T = (x: number, y: number, s: string, size: number, fill: string, w = 900) => (
  <text x={x} y={y} textAnchor="middle" fontFamily={FONT} fontWeight={w} fontSize={size} fill={fill}>{s}</text>
);
const floorShadow = (w = 70) => <ellipse cx={50} cy={98} rx={w / 2} ry={2.6} fill="rgba(0,0,0,0.28)" />;

export const PROPS: Record<string, Draw> = {
  house: ({p, c}) => <>{floorShadow(80)}
    <rect x={18} y={48} width={64} height={50} rx={3} fill={c} />
    <path d="M10 52 L50 18 L90 52 Z" fill={shade(c, -0.35)} strokeLinejoin="round" />
    <rect x={43} y={70} width={14} height={28} rx={2} fill={shade(c, -0.45)} />
    <rect x={25} y={60} width={12} height={11} rx={2} fill={p.ink} opacity={0.85} />
    <rect x={63} y={60} width={12} height={11} rx={2} fill={p.ink} opacity={0.85} /></>,
  bank: ({p, c}) => <>{floorShadow(86)}
    <path d="M8 34 L50 10 L92 34 Z" fill={shade(c, -0.3)} />
    <rect x={10} y={34} width={80} height={6} fill={shade(c, -0.15)} />
    {[18, 34, 50, 66, 82].map((x) => <rect key={x} x={x - 4} y={42} width={8} height={44} rx={2} fill={c} />)}
    <rect x={6} y={86} width={88} height={10} rx={2} fill={shade(c, -0.3)} />
    {T(50, 30, '$', 14, p.ink)}</>,
  factory: ({p, c, f}) => <>{floorShadow(90)}
    {[0, 1, 2].map((i) => <circle key={i} cx={22 + (f / 2 + i * 13) % 40 * 0.15} cy={18 - ((f / 2 + i * 13) % 40) * 0.35}
      r={4 + ((f / 2 + i * 13) % 40) * 0.12} fill={p.ink} opacity={0.35 - ((f / 2 + i * 13) % 40) * 0.008} />)}
    <rect x={16} y={26} width={10} height={40} fill={shade(c, -0.4)} />
    <path d="M10 98 L10 56 L35 44 L35 56 L60 44 L60 56 L90 44 L90 98 Z" fill={c} />
    {[22, 47, 72].map((x) => <rect key={x} x={x} y={66} width={12} height={10} rx={2} fill={p.accent} opacity={0.9} />)}</>,
  skyline: ({c, f}) => <>
    {[[4, 40, 14], [19, 22, 12], [32, 52, 15], [48, 12, 13], [62, 34, 16], [79, 46, 17]].map(([x, y, w], i) => (
      <g key={i}><rect x={x} y={y} width={w} height={100 - y} fill={i % 2 ? shade(c, -0.25) : c} />
        {Array.from({length: Math.floor((100 - y) / 9)}).map((_, r) => [0, 1].map((col) =>
          <rect key={`${r}-${col}`} x={x + 2.5 + col * (w / 2)} y={y + 4 + r * 9} width={w / 2 - 4} height={4}
            fill="#FFE29A" opacity={(Math.sin(f / 23 + i * 7 + r * 3 + col) > 0.3) ? 0.9 : 0.15} />))}</g>))}</>,
  server: ({p, c, f}) => <>{floorShadow(60)}
    <rect x={24} y={4} width={52} height={94} rx={5} fill={shade(c, -0.5)} />
    {[0, 1, 2, 3, 4, 5].map((i) => <g key={i}>
      <rect x={29} y={9 + i * 15} width={42} height={11} rx={2} fill={shade(c, -0.25)} />
      <circle cx={35} cy={14.5 + i * 15} r={2} fill={Math.sin(f / 5 + i * 1.7) > 0 ? p.good : shade(p.good, -0.6)} />
      <circle cx={41} cy={14.5 + i * 15} r={2} fill={Math.sin(f / 7 + i * 2.3) > 0.4 ? p.accent : shade(p.accent, -0.6)} />
      <rect x={50} y={13} width={16} height={3} rx={1} fill={p.ink} opacity={0.25} transform={`translate(0 ${i * 15})`} /></g>)}</>,
  phone: ({p, c, f}) => <>
    <rect x={22} y={2} width={56} height={96} rx={10} fill={shade(c, -0.55)} />
    <rect x={26} y={8} width={48} height={82} rx={6} fill={c} />
    <rect x={32} y={16} width={36} height={6} rx={3} fill={p.ink} opacity={0.7} />
    {[0, 1, 2].map((i) => <rect key={i} x={32} y={30 + i * 14} width={36 * (0.6 + 0.4 * ((Math.sin(f / 20 + i) + 1) / 2))} height={8} rx={3}
      fill={p.ink} opacity={0.35} />)}
    <circle cx={50} cy={94} r={2} fill={p.ink} opacity={0.5} /></>,
  laptop: ({p, c, f}) => <>{floorShadow(96)}
    <rect x={14} y={14} width={72} height={52} rx={4} fill={shade(c, -0.55)} />
    <rect x={18} y={18} width={64} height={44} rx={2} fill={c} />
    <polyline points={Array.from({length: 9}).map((_, i) => `${22 + i * 7},${50 - Math.sin(f / 15 + i) * 6 - i * 2}`).join(' ')}
      fill="none" stroke={p.ink} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" opacity={0.85} />
    <path d="M4 70 L96 70 L90 82 L10 82 Z" fill={shade(c, -0.3)} /></>,
  chip: ({p, c, f}) => <>
    {[0, 1, 2, 3, 4].map((i) => <g key={i}>
      <rect x={24 + i * 11} y={6} width={5} height={14} rx={1} fill={p.muted.replace('0.32', '0.8')} />
      <rect x={24 + i * 11} y={80} width={5} height={14} rx={1} fill={p.muted.replace('0.32', '0.8')} />
      <rect x={6} y={24 + i * 11} width={14} height={5} rx={1} fill={p.muted.replace('0.32', '0.8')} />
      <rect x={80} y={24 + i * 11} width={14} height={5} rx={1} fill={p.muted.replace('0.32', '0.8')} /></g>)}
    <rect x={18} y={18} width={64} height={64} rx={8} fill={shade(c, -0.45)} />
    <rect x={28} y={28} width={44} height={44} rx={5} fill={c} opacity={0.7 + 0.3 * Math.sin(f / 12)} />
    {T(50, 57, 'AI', 18, p.ink)}</>,
  battery: ({p, c, f}) => {
    const lvl = 0.25 + 0.65 * ((Math.sin(f / 30) + 1) / 2);
    return <><rect x={40} y={2} width={20} height={8} rx={2} fill={shade(c, -0.4)} />
      <rect x={24} y={9} width={52} height={89} rx={8} fill="none" stroke={shade(c, -0.4)} strokeWidth={6} />
      <rect x={31} y={16 + 75 * (1 - lvl)} width={38} height={75 * lvl} rx={4} fill={lvl < 0.4 ? p.bad : p.good} /></>;
  },
  gear: ({c, f}) => <g transform={`rotate(${f * 1.2} 50 50)`}>
    {Array.from({length: 8}).map((_, i) => <rect key={i} x={44} y={4} width={12} height={20} rx={3} fill={c}
      transform={`rotate(${i * 45} 50 50)`} />)}
    <circle cx={50} cy={50} r={32} fill={c} /><circle cx={50} cy={50} r={13} fill={shade(c, -0.45)} /></g>,
  rocket: ({p, c, f}) => <>
    <path d={`M42 80 Q50 ${96 + Math.sin(f / 2) * 4} 58 80 Z`} fill={p.accent} />
    <path d={`M46 80 Q50 ${90 + Math.sin(f / 2.5) * 3} 54 80 Z`} fill="#FFF1C9" />
    <path d="M50 4 C66 20 66 52 62 80 L38 80 C34 52 34 20 50 4 Z" fill={c} />
    <circle cx={50} cy={38} r={8} fill={p.sky} stroke={shade(c, -0.4)} strokeWidth={3} />
    <path d="M38 58 L24 78 L38 76 Z" fill={shade(c, -0.35)} /><path d="M62 58 L76 78 L62 76 Z" fill={shade(c, -0.35)} /></>,
  lightbulb: ({p, f}) => {
    const g = 0.55 + 0.45 * ((Math.sin(f / 10) + 1) / 2);
    return <><circle cx={50} cy={36} r={34} fill={p.accent} opacity={0.18 * g} />
      <circle cx={50} cy={36} r={24} fill={p.accent} opacity={0.6 + 0.4 * g} />
      <path d="M38 52 L62 52 L58 70 L42 70 Z" fill={p.accent} opacity={0.6 + 0.4 * g} />
      <rect x={40} y={70} width={20} height={8} rx={2} fill="#B8BFCC" /><rect x={42} y={79} width={16} height={7} rx={2} fill="#9AA2B1" />
      <path d="M44 40 Q50 30 56 40" fill="none" stroke="#fff" strokeWidth={3} strokeLinecap="round" opacity={0.8} /></>;
  },
  magnifier: ({p, c, f}) => <g transform={`rotate(${Math.sin(f / 25) * 6} 50 50)`}>
    <rect x={56} y={56} width={14} height={40} rx={6} fill={shade(c, -0.4)} transform="rotate(-45 63 76)" />
    <circle cx={42} cy={42} r={30} fill={p.sky} opacity={0.3} stroke={c} strokeWidth={9} />
    <path d="M28 34 Q34 24 46 24" fill="none" stroke="#fff" strokeWidth={4} strokeLinecap="round" opacity={0.7} /></g>,
  target: ({p, c, f}) => <>
    {[44, 32, 20, 8].map((r, i) => <circle key={r} cx={50} cy={50} r={r} fill={i % 2 ? p.panel : c} />)}
    <g transform={`translate(${(1 - Math.min(1, f / 18)) * 40} ${-(1 - Math.min(1, f / 18)) * 40})`}>
      <line x1={50} y1={50} x2={86} y2={14} stroke={shade(c, -0.5)} strokeWidth={4} strokeLinecap="round" />
      <path d="M86 14 L80 6 M86 14 L94 20" stroke={p.accent} strokeWidth={4} strokeLinecap="round" /></g></>,
  cloud: ({p, f}) => <g transform={`translate(${Math.sin(f / 40) * 3} 0)`}>
    <path d="M22 78 C6 78 6 56 22 56 C22 38 46 34 52 48 C58 34 84 38 80 58 C96 58 96 78 80 78 Z" fill={p.panel} />
    <path d="M22 78 L80 78 C90 78 94 72 94 68 C88 74 30 74 14 70 C14 75 17 78 22 78 Z" fill="#D7DCE6" /></g>,
  cash: ({p, c}) => <>{floorShadow(90)}
    {[0, 1, 2, 3, 4].map((i) => <g key={i} transform={`translate(${(i % 2) * 3} ${-i * 9})`}>
      <rect x={10} y={72} width={78} height={22} rx={3} fill={i === 4 ? c : shade(c, -0.2 + i * 0.04)} />
      <circle cx={49} cy={83} r={6} fill={shade(c, -0.35)} /><rect x={14} y={75} width={70} height={16} rx={2} fill="none" stroke={shade(c, -0.3)} strokeWidth={1.5} /></g>)}
    {T(52, 47, '$', 12, p.bg)}</>,
  piggy: ({p, c, f}) => <>{floorShadow(76)}
    <ellipse cx={50} cy={62} rx={36} ry={28} fill={c} />
    <circle cx={83} cy={58} r={8} fill={shade(c, -0.15)} /><circle cx={84} cy={57} r={1.6} fill={shade(c, -0.5)} />
    <circle cx={68} cy={48} r={2.6} fill={p.onPanel} /><path d="M38 34 L44 22 L50 34 Z" fill={shade(c, -0.2)} />
    <rect x={40} y={34} width={18} height={4} rx={2} fill={shade(c, -0.5)} />
    {[24, 40, 58, 72].map((x) => <rect key={x} x={x} y={84} width={9} height={12} rx={3} fill={shade(c, -0.2)} />)}
    <circle cx={49} cy={30 - ((f % 45) / 45) * 18} r={5} fill={p.accent} opacity={1 - (f % 45) / 45} /></>,
  wallet: ({p, c}) => <>
    <rect x={8} y={20} width={84} height={68} rx={10} fill={shade(c, -0.25)} />
    <rect x={14} y={12} width={60} height={20} rx={4} fill="#7FD18B" />
    <rect x={8} y={28} width={84} height={60} rx={10} fill={c} />
    <rect x={62} y={46} width={30} height={22} rx={6} fill={shade(c, -0.35)} /><circle cx={72} cy={57} r={4} fill={p.accent} /></>,
  creditcard: ({p, c}) => <>
    <rect x={4} y={18} width={92} height={62} rx={8} fill={c} />
    <rect x={4} y={30} width={92} height={10} fill={shade(c, -0.45)} />
    <rect x={12} y={50} width={16} height={12} rx={2} fill={p.accent} />
    {[0, 1, 2, 3].map((i) => <rect key={i} x={36 + i * 14} y={66} width={10} height={4} rx={2} fill={p.ink} opacity={0.7} />)}</>,
  jar: ({p, c, f}) => <>{floorShadow(60)}
    <rect x={26} y={14} width={48} height={10} rx={3} fill={shade(c, -0.4)} />
    <path d="M24 26 L76 26 C84 34 84 90 74 96 L26 96 C16 90 16 34 24 26 Z" fill={p.sky} opacity={0.35} stroke={p.panel} strokeOpacity={0.6} strokeWidth={2} />
    {[0, 1, 2, 3, 4, 5].map((i) => <ellipse key={i} cx={36 + (i % 3) * 14} cy={88 - Math.floor(i / 3) * 9} rx={8} ry={4} fill={p.accent} />)}
    <path d="M30 34 L30 80" stroke="#fff" strokeWidth={3} strokeLinecap="round" opacity={0.4 + 0.2 * Math.sin(f / 20)} /></>,
  briefcase: ({c}) => <>{floorShadow(84)}
    <rect x={36} y={16} width={28} height={16} rx={5} fill="none" stroke={shade(c, -0.4)} strokeWidth={6} />
    <rect x={8} y={28} width={84} height={66} rx={8} fill={c} />
    <rect x={8} y={50} width={84} height={6} fill={shade(c, -0.3)} /><rect x={44} y={46} width={12} height={14} rx={2} fill={shade(c, -0.45)} /></>,
  scale: ({p, c, f}) => {
    const tilt = Math.sin(f / 35) * 8;
    return <>{floorShadow(60)}
      <rect x={47} y={20} width={6} height={70} fill={shade(c, -0.3)} /><rect x={30} y={90} width={40} height={6} rx={3} fill={shade(c, -0.3)} />
      <g transform={`rotate(${tilt} 50 22)`}>
        <rect x={10} y={19} width={80} height={5} rx={2} fill={c} />
        <path d={`M14 24 L6 ${50} L30 50 L22 24`} fill="none" stroke={p.ink} strokeOpacity={0.5} strokeWidth={1.5} />
        <path d={`M78 24 L70 50 L94 50 L86 24`} fill="none" stroke={p.ink} strokeOpacity={0.5} strokeWidth={1.5} />
        <path d="M4 50 L32 50 Q18 60 4 50 Z" fill={c} /><path d="M68 50 L96 50 Q82 60 68 50 Z" fill={c} /></g>
      <circle cx={50} cy={22} r={5} fill={p.accent} /></>;
  },
  envelope: ({p, c, f}) => {
    const open = Math.max(0, Math.sin(f / 40));
    return <><rect x={6} y={24} width={88} height={60} rx={6} fill={p.panel} />
      <path d="M6 30 L50 60 L94 30" fill="none" stroke="#C9CFDA" strokeWidth={3} />
      <path d={`M6 26 L50 ${26 + 32 * (1 - 2 * open)} L94 26 Z`} fill={c} />
      <circle cx={50} cy={52} r={7} fill={p.bad} /></>;
  },
  clock: ({p, c, f}) => <>
    <circle cx={50} cy={50} r={44} fill={c} /><circle cx={50} cy={50} r={36} fill={p.panel} />
    {Array.from({length: 12}).map((_, i) => <rect key={i} x={49} y={17} width={2} height={6} fill={p.onPanel} transform={`rotate(${i * 30} 50 50)`} />)}
    <line x1={50} y1={50} x2={50} y2={30} stroke={p.onPanel} strokeWidth={4} strokeLinecap="round" transform={`rotate(${f * 0.5} 50 50)`} />
    <line x1={50} y1={50} x2={50} y2={22} stroke={p.bad} strokeWidth={2.5} strokeLinecap="round" transform={`rotate(${f * 6} 50 50)`} />
    <circle cx={50} cy={50} r={4} fill={p.onPanel} /></>,
  hourglass: ({p, c, f}) => {
    const t = (f % 150) / 150;
    return <><rect x={18} y={4} width={64} height={8} rx={3} fill={shade(c, -0.3)} /><rect x={18} y={88} width={64} height={8} rx={3} fill={shade(c, -0.3)} />
      <path d="M26 12 L74 12 Q72 36 52 50 Q72 64 74 88 L26 88 Q28 64 48 50 Q28 36 26 12 Z" fill={p.sky} opacity={0.3} />
      <path d={`M${32 + t * 14} ${16 + t * 26} L${68 - t * 14} ${16 + t * 26} Q60 40 50 48 Q40 40 ${32 + t * 14} ${16 + t * 26} Z`} fill={p.accent} />
      <path d={`M30 86 L70 86 Q62 ${86 - t * 26} 50 ${86 - t * 30} Q38 ${86 - t * 26} 30 86 Z`} fill={p.accent} />
      <line x1={50} y1={50} x2={50} y2={84} stroke={p.accent} strokeWidth={1.5} /></>;
  },
  shield: ({p, c}) => <>
    <path d="M50 4 L88 18 C88 56 74 82 50 96 C26 82 12 56 12 18 Z" fill={c} />
    <path d="M50 4 L88 18 C88 56 74 82 50 96 Z" fill={shade(c, -0.2)} />
    <path d="M34 50 L46 62 L68 38" fill="none" stroke={p.ink} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" /></>,
  lock: ({p, c}) => <>
    <path d="M30 44 L30 30 C30 4 70 4 70 30 L70 44" fill="none" stroke={shade(c, -0.25)} strokeWidth={9} />
    <rect x={18} y={42} width={64} height={54} rx={9} fill={c} />
    <circle cx={50} cy={64} r={7} fill={shade(c, -0.5)} /><rect x={47} y={66} width={6} height={14} rx={2} fill={shade(c, -0.5)} /></>,
  crown: ({p, c, f}) => <>
    <path d="M8 80 L14 28 L34 52 L50 18 L66 52 L86 28 L92 80 Z" fill={p.accent} />
    <rect x={8} y={78} width={84} height={14} rx={3} fill={shade(p.accent, -0.25)} />
    {[[14, 28], [50, 18], [86, 28]].map(([x, y]) => <circle key={x} cx={x} cy={y} r={5} fill={c} />)}
    <circle cx={50} cy={62} r={6} fill={p.bad} opacity={0.6 + 0.4 * Math.sin(f / 8)} /></>,
  trophy: ({p, f}) => <>{floorShadow(50)}
    <path d="M28 10 L72 10 L70 40 C68 54 58 60 50 60 C42 60 32 54 30 40 Z" fill={p.accent} />
    <path d="M28 16 C10 16 12 40 30 40 M72 16 C90 16 88 40 70 40" fill="none" stroke={shade(p.accent, -0.2)} strokeWidth={6} />
    <rect x={45} y={60} width={10} height={18} fill={shade(p.accent, -0.25)} /><rect x={30} y={78} width={40} height={16} rx={3} fill={shade(p.accent, -0.35)} />
    <path d="M40 22 L44 34" stroke="#fff" strokeWidth={4} strokeLinecap="round" opacity={0.4 + 0.4 * Math.sin(f / 12)} /></>,
  globe: ({p, c, f}) => <>
    <circle cx={50} cy={50} r={42} fill={p.sky} />
    <clipPath id="gl"><circle cx={50} cy={50} r={42} /></clipPath>
    <g clipPath="url(#gl)"><g transform={`translate(${-((f * 0.4) % 60)} 0)`}>
      {[0, 60].map((o) => <g key={o} transform={`translate(${o} 0)`}>
        <path d="M14 30 C24 20 40 24 42 36 C44 48 30 50 26 62 C22 70 10 64 10 52 Z" fill={c} />
        <path d="M54 22 C66 18 80 26 76 40 C72 50 60 46 58 58 C56 70 66 80 58 86 C48 80 50 66 46 56 C42 44 46 28 54 22 Z" fill={c} /></g>)}
    </g></g>
    <circle cx={50} cy={50} r={42} fill="none" stroke={shade(p.sky, -0.35)} strokeWidth={3} /></>,
  flag: ({p, c, f}) => <>{floorShadow(30)}
    <rect x={20} y={6} width={5} height={92} rx={2} fill="#B8BFCC" />
    <path d={`M25 10 Q45 ${4 + Math.sin(f / 9) * 4} 62 10 T 92 10 L92 46 Q75 ${40 + Math.sin(f / 9 + 1) * 4} 62 46 T 25 46 Z`} fill={c} /></>,
  megaphone: ({p, c, f}) => <>
    <path d="M18 40 L60 18 L60 82 L18 60 Z" fill={c} /><rect x={8} y={38} width={14} height={24} rx={4} fill={shade(c, -0.35)} />
    <rect x={26} y={60} width={10} height={20} rx={3} fill={shade(c, -0.35)} />
    {[0, 1, 2].map((i) => <path key={i} d={`M${68 + i * 9} 34 Q${76 + i * 9} 50 ${68 + i * 9} 66`} fill="none" stroke={p.accent}
      strokeWidth={4} strokeLinecap="round" opacity={(Math.sin(f / 6 - i) + 1) / 2} />)}</>,
  arrow_up: ({p, f}) => <g transform={`translate(0 ${-Math.abs(Math.sin(f / 12)) * 6})`}>
    <path d="M50 4 L90 46 L66 46 L66 96 L34 96 L34 46 L10 46 Z" fill={p.good} /></g>,
  arrow_down: ({p, f}) => <g transform={`translate(0 ${Math.abs(Math.sin(f / 12)) * 6})`}>
    <path d="M50 96 L90 54 L66 54 L66 4 L34 4 L34 54 L10 54 Z" fill={p.bad} /></g>,
  check: ({p}) => <><circle cx={50} cy={50} r={44} fill={p.good} />
    <path d="M28 52 L44 68 L74 36" fill="none" stroke="#fff" strokeWidth={10} strokeLinecap="round" strokeLinejoin="round" /></>,
  cross: ({p}) => <><circle cx={50} cy={50} r={44} fill={p.bad} />
    <path d="M32 32 L68 68 M68 32 L32 68" stroke="#fff" strokeWidth={10} strokeLinecap="round" /></>,
  warning: ({p, f}) => <>
    <path d="M50 6 L96 90 L4 90 Z" fill={p.accent} strokeLinejoin="round" opacity={0.85 + 0.15 * Math.sin(f / 5)} />
    <rect x={45} y={34} width={10} height={32} rx={4} fill={p.onPanel} /><circle cx={50} cy={76} r={6} fill={p.onPanel} /></>,
  earphones: ({f}) => {
    const sw = Math.sin(f / 28) * 2.2;                       // the cable sways a little
    const bud = (x: number, flip: number) => <g transform={`translate(${x} 0) scale(${flip} 1)`}>
      <rect x={-4} y={22} width={8} height={30} rx={4} fill="#E3E7EE" />
      <ellipse cx={-3} cy={19} rx={14} ry={13} fill="#FFFFFF" />
      <ellipse cx={-3} cy={19} rx={14} ry={13} fill="none" stroke="#C4CBD8" strokeWidth={1.6} />
      <ellipse cx={-9} cy={18} rx={4.5} ry={6.5} fill="#8E98AB" />
      <path d="M2 10 Q8 14 8 22" fill="none" stroke="#fff" strokeWidth={2} strokeLinecap="round" opacity={0.9} /></g>;
    const cable = (d: string) => <><path d={d} fill="none" stroke="#C4CBD8" strokeWidth={4.4} strokeLinecap="round" />
      <path d={d} fill="none" stroke="#FFFFFF" strokeWidth={2.8} strokeLinecap="round" /></>;
    return <>
      {cable(`M27 50 C27 70 ${46 + sw} 62 ${50 + sw} 78`)}
      {cable(`M73 50 C73 70 ${54 + sw} 62 ${50 + sw} 78`)}
      {cable(`M${50 + sw} 78 C${50 + sw} 88 ${50 - sw} 90 50 99`)}
      <rect x={69.5} y={52} width={7} height={15} rx={3.5} fill="#FFFFFF" stroke="#C4CBD8" strokeWidth={1.4} />
      <rect x={45.5 + sw} y={75} width={9} height={7} rx={3} fill="#E3E7EE" stroke="#C4CBD8" strokeWidth={1.2} />
      {bud(27, 1)}{bud(73, -1)}</>;
  },
  earbuds: ({p, f}) => {
    const lift = 2 + 1.5 * Math.sin(f / 22);                 // the two buds hover in the open case
    return <>
      {[38, 62].map((x, i) => <g key={x} transform={`translate(0 ${-lift * (i ? 1 : 0.6)})`}>
        <rect x={x - 3.5} y={24} width={7} height={26} rx={3.5} fill="#E3E7EE" />
        <ellipse cx={x} cy={22} rx={9.5} ry={9} fill="#FFFFFF" stroke="#C4CBD8" strokeWidth={1.5} />
        <ellipse cx={x + (i ? 3 : -3)} cy={22} rx={3} ry={4.5} fill="#8E98AB" /></g>)}
      <rect x={20} y={42} width={60} height={56} rx={17} fill="#FFFFFF" stroke="#C4CBD8" strokeWidth={1.8} />
      <path d="M21 58 L79 58" stroke="#C4CBD8" strokeWidth={1.6} />
      <path d="M28 50 Q32 46 40 46" fill="none" stroke="#fff" strokeWidth={2} strokeLinecap="round" />
      <circle cx={50} cy={68} r={2.4} fill={Math.sin(f / 9) > 0.2 ? p.good : '#B9E8E2'} />
      <rect x={44} y={90} width={12} height={2.4} rx={1.2} fill="#D5DAE3" /></>;
  },
};

// where each drawing actually sits inside its 100x100 canvas (minX, minY, maxX, maxY): the viewBox is cropped to
// this, so a tall prop fills a tall box and a wide prop a wide one
const BOUNDS: Record<string, [number, number, number, number]> = {
  house: [8, 16, 92, 100], bank: [5, 8, 95, 98], factory: [8, 4, 92, 100], skyline: [3, 10, 97, 100],
  server: [22, 3, 78, 100], phone: [21, 1, 79, 99], laptop: [3, 12, 97, 84], chip: [5, 5, 95, 95],
  battery: [20, 1, 80, 99], gear: [3, 3, 97, 97], rocket: [22, 3, 78, 100], lightbulb: [15, 1, 85, 88],
  magnifier: [5, 5, 95, 97], target: [5, 3, 97, 95], cloud: [5, 32, 95, 81], cash: [9, 34, 94, 100],
  piggy: [11, 12, 95, 100], wallet: [7, 10, 93, 90], creditcard: [3, 16, 97, 82], jar: [14, 12, 86, 100],
  briefcase: [7, 10, 93, 100], scale: [3, 12, 97, 100], envelope: [5, 18, 95, 86], clock: [5, 5, 95, 95],
  hourglass: [17, 3, 83, 97], shield: [11, 3, 89, 97], lock: [16, 3, 84, 97], crown: [7, 12, 93, 93],
  trophy: [9, 8, 91, 100], globe: [7, 7, 93, 93], flag: [17, 3, 95, 100], megaphone: [7, 16, 97, 84],
  arrow_up: [9, -2, 91, 97], arrow_down: [9, 3, 91, 102], check: [5, 5, 95, 95], cross: [5, 5, 95, 95],
  warning: [3, 4, 97, 92], earphones: [9, 4, 91, 100], earbuds: [18, 9, 82, 99],
};

/** Draw a library prop inside a box of w x h px. Returns null for kinds that aren't in PROPS. */
export const LibraryProp: React.FC<{kind: string; w: number; h: number; p: Palette; c: string; text?: string}> = (
  {kind, w, h, p, c, text = ''}) => {
  const f = useCurrentFrame();
  const draw = PROPS[kind];
  if (!draw) return null;
  return (
    <div style={{width: w, height: h, position: 'relative'}}>
      <svg width={w} height={h} viewBox={(() => { const [a, b, c2, d] = BOUNDS[kind] ?? [0, 0, 100, 100];
        return `${a} ${b} ${c2 - a} ${d - b}`; })()} preserveAspectRatio="xMidYMax meet" style={{overflow: 'visible'}}>
        {draw({p, c, f, text})}
      </svg>
      {text ? <div style={{position: 'absolute', left: 0, right: 0, bottom: -Math.max(34, h * 0.14), textAlign: 'center',
        fontFamily: FONT, fontWeight: 800, fontSize: Math.max(22, Math.min(40, w / 7)), color: p.ink,
        textShadow: '0 3px 0 rgba(0,0,0,0.35)'}}>{text}</div> : null}
    </div>
  );
};
