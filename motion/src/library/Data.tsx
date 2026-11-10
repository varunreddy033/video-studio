import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {clamp, ease, pop} from '../lib/anim';
import {FONT, Palette} from '../lib/theme';
import world from './worldmap.json';

// Data components drawn natively in their box (w x h px): pie, comparison, ranking, map with pin.
// Bar/line charts, big numbers, cards and quotes live in motion/Elements.tsx.

const fmt = (v: number, unit = '') =>
  `${v.toLocaleString('en-US', {maximumFractionDigits: Number.isInteger(v) ? 0 : 1})}${unit}`;

export const Pie: React.FC<{p: Palette; w: number; h: number; data: [string, number][]; unit?: string}> = ({p, w, h, data, unit = ''}) => {
  const f = useCurrentFrame();
  const total = data.reduce((s, d) => s + d[1], 0) || 1;
  const t = ease(f, 4, 40);
  const r = Math.min(w * 0.42, h * 0.4), cx = r + 10, cy = h / 2;
  const cols = [p.accent, p.teal, p.sky, p.coral, p.good, p.bad];
  let a0 = -Math.PI / 2;
  const slices = data.map(([label, v], i) => {
    const a1 = a0 + (v / total) * Math.PI * 2 * t;
    const large = a1 - a0 > Math.PI ? 1 : 0;
    const d = `M${cx},${cy} L${cx + r * Math.cos(a0)},${cy + r * Math.sin(a0)} A${r},${r} 0 ${large} 1 ${cx + r * Math.cos(a1)},${cy + r * Math.sin(a1)} Z`;
    a0 = a1;
    return <path key={label} d={d} fill={cols[i % cols.length]} stroke={p.bg} strokeWidth={4} />;
  });
  return (
    <div style={{width: w, height: h, position: 'relative'}}>
      <svg width={w} height={h} style={{overflow: 'visible'}}>
        <circle cx={cx} cy={cy + 10} r={r} fill="rgba(0,0,0,0.25)" />{slices}<circle cx={cx} cy={cy} r={r * 0.45} fill={p.bg2} />
      </svg>
      {(() => {
        const room = w - (cx * 2 + 40);
        const longest = Math.max(...data.map(([l, v]) => l.length + fmt(v, unit).length + 2));
        const fs = Math.max(18, Math.min(40, h / 12, room / (longest * 0.62)));
        return (
          <div style={{position: 'absolute', left: cx * 2 + 40, top: cy - data.length * fs * 0.8, fontFamily: FONT, width: room}}>
            {data.map(([label, v], i) => (
              <div key={label} style={{display: 'flex', alignItems: 'center', gap: fs * 0.35, height: fs * 1.6,
                opacity: ease(f, 10 + i * 6, 10), whiteSpace: 'nowrap'}}>
                <div style={{width: fs * 0.65, height: fs * 0.65, borderRadius: fs * 0.2, background: cols[i % cols.length], flexShrink: 0}} />
                <div style={{fontWeight: 800, fontSize: fs, color: p.ink}}>{label}</div>
                <div style={{fontWeight: 900, fontSize: fs, color: cols[i % cols.length]}}>{fmt(v, unit)}</div>
              </div>
            ))}
          </div>
        );
      })()}
    </div>
  );
};

/** Two sides, VS in the middle: [compare: LEFT: value | RIGHT: value]. Values count up; the bigger side grows. */
export const Compare: React.FC<{p: Palette; w: number; h: number; left: [string, number, string]; right: [string, number, string]}> = (
  {p, w, h, left, right}) => {
  const f = useCurrentFrame();
  const big = Math.max(Math.abs(left[1]), Math.abs(right[1]), 1e-9);
  const side = (d: [string, number, string], i: number) => {
    const s = pop(f, 4 + i * 8, 30, 12, 160);
    const t = ease(f, 8 + i * 8, 30);
    const k = 0.55 + 0.45 * Math.abs(d[1]) / big;
    const col = i ? p.coral : p.teal;
    return (
      <div style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        transform: `scale(${s})`, opacity: Math.min(1, s * 2)}}>
        <div style={{width: w * 0.3 * k, height: w * 0.3 * k, borderRadius: '50%', background: col, display: 'flex',
          alignItems: 'center', justifyContent: 'center', boxShadow: `0 12px 0 ${p.shadow}`}}>
          <div style={{fontFamily: FONT, fontWeight: 900, fontSize: w * 0.06 * k, color: p.onPanel}}>{d[2].replace('{v}', fmt(d[1] * t))}</div>
        </div>
        <div style={{fontFamily: FONT, fontWeight: 800, fontSize: Math.min(44, w / 22), color: p.ink, marginTop: 24, textAlign: 'center'}}>{d[0]}</div>
      </div>
    );
  };
  return (
    <div style={{width: w, height: h, display: 'flex', alignItems: 'center', position: 'relative'}}>
      {side(left, 0)}
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: w * 0.05, color: p.accent, transform: `scale(${pop(f, 14, 30, 8, 220)})`}}>VS</div>
      {side(right, 1)}
    </div>
  );
};

/** Ranking: rows sorted biggest first, rank number, bar growing from the left, value at the end. */
export const Ranking: React.FC<{p: Palette; w: number; h: number; data: [string, number][]; unit?: string}> = ({p, w, h, data, unit = ''}) => {
  const f = useCurrentFrame();
  const rows = [...data].sort((a, b) => b[1] - a[1]).slice(0, 8);
  const vmax = rows[0]?.[1] || 1;
  const rh = h / Math.max(rows.length, 3);
  return (
    <div style={{width: w, height: h, position: 'relative', fontFamily: FONT}}>
      {rows.map(([label, v], i) => {
        const g = pop(f, 4 + i * 6, 30, 13, 130);
        const bw = (w * 0.55) * (v / vmax) * Math.max(0, g);
        return (
          <div key={label} style={{position: 'absolute', top: i * rh, left: 0, right: 0, height: rh * 0.8, display: 'flex',
            alignItems: 'center', gap: 18, opacity: Math.min(1, g * 2)}}>
            <div style={{width: rh * 0.62, height: rh * 0.62, borderRadius: '50%', background: i === 0 ? p.accent : p.bg2,
              color: i === 0 ? p.onPanel : p.ink, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900,
              fontSize: rh * 0.32, flexShrink: 0}}>{i + 1}</div>
            <div style={{width: w * 0.25, fontWeight: 800, fontSize: Math.min(40, rh * 0.36), color: p.ink, whiteSpace: 'nowrap',
              overflow: 'hidden', textOverflow: 'ellipsis'}}>{label}</div>
            <div style={{width: bw, height: rh * 0.46, borderRadius: rh * 0.12, background: i === 0 ? p.accent : p.teal}} />
            <div style={{fontWeight: 900, fontSize: Math.min(40, rh * 0.36), color: p.ink}}>{fmt(v * Math.min(1, g), unit)}</div>
          </div>
        );
      })}
    </div>
  );
};

type Country = {name: string; iso: string; d: string; x: number; y: number};
const COUNTRIES = (world as {countries: Country[]}).countries;
const findCountry = (q: string) => {
  const n = q.trim().toLowerCase();
  const alias: Record<string, string> = {usa: 'united states of america', us: 'united states of america',
    'united states': 'united states of america', america: 'united states of america', uk: 'united kingdom',
    britain: 'united kingdom', korea: 'south korea', russia: 'russia', uae: 'united arab emirates'};
  const want = alias[n] ?? n;
  return COUNTRIES.find((c) => c.name.toLowerCase() === want || c.iso.toLowerCase() === want);
};

/** World map (Natural Earth, public domain): highlighted countries fill in one by one; a pin drops on the first
 *  one (or at pin lat,lon) and pulses. */
export const WorldMap: React.FC<{p: Palette; w: number; h: number; countries: string[]; pin?: string; pinLabel?: string}> = (
  {p, w, h, countries, pin, pinLabel}) => {
  const f = useCurrentFrame();
  const hl = countries.map(findCountry).filter(Boolean) as Country[];
  const vb = `0 0 ${(world as {width: number}).width} ${(world as {height: number}).height}`;
  let px: number | null = null, py: number | null = null;
  const m = pin?.match(/^\s*(-?\d+(\.\d+)?)\s*,\s*(-?\d+(\.\d+)?)\s*$/);
  if (m) {
    const lat = Number(m[1]), lon = Number(m[3]);
    px = (lon + 180) / 360 * 1000; py = (84 - Math.max(-58, Math.min(84, lat))) / 142 * 460;
  } else if (hl[0]) { px = hl[0].x; py = hl[0].y; }
  const drop = pop(f, 18 + hl.length * 6, 30, 9, 200);
  const pulse = (f % 40) / 40;
  return (
    <svg width={w} height={h} viewBox={vb} preserveAspectRatio="xMidYMid meet" style={{overflow: 'visible'}}>
      {COUNTRIES.map((c) => {
        const i = hl.indexOf(c);
        const on = i >= 0 ? interpolate(f, [6 + i * 6, 16 + i * 6], [0, 1], clamp) : 0;
        return <path key={c.iso + c.name} d={c.d} fill={on > 0 ? p.accent : p.ink} fillOpacity={on > 0 ? 0.35 + 0.65 * on : 0.13}
          stroke={p.bg} strokeWidth={0.6} />;
      })}
      {px !== null && py !== null ? (
        <g transform={`translate(${px} ${py - (1 - drop) * 80})`} opacity={Math.min(1, drop * 2)}>
          <circle r={6 + pulse * 22} fill={p.bad} opacity={(1 - pulse) * 0.5} />
          <path d="M0 0 C-9 -12 -12 -18 -12 -24 A12 12 0 1 1 12 -24 C12 -18 9 -12 0 0 Z" fill={p.bad} />
          <circle cy={-24} r={5} fill="#fff" />
          {pinLabel ? <text y={-44} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={18} fill={p.ink}>{pinLabel}</text> : null}
        </g>
      ) : null}
    </svg>
  );
};
