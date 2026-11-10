import React from 'react';
import {AbsoluteFill, Easing} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import type {TransitionPresentation} from '@remotion/transitions';
import {Background} from '../components/Background';
import {HeadlinePill} from '../components/HeadlinePill';
import {NAVY, PALETTES, Palette} from '../lib/theme';
import {push} from '../transitions/push';
import {zoomThrough} from '../transitions/zoomThrough';
import {iris} from '../transitions/iris';
import {whip} from '../transitions/whip';
import {fade} from '@remotion/transitions/fade';
import {Captions} from './Captions';
import {ElementView} from './Elements';
import {Scene, Timeline, Transition} from './types';


// eslint-disable-next-line @typescript-eslint/no-explicit-any
const presentation = (t: Transition): TransitionPresentation<any> =>
  (t.type === 'zoom' ? zoomThrough({x: t.x, y: t.y})
    : t.type === 'iris' ? iris({x: (t as {x?: number}).x, y: (t as {y?: number}).y})
    : t.type === 'whip' ? whip({dir: 1})
    : t.type === 'fade' ? fade()
    : push({direction: t.type === 'push' ? t.dir : 'from-right'})) as TransitionPresentation<any>;

const SceneView: React.FC<{sc: Scene; p: Palette}> = ({sc, p: base}) => {
  const p = (sc.palette && PALETTES[sc.palette]) || base;       // [scene: ... | palette=light] overrides
  return (
  <AbsoluteFill>
    <Background p={p} tint={sc.background?.tint} plate={sc.background?.plate} />
    {sc.elements.map((el) => <ElementView key={el.id} el={el} p={p} sceneFrames={sc.frames} />)}
    {sc.headline ? <HeadlinePill p={p} appear={sc.headline.appear}
      words={sc.headline.words.map((w) => ({text: w.text, at: w.frame}))} /> : null}
  </AbsoluteFill>
  );
};

/** Renders any timeline.json (docs/MOTION_TIMELINE.md). Scene k's sequence length is chosen so that it starts at
 *  exactly scene.from inside the TransitionSeries (sequences overlap by the incoming transition's frames). */
export const MotionVideo: React.FC<Timeline> = (tl) => {
  const p = PALETTES[tl.palette] ?? NAVY;
  const sc = tl.scenes;
  return (
    <AbsoluteFill style={{background: p.bg}}>
      <TransitionSeries>
        {sc.map((s, k) => {
          const next = sc[k + 1];
          const len = next ? next.from - s.from + (next.transition && next.transition.type !== 'cut' ? next.transition.frames : 0)
            : tl.durationFrames - s.from;
          return (
            <React.Fragment key={s.id}>
              {k > 0 && s.transition && s.transition.type !== 'cut' ? (
                <TransitionSeries.Transition presentation={presentation(s.transition)}
                  timing={linearTiming({durationInFrames: s.transition.frames, easing: Easing.inOut(Easing.cubic)})} />
              ) : null}
              <TransitionSeries.Sequence durationInFrames={Math.max(1, len)}><SceneView sc={s} p={p} /></TransitionSeries.Sequence>
            </React.Fragment>
          );
        })}
      </TransitionSeries>
      {tl.captions?.show ? <Captions p={p} words={tl.words} fps={tl.fps} /> : null}
    </AbsoluteFill>
  );
};
