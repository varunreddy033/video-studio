import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import type {TransitionPresentation, TransitionPresentationComponentProps} from '@remotion/transitions';

type Props = {x?: number; y?: number; ring?: string};

/** Iris: the new scene opens as a growing circle (from the centre or a point) with a thin bright ring on its edge. */
const Iris: React.FC<TransitionPresentationComponentProps<Props>> = ({children, presentationDirection, presentationProgress, passedProps}) => {
  const {x = 960, y = 540, ring = 'rgba(255,255,255,0.85)'} = passedProps;
  if (presentationDirection === 'exiting') {
    return <AbsoluteFill style={{filter: `brightness(${1 - 0.35 * presentationProgress})`}}>{children}</AbsoluteFill>;
  }
  const r = interpolate(presentationProgress, [0, 1], [0, 2300], {easing: (t) => t * t * (3 - 2 * t)});
  return (
    <AbsoluteFill style={{zIndex: 2}}>
      <AbsoluteFill style={{clipPath: `circle(${r}px at ${x}px ${y}px)`}}>{children}</AbsoluteFill>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
        <circle cx={x} cy={y} r={r} fill="none" stroke={ring} strokeWidth={10} opacity={1 - presentationProgress} />
      </svg>
    </AbsoluteFill>
  );
};
export const iris = (props: Props = {}): TransitionPresentation<Props> => ({component: Iris, props});
