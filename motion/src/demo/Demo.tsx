import React from 'react';
import {AbsoluteFill, Easing, useCurrentFrame} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import timing from './timing.json';
import {Background, Floor} from '../components/Background';
import {HeadlinePill} from '../components/HeadlinePill';
import {LabelTag} from '../components/LabelTag';
import {BigNumber, CalendarPage, Coin, DashedArrow, Door, LineChart, QuestionBubble} from '../components/props';
import {push} from '../transitions/push';
import {zoomThrough} from '../transitions/zoomThrough';
import {at} from '../lib/anim';
import {NAVY as p} from '../lib/theme';

// Phase 1 look test (docs/MOTION_PLAN.md): three hand-built scenes. Every cue is tied to a spoken word.
type Scene = (typeof timing.scenes)[number];
const S = timing.scenes;
const T = timing.transitionFrames;
const word = (sc: Scene, i: number) => at(sc.words[i].s, sc.from);          // scene-local frame of word i
const totalFrames = Math.round(timing.total * timing.fps);
const durations = S.map((sc, i) => (i + 1 < S.length ? S[i + 1].from - sc.from + T : totalFrames - sc.from));
export const DEMO_FRAMES = totalFrames;

const Shake: React.FC<{at: number; children: React.ReactNode}> = ({at: a, children}) => {
  const f = useCurrentFrame();
  const k = f >= a && f < a + 10 ? (1 - (f - a) / 10) : 0;
  return <AbsoluteFill style={{transform: `translate(${Math.sin(f * 2.7) * 14 * k}px, ${Math.cos(f * 3.1) * 9 * k}px)`}}>{children}</AbsoluteFill>;
};

// ---------------------------------------------------------------- scene 1: four doors
const DOORS = [
  {label: 'FUND', color: p.accent, w: 8}, {label: 'PENSION', color: p.teal, w: 10},
  {label: 'JOB', color: p.sky, w: 12}, {label: 'BILLS', color: p.coral, w: 15},
];
const Doors: React.FC = () => {
  const sc = S[0];
  const floor = 900;
  return (
    <AbsoluteFill>
      <Background p={p} />
      <Floor p={p} y={floor} />
      <HeadlinePill p={p} appear={4} words={[
        {text: 'FOUR', at: word(sc, 2)}, {text: 'DOORS', at: word(sc, 3)}, {text: 'INTO', at: word(sc, 4)},
        {text: 'YOUR', at: word(sc, 5)}, {text: 'MONEY.', at: word(sc, 6)}]} />
      {DOORS.map((d, i) => {
        const x = 420 + i * 360;
        const a = word(sc, d.w) - 3;
        return (
          <React.Fragment key={d.label}>
            <Door p={p} x={x} bottom={floor} at={a} color={d.color} phase={i * 17} />
            <LabelTag p={p} text={d.label} x={x} y={floor - 440} at={a + 7} phase={i * 13} />
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- scene 2: the chart falls
const CHART = [100, 104, 102, 107, 105, 110, 108, 113, 111, 116, 114, 118, 117, 121, 119, 112, 106, 101.5];
const ChartScene: React.FC = () => {
  const sc = S[1];
  return (
    <Shake at={word(sc, 5)}>
      <Background p={p} tint="#1A2440" />
      <HeadlinePill p={p} appear={6} words={[
        {text: 'THE', at: word(sc, 7)}, {text: 'NASDAQ', at: word(sc, 8)}, {text: 'FELL', at: word(sc, 9)},
        {text: '5.5%', at: word(sc, 14)}]} />
      <CalendarPage p={p} x={150} y={330} month="NOV" day="5" weekday="THURSDAY" at={word(sc, 1) - 2} />
      <LineChart p={p} x={560} y={260} w={1220} h={600} values={CHART} appear={word(sc, 2)} from={word(sc, 7)}
                 to={word(sc, 18)} color={p.sky} endColor={p.bad} />
      <BigNumber x={850} y={385} value={-5.5} from={word(sc, 10)} to={word(sc, 14) + 6} color={p.bad} size={150} suffix="%" />
      <LabelTag p={p} text="WORST DAY IN 19 MONTHS" x={1560} y={300} at={word(sc, 20)} color={p.bad} size={30} />
    </Shake>
  );
};

// ---------------------------------------------------------------- scene 3: which door is next?
const Next: React.FC = () => {
  const sc = S[2];
  const floor = 900;
  const xs = [430, 720, 1010, 1300];
  return (
    <AbsoluteFill>
      <Background p={p} tint="#132643" />
      <Floor p={p} y={floor} />
      <HeadlinePill p={p} appear={10} words={[
        {text: 'WHICH', at: word(sc, 1)}, {text: 'DOOR', at: word(sc, 2)}, {text: 'IS', at: word(sc, 3)},
        {text: 'NEXT?', at: word(sc, 4)}]} />
      {xs.map((x, i) => (
        <Door key={i} p={p} x={x} bottom={floor} at={14 + i * 4} color={DOORS[i].color} w={205} h={365} phase={i * 21} />
      ))}
      {xs.map((x, i) => (
        <QuestionBubble key={i} p={p} x={x + 40} y={floor - 395} at={word(sc, 4) + i * 4} size={110} phase={i * 11} />
      ))}
      {[[0, 0], [1, 0], [2, 0], [0.5, 1], [1.5, 1], [1, 2]].map(([cx, row], i) => (
        <Coin key={i} p={p} x={1560 + cx * 112} y={floor - 58 - row * 100} at={word(sc, 8) + i * 4} size={112} phase={i * 23} />
      ))}
      <DashedArrow x1={1350} y1={floor - 470} x2={1640} y2={floor - 330} from={word(sc, 14)} to={word(sc, 16) + 8}
                   color={p.accent} bend={-170} />
    </AbsoluteFill>
  );
};

// the chart's last point, in frame pixels (chart box 560,260 1220x600, last value at the right end)
const lastY = 260 + 30 + (1 - (CHART[CHART.length - 1] - Math.min(...CHART)) / (Math.max(...CHART) - Math.min(...CHART))) * (600 - 70);
const lastX = 560 + 1220 - 40;

export const Demo: React.FC = () => (
  <AbsoluteFill style={{background: p.bg}}>
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={durations[0]}><Doors /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={push({direction: 'from-right'})}
        timing={linearTiming({durationInFrames: T, easing: Easing.inOut(Easing.cubic)})} />
      <TransitionSeries.Sequence durationInFrames={durations[1]}><ChartScene /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={zoomThrough({x: lastX, y: lastY})}
        timing={linearTiming({durationInFrames: T, easing: Easing.in(Easing.quad)})} />
      <TransitionSeries.Sequence durationInFrames={durations[2]}><Next /></TransitionSeries.Sequence>
    </TransitionSeries>
  </AbsoluteFill>
);
