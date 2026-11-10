import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import type {TransitionPresentation, TransitionPresentationComponentProps} from '@remotion/transitions';

type Props = {dir?: 1 | -1};

/** Whip pan: a very fast sideways camera swing; both scenes smear with motion blur in the middle of the move. */
const Whip: React.FC<TransitionPresentationComponentProps<Props>> = ({children, presentationDirection, presentationProgress, passedProps}) => {
  const dir = passedProps.dir ?? 1;
  const p = presentationProgress;
  const e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;      // ease in-out, fast in the middle
  const entering = presentationDirection === 'entering';
  const x = entering ? (1 - e) * 100 * dir : -e * 100 * dir;
  const blur = interpolate(Math.abs(p - 0.5), [0, 0.5], [38, 0]);
  return (
    <AbsoluteFill style={{transform: `translateX(${x}%) skewX(${-dir * blur * 0.15}deg)`, filter: `blur(${blur}px)`, zIndex: entering ? 2 : 1}}>
      {children}
    </AbsoluteFill>
  );
};
export const whip = (props: Props = {}): TransitionPresentation<Props> => ({component: Whip, props});
