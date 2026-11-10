import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {bob, clamp, ease, pop} from '../lib/anim';
import {FONT, Palette} from '../lib/theme';

const shade = (hex: string, k: number) => {      // k < 0 darker, k > 0 lighter
  const n = parseInt(hex.slice(1), 16);
  const ch = (v: number) => Math.max(0, Math.min(255, Math.round(k < 0 ? v * (1 + k) : v + (255 - v) * k)));
  return `rgb(${ch(n >> 16)},${ch((n >> 8) & 255)},${ch(n & 255)})`;
};

/** A flat door that grows up from the floor at `at`, then sways gently. (x, bottom) = bottom centre. */
export const Door: React.FC<{p: Palette; x: number; bottom: number; at: number; color: string; w?: number; h?: number;
  phase?: number; open?: number}> = ({p, x, bottom, at, color, w = 230, h = 410, phase = 0, open = 0}) => {
  const f = useCurrentFrame();
  const g = pop(f, at, 30, 12, 140);
  const sway = Math.sin((f + phase) / 55) * 0.8 * Math.min(1, g);
  const glint = (Math.sin((f + phase * 3) / 23) + 1) / 2;
  return (
    <div style={{position: 'absolute', left: x - w / 2, top: bottom - h, width: w, height: h,
      transform: `scaleY(${g}) rotate(${sway}deg)`, transformOrigin: '50% 100%'}}>
      <div style={{position: 'absolute', left: -w * 0.08, right: -w * 0.08, bottom: -10, height: 22, borderRadius: '50%',
        background: p.shadow, opacity: 0.7 * Math.min(1, g)}} />
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
        <rect x={0} y={0} width={w} height={h} rx={w * 0.5} ry={w * 0.5} fill={shade(color, -0.35)} />
        <rect x={0} y={w * 0.5} width={w} height={h - w * 0.5} fill={shade(color, -0.35)} />
        <g style={{transform: `perspective(600px) rotateY(${-open * 65}deg)`, transformOrigin: `14px 50%`}}>
          <rect x={14} y={14} width={w - 28} height={h - 14} rx={(w - 28) * 0.5} fill={color} />
          <rect x={14} y={14 + (w - 28) * 0.5} width={w - 28} height={h - 14 - (w - 28) * 0.5} fill={color} />
          <rect x={40} y={h * 0.34} width={w - 80} height={h * 0.22} rx={12} fill={shade(color, -0.12)} />
          <rect x={40} y={h * 0.62} width={w - 80} height={h * 0.28} rx={12} fill={shade(color, -0.12)} />
          <circle cx={w - 46} cy={h * 0.6} r={11} fill={p.ink} />
          <circle cx={w - 49} cy={h * 0.6 - 3} r={4} fill="#fff" opacity={0.4 + 0.6 * glint} />
        </g>
      </svg>
    </div>
  );
};

/** Line chart that draws itself between `from` and `to` (scene frames); end dot pulses. Box = (x, y, w, h). */
export const LineChart: React.FC<{p: Palette; x: number; y: number; w: number; h: number; values: number[]; from: number;
  to: number; color: string; endColor?: string; appear?: number}> = ({p, x, y, w, h, values, from, to, color, endColor, appear = 0}) => {
  const f = useCurrentFrame();
  const a = pop(f, appear, 30, 14, 150);
  const lo = Math.min(...values), hi = Math.max(...values);
  const pts = values.map((v, i) => [40 + (i / (values.length - 1)) * (w - 80), 30 + (1 - (v - lo) / (hi - lo)) * (h - 70)]);
  const d = pts.map(([px, py], i) => `${i ? 'L' : 'M'}${px.toFixed(1)},${py.toFixed(1)}`).join(' ');
  let len = 0;
  for (let i = 1; i < pts.length; i++) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  const t = interpolate(f, [from, to], [0, 1], clamp);
  // head position along the polyline
  let remain = t * len, hx = pts[0][0], hy = pts[0][1];
  for (let i = 1; i < pts.length; i++) {
    const seg = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    if (remain <= seg) { const k = remain / seg; hx = pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k; hy = pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k; break; }
    remain -= seg; hx = pts[i][0]; hy = pts[i][1];
  }
  const pulse = 1 + 0.35 * Math.max(0, Math.sin(f / 6)) * (t >= 1 ? 1 : 0);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, transform: `scale(${0.85 + 0.15 * a})`, opacity: Math.min(1, a * 1.5)}}>
      <div style={{position: 'absolute', inset: 0, borderRadius: 28, background: p.bg2, boxShadow: `0 14px 0 ${p.shadow}`}} />
      <svg width={w} height={h} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
        {[0.25, 0.5, 0.75].map((k) => (
          <line key={k} x1={40} x2={w - 40} y1={30 + k * (h - 70)} y2={30 + k * (h - 70)} stroke={p.ink} strokeOpacity={0.08}
                strokeWidth={3} strokeDasharray="10 14" />
        ))}
        <path d={d} fill="none" stroke={color} strokeWidth={12} strokeLinecap="round" strokeLinejoin="round"
              strokeDasharray={len} strokeDashoffset={len * (1 - t)} />
        {t > 0 && <circle cx={hx} cy={hy} r={16 * (t >= 1 ? pulse : 1)} fill={t >= 1 ? (endColor ?? color) : color} />}
      </svg>
    </div>
  );
};

/** A number that counts from 0 to `value` between `from` and `to`. */
export const BigNumber: React.FC<{x: number; y: number; value: number; from: number; to: number; decimals?: number;
  prefix?: string; suffix?: string; color: string; size?: number; appear?: number}> = (
  {x, y, value, from, to, decimals = 1, prefix = '', suffix = '', color, size = 170, appear}) => {
  const f = useCurrentFrame();
  const s = pop(f, appear ?? from - 4, 30, 10, 200);
  const v = value * ease(f, from, Math.max(1, to - from));
  const sign = v < 0 ? '−' : '';
  return (
    <div style={{position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) scale(${s})`, fontFamily: FONT,
      fontWeight: 900, fontSize: size, color, letterSpacing: -2, textShadow: `0 10px 0 rgba(0,0,0,0.3)`, whiteSpace: 'nowrap'}}>
      {sign}{prefix}{Math.abs(v).toFixed(decimals)}{suffix}
    </div>
  );
};

/** A tear-off calendar page that flips down into place at `at`. */
export const CalendarPage: React.FC<{p: Palette; x: number; y: number; month: string; day: string; weekday: string;
  at: number; w?: number}> = ({p, x, y, month, day, weekday, at, w = 300}) => {
  const f = useCurrentFrame();
  const s = pop(f, at, 30, 13, 150);
  const flip = interpolate(s, [0, 1], [-95, 0]);
  const fy = bob(f, 20, 5, 80);
  return (
    <div style={{position: 'absolute', left: x, top: y + fy, width: w, transform: `perspective(900px) rotateX(${flip}deg)`,
      transformOrigin: '50% 0%', opacity: Math.min(1, s * 2), fontFamily: FONT}}>
      <div style={{background: p.bad, color: '#fff', fontWeight: 900, fontSize: w * 0.16, textAlign: 'center',
        padding: `${w * 0.05}px 0`, borderRadius: `${w * 0.08}px ${w * 0.08}px 0 0`, letterSpacing: 4}}>{month}</div>
      <div style={{background: p.panel, borderRadius: `0 0 ${w * 0.08}px ${w * 0.08}px`, textAlign: 'center',
        padding: `${w * 0.02}px 0 ${w * 0.07}px`, boxShadow: `0 14px 0 ${p.shadow}`}}>
        <div style={{color: p.onPanel, fontWeight: 900, fontSize: w * 0.5, lineHeight: 1.05}}>{day}</div>
        <div style={{color: '#6B7385', fontWeight: 800, fontSize: w * 0.11, letterSpacing: 3}}>{weekday}</div>
      </div>
      {[0.25, 0.5, 0.75].map((k) => (
        <div key={k} style={{position: 'absolute', top: -w * 0.05, left: `${k * 100}%`, width: w * 0.05, height: w * 0.12,
          marginLeft: -w * 0.025, borderRadius: 99, background: '#2B3A55'}} />
      ))}
    </div>
  );
};

/** Speech-style bubble with a "?" (or any short text) that pops over something. */
export const QuestionBubble: React.FC<{p: Palette; x: number; y: number; at: number; text?: string; size?: number; phase?: number}> = (
  {p, x, y, at, text = '?', size = 110, phase = 0}) => {
  const f = useCurrentFrame();
  const s = pop(f, at, 30, 8, 240);
  const fy = bob(f, phase, 7, 50);
  const tilt = Math.sin((f + phase) / 30) * 4;
  return (
    <div style={{position: 'absolute', left: x, top: y + fy, width: size, height: size, transform: `translate(-50%, -100%) scale(${s}) rotate(${tilt}deg)`,
      transformOrigin: '50% 100%'}}>
      <div style={{position: 'absolute', inset: 0, borderRadius: '50%', background: p.panel, boxShadow: `0 8px 0 ${p.shadow}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT, fontWeight: 900,
        fontSize: size * 0.62, color: p.accent}}>{text}</div>
      <div style={{position: 'absolute', bottom: -size * 0.12, left: size * 0.22, width: size * 0.26, height: size * 0.26,
        background: p.panel, transform: 'rotate(45deg)', borderRadius: 4}} />
    </div>
  );
};

/** A gold coin (flat, with an edge), popping in at `at`. (x, y) = centre. */
export const Coin: React.FC<{p: Palette; x: number; y: number; at: number; size?: number; phase?: number}> = (
  {p, x, y, at, size = 120, phase = 0}) => {
  const f = useCurrentFrame();
  const s = pop(f, at, 30, 9, 230);
  const spin = 0.86 + 0.14 * Math.cos((f + phase) / 16);
  return (
    <div style={{position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) scale(${s})`}}>
      <svg width={size} height={size * 1.12} viewBox="0 0 100 112" style={{overflow: 'visible'}}>
        <ellipse cx={50} cy={58} rx={46 * Math.max(0.35, Math.abs(spin))} ry={46} fill="#C9861A" />
        <ellipse cx={50} cy={50} rx={46 * Math.max(0.35, Math.abs(spin))} ry={46} fill={p.accent} />
        <ellipse cx={50} cy={50} rx={32 * Math.max(0.35, Math.abs(spin))} ry={32} fill="none" stroke="#C9861A" strokeWidth={6} />
        <text x={50} y={64} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={40} fill="#C9861A"
              transform={`translate(50 0) scale(${Math.max(0.35, Math.abs(spin))} 1) translate(-50 0)`}>$</text>
      </svg>
    </div>
  );
};

/** Dashed arrow drawing from (x1,y1) to (x2,y2) between `from` and `to`. */
export const DashedArrow: React.FC<{x1: number; y1: number; x2: number; y2: number; from: number; to: number; color: string; bend?: number}> = (
  {x1, y1, x2, y2, from, to, color, bend = -120}) => {
  const f = useCurrentFrame();
  const t = interpolate(f, [from, to], [0, 1], clamp);
  const mx = (x1 + x2) / 2, my = (y1 + y2) / 2 + bend;
  const d = `M${x1},${y1} Q${mx},${my} ${x2},${y2}`;
  const L = 1.2 * Math.hypot(x2 - x1, y2 - y1) + Math.abs(bend);
  const march = -f * 1.5;
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
      <mask id={`m${x1}${y1}`}>
        <path d={d} fill="none" stroke="#fff" strokeWidth={30} strokeDasharray={L} strokeDashoffset={L * (1 - t)} />
      </mask>
      <path d={d} fill="none" stroke={color} strokeWidth={10} strokeLinecap="round" strokeDasharray="4 26"
            strokeDashoffset={march} mask={`url(#m${x1}${y1})`} />
      {t > 0.97 && (
        <g transform={`translate(${x2} ${y2}) rotate(${Math.atan2(y2 - my, x2 - mx) * 180 / Math.PI})`}>
          <path d="M-30,-22 L6,0 L-30,22" fill="none" stroke={color} strokeWidth={10} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      )}
    </svg>
  );
};
