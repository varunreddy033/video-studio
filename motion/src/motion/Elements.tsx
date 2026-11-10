import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {bob, clamp, ease, pop} from '../lib/anim';
import {FONT, Palette} from '../lib/theme';
import {BigNumber, LineChart} from '../components/props';
import {Element} from './types';

const MOVES = [[1, 1.1, 0, 0], [1.08, 1.08, -0.03, 0], [1.1, 1, 0, 0], [1.08, 1.08, 0.03, 0], [1, 1.1, -0.02, -0.015], [1.08, 1.08, 0, 0.025]];

/** Full-frame still with a slow camera move across the scene (draft placeholders and FLUX images). */
const ImageEl: React.FC<{el: Element; frames: number}> = ({el, frames}) => {
  const f = useCurrentFrame();
  const [z0, z1, px, py] = MOVES[(el.props.move ?? 0) % MOVES.length];
  const t = interpolate(f, [0, Math.max(1, frames)], [0, 1], clamp);
  const e = 0.5 - 0.5 * Math.cos(Math.PI * t);
  const z = z0 + (z1 - z0) * e;
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img src={staticFile(el.props.src)} style={{width: '100%', height: '100%', objectFit: el.props.fit ?? 'cover',
        transform: `scale(${z}) translate(${px * (e - 0.5) * 2 * 100}%, ${py * (e - 0.5) * 2 * 100}%)`}} />
    </AbsoluteFill>
  );
};

const VideoEl: React.FC<{el: Element}> = ({el}) => (
  <AbsoluteFill><OffthreadVideo src={staticFile(el.props.src)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} /></AbsoluteFill>
);

const CardEl: React.FC<{el: Element; p: Palette}> = ({el, p}) => {
  const f = useCurrentFrame();
  const s = pop(f, 0, 30, 12, 170);
  const bar = ease(f, 6, 14);
  const text: string = el.props.text ?? '';
  const size = text.length > 28 ? 104 : text.length > 16 ? 132 : 160;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column', padding: '0 160px'}}>
      <div style={{transform: `scale(${0.7 + 0.3 * s}) translateY(${bob(f, 0, 4, 90)}px)`, opacity: Math.min(1, s * 1.5),
        fontFamily: FONT, fontWeight: 900, fontSize: size, color: p.ink, textAlign: 'center', lineHeight: 1.05,
        textTransform: 'uppercase', textShadow: `0 10px 0 ${p.shadow}`}}>{text}</div>
      <div style={{width: 260 * bar, height: 12, borderRadius: 6, background: p.accent, margin: '38px 0 28px'}} />
      {el.props.sub ? <div style={{fontFamily: FONT, fontWeight: 600, fontSize: 48, color: p.muted.replace('0.32', '0.85'),
        opacity: ease(f, 10, 12), textAlign: 'center'}}>{el.props.sub}</div> : null}
    </AbsoluteFill>
  );
};

const NumberEl: React.FC<{el: Element; p: Palette}> = ({el, p}) => {
  const f = useCurrentFrame();
  const v = el.props.value as number;
  return (
    <AbsoluteFill>
      <BigNumber x={960} y={470} value={v} from={0} to={el.props.countFrames ?? 45} decimals={el.props.decimals ?? 0}
                 prefix={el.props.prefix ?? ''} suffix={el.props.suffix ?? ''} color={v < 0 ? p.bad : p.accent} size={260} appear={0} />
      <div style={{position: 'absolute', top: 650, left: 200, right: 200, textAlign: 'center', fontFamily: FONT, fontWeight: 700,
        fontSize: 52, color: p.ink, opacity: ease(f, 10, 14)}}>{el.props.label}</div>
    </AbsoluteFill>
  );
};

const QuoteEl: React.FC<{el: Element; p: Palette}> = ({el, p}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{justifyContent: 'center', padding: '0 220px'}}>
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 260, color: p.accent, lineHeight: 0.6, opacity: ease(f, 0, 10),
        transform: `translateY(${(1 - pop(f, 0)) * 30}px)`}}>“</div>
      <div style={{fontFamily: FONT, fontWeight: 600, fontStyle: 'italic', fontSize: 64, color: p.ink, lineHeight: 1.3,
        opacity: ease(f, 4, 14), transform: `translateY(${(1 - ease(f, 4, 14)) * 20}px)`}}>{el.props.text}</div>
      {el.props.by ? <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 40, color: p.accent, marginTop: 36,
        opacity: ease(f, 14, 12)}}>— {el.props.by}</div> : null}
    </AbsoluteFill>
  );
};

const ChartEl: React.FC<{el: Element; p: Palette; frames: number}> = ({el, p, frames}) => {
  const f = useCurrentFrame();
  const data: [string, number][] = el.props.data;
  const unit: string = el.props.unit ?? '';
  const title = (
    <div style={{position: 'absolute', top: 70, left: 0, right: 0, textAlign: 'center', fontFamily: FONT, fontWeight: 900,
      fontSize: 62, color: p.ink, opacity: ease(f, 0, 10)}}>{el.props.title}</div>
  );
  if (el.props.kind === 'line') {
    return <AbsoluteFill>{title}<LineChart p={p} x={200} y={230} w={1520} h={640} values={data.map((d) => d[1])}
      from={6} to={Math.min(frames - 10, 75)} color={p.sky} endColor={p.accent} appear={0} />
      <div style={{position: 'absolute', top: 890, left: 200, width: 1520, display: 'flex', justifyContent: 'space-between',
        fontFamily: FONT, fontWeight: 700, fontSize: 32, color: p.ink, opacity: 0.8}}>{data.map((d) => <span key={d[0]}>{d[0]}</span>)}</div>
    </AbsoluteFill>;
  }
  const vmax = Math.max(...data.map((d) => d[1]), 1e-9);
  const n = data.length, gap = 40, area = 1500, bw = (area - gap * (n - 1)) / n, base = 860, hmax = 540;
  return (
    <AbsoluteFill>{title}
      {data.map(([label, v], i) => {
        const g = pop(f, 6 + i * 5, 30, 13, 120);
        const h = (v / vmax) * hmax * Math.max(0, g);
        const x = 210 + i * (bw + gap);
        return (
          <React.Fragment key={label}>
            <div style={{position: 'absolute', left: x, top: base - h, width: bw, height: h, borderRadius: '18px 18px 4px 4px',
              background: i % 2 ? p.teal : p.accent, boxShadow: `0 10px 0 ${p.shadow}`}} />
            <div style={{position: 'absolute', left: x, width: bw, top: base - h - 74, textAlign: 'center', fontFamily: FONT,
              fontWeight: 900, fontSize: 50, color: p.ink, opacity: Math.min(1, g)}}>
              {(v * Math.min(1, g)).toLocaleString('en-US', {maximumFractionDigits: Number.isInteger(v) ? 0 : 1})}{unit}</div>
            <div style={{position: 'absolute', left: x - 20, width: bw + 40, top: base + 22, textAlign: 'center', fontFamily: FONT,
              fontWeight: 700, fontSize: 34, color: p.ink, opacity: 0.85}}>{label}</div>
          </React.Fragment>
        );
      })}
      <div style={{position: 'absolute', left: 190, width: 1540, top: base, height: 5, borderRadius: 3, background: `${p.ink}44`}} />
    </AbsoluteFill>
  );
};

/** One element of a scene, shown from its enter frame (and until its exit frame, if any). */
export const ElementView: React.FC<{el: Element; p: Palette; sceneFrames: number}> = ({el, p, sceneFrames}) => {
  const from = el.enter?.frame ?? 0;
  const until = el.exit ? el.exit.frame : sceneFrames;
  const frames = Math.max(1, until - from);
  const body = el.type === 'image' ? <ImageEl el={el} frames={frames} />
    : el.type === 'video' ? <VideoEl el={el} />
    : el.type === 'card' ? <CardEl el={el} p={p} />
    : el.type === 'number' ? <NumberEl el={el} p={p} />
    : el.type === 'quote' ? <QuoteEl el={el} p={p} />
    : el.type === 'chart' ? <ChartEl el={el} p={p} frames={frames} />
    : null;
  return <Sequence from={from} durationInFrames={frames} layout="none">{body}</Sequence>;
};
