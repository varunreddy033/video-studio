import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {bob, clamp, ease, pop} from '../lib/anim';
import {FONT, Palette} from '../lib/theme';
import {CalendarPage, Coin, DashedArrow, Door, QuestionBubble} from '../components/props';
import {LabelTag} from '../components/LabelTag';
import {Element} from './types';

const hash = (s: string) => [...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) | 0, 7);
const colorOf = (p: Palette, c?: string) => (c && (p as Record<string, string>)[c]) || c || p.accent;
// kinds whose drawing has its own entrance (the wrapper doesn't animate them again)
const SELF_ANIMATED = new Set(['door', 'coin', 'coins', 'question', 'exclamation', 'calendar', 'arrow', 'label']);

/** Enter + exit + idle for one placed element. Frames are local to the element's Sequence (0 = enter). */
export const Motion: React.FC<{el: Element; frames: number; children: React.ReactNode; idle?: boolean}> = (
  {el, frames, children, idle = true}) => {
  const f = useCurrentFrame();
  const anim = SELF_ANIMATED.has(el.kind ?? '') ? 'none' : el.enter.anim ?? 'pop';
  const s = pop(f, 0, 30, 11, 180);
  let tr = '', op = 1;
  if (anim === 'pop') { tr = `scale(${s})`; op = Math.min(1, s * 2); }
  else if (anim === 'grow') { tr = `scaleY(${s})`; }
  else if (anim === 'slide') { const k = ease(f, 0, 14); tr = `translateX(${(1 - k) * (el.box.x + el.box.w / 2 > 960 ? 400 : -400)}px)`; op = k; }
  else if (anim === 'fade') { op = ease(f, 0, 12); }
  else if (anim === 'drop') { const k = pop(f, 0, 30, 9, 140); tr = `translateY(${(1 - k) * -700}px)`; }
  else if (anim === 'shake') { tr = f < 12 ? `translateX(${Math.sin(f * 2.4) * 18 * (1 - f / 12)}px)` : ''; }
  const out = el.exit ? interpolate(f, [frames - 8, frames], [1, 0], clamp) : 1;
  const idleY = idle ? bob(f, hash(el.id) % 90, 5, 72 + (hash(el.id) % 30)) : 0;
  const origin = anim === 'grow' ? '50% 100%' : '50% 50%';
  return (
    <div style={{position: 'absolute', left: el.box.x, top: el.box.y + idleY, width: el.box.w, height: el.box.h,
      transform: `${tr} scale(${0.85 + 0.15 * out})`, transformOrigin: origin, opacity: op * out}}>{children}</div>
  );
};

const Placeholder: React.FC<{p: Palette; title: string; text?: string; w: number; h: number}> = ({p, title, text, w, h}) => (
  <div style={{width: w, height: h, borderRadius: 28, border: `5px dashed ${p.ink}55`, background: `${p.bg2}cc`,
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: FONT, textAlign: 'center',
    padding: 20, boxSizing: 'border-box'}}>
    <div style={{fontWeight: 900, fontSize: Math.min(44, w / 8), color: p.accent, letterSpacing: 1}}>{title}</div>
    {text ? <div style={{fontWeight: 700, fontSize: Math.min(34, w / 11), color: p.ink, marginTop: 10}}>{text}</div> : null}
  </div>
);

/** A soap bubble with a word in it. */
const Bubble: React.FC<{p: Palette; w: number; text: string}> = ({p, w, text}) => {
  const f = useCurrentFrame();
  const wob = 1 + 0.025 * Math.sin(f / 9);
  return (
    <svg width={w} height={w} viewBox="0 0 100 100" style={{overflow: 'visible', transform: `scale(${wob}, ${2 - wob})`}}>
      <defs>
        <radialGradient id="bub" cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.55" />
          <stop offset="55%" stopColor={p.sky} stopOpacity="0.18" />
          <stop offset="100%" stopColor={p.teal} stopOpacity="0.45" />
        </radialGradient>
      </defs>
      <circle cx="50" cy="50" r="46" fill="url(#bub)" stroke="#ffffff" strokeOpacity="0.7" strokeWidth="1.6" />
      <ellipse cx="34" cy="28" rx="10" ry="6" fill="#fff" opacity="0.75" transform="rotate(-30 34 28)" />
      <text x="50" y="57" textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={text.length > 6 ? 12 : 18} fill={p.ink}>{text}</text>
    </svg>
  );
};

/** Draws a library prop inside its box (phase 4 adds ~40 more kinds). */
export const PropView: React.FC<{el: Element; p: Palette}> = ({el, p}) => {
  const {w, h} = el.box;
  const k = el.kind ?? el.props.kind;
  const text: string = el.props.text ?? '';
  const c = colorOf(p, el.props.color);
  if (k === 'door') return <Door p={p} x={w / 2} bottom={h} at={0} color={c} w={w} h={h} phase={hash(el.id) % 40} />;
  if (k === 'coin') return <Coin p={p} x={w / 2} y={h / 2} at={0} size={Math.min(w, h)} />;
  if (k === 'coins') {
    const s = w / 3;
    return <>{[[0, 0], [1, 0], [2, 0], [0.5, 1], [1.5, 1], [1, 2]].map(([cx, row], i) =>
      <Coin key={i} p={p} x={s / 2 + cx * s} y={h - s * 0.55 - row * s * 0.9} at={i * 3} size={s} phase={i * 23} />)}</>;
  }
  if (k === 'question' || k === 'exclamation') return <QuestionBubble p={p} x={w / 2} y={h} at={0} text={k === 'question' ? '?' : '!'} size={Math.min(w, h)} />;
  if (k === 'calendar') {
    const [month, ...rest] = (text || 'NOV 5').split(/\s+/);
    return <CalendarPage p={p} x={0} y={0} month={month.toUpperCase()} day={rest[0] ?? ''} weekday={(el.props.weekday ?? rest.slice(1).join(' ')).toUpperCase()} at={0} w={w} />;
  }
  if (k === 'arrow') return <DashedArrow x1={el.box.x} y1={el.box.y + h / 2} x2={el.box.x + w} y2={el.box.y + h / 2} from={0} to={20} color={c} bend={-h * 0.6} />;
  if (k === 'bubble') return <Bubble p={p} w={Math.min(w, h)} text={text} />;
  return <Placeholder p={p} title={k.toUpperCase()} text={text} w={w} h={h} />;
};

export const GenView: React.FC<{el: Element; p: Palette}> = ({el, p}) =>
  el.props.src ? <Img src={staticFile(el.props.src)} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
    : <Placeholder p={p} title="AI PROP" text={el.props.text} w={el.box.w} h={el.box.h} />;

/** The presenter inside a scene: a pose cut-out (lip-sync arrives with Sterling Flat in phase 6), or a placeholder. */
export const CharView: React.FC<{el: Element; p: Palette}> = ({el, p}) => {
  const f = useCurrentFrame();
  const breathe = 1 + 0.012 * Math.sin(f / 18);
  if (el.props.src) return (
    <div style={{width: '100%', height: '100%', display: 'flex', alignItems: 'flex-end', justifyContent: 'center'}}>
      <Img src={staticFile(el.props.src)} style={{maxWidth: '100%', maxHeight: '100%', objectFit: 'contain',
        transform: `scaleY(${breathe})`, transformOrigin: '50% 100%', filter: 'drop-shadow(0 12px 0 rgba(0,0,0,0.25))'}} />
    </div>
  );
  return <Placeholder p={p} title="PRESENTER" text={el.props.pose} w={el.box.w} h={el.box.h} />;
};

export const LabelView: React.FC<{el: Element; p: Palette}> = ({el, p}) =>
  <LabelTag p={p} text={el.props.text} x={el.box.x} y={el.box.y} at={0} size={32} phase={hash(el.id) % 60} />;
