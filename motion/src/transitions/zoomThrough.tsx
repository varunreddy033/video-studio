import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import type {TransitionPresentation, TransitionPresentationComponentProps} from '@remotion/transitions';

type Props = {x: number; y: number; holeColor?: string};   // x, y = the point we dive into, in pixels (1920x1080)

/** Zoom-through: the camera dives into a point of the old scene (it grows huge around that point), and the new
 *  scene opens out of that same point as a growing circle, so the inside of the object becomes the next scene. */
const Zoom: React.FC<TransitionPresentationComponentProps<Props>> = ({children, presentationDirection, presentationProgress, passedProps}) => {
  const p = presentationProgress;
  const {x, y} = passedProps;
  const origin = `${x}px ${y}px`;
  if (presentationDirection === 'exiting') {
    const s = interpolate(p, [0, 1], [1, 9], {easing: (t) => t * t * t});
    return <AbsoluteFill style={{transform: `scale(${s})`, transformOrigin: origin}}>{children}</AbsoluteFill>;
  }
  const r = interpolate(p, [0.18, 1], [0, 2300], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: (t) => t * t});
  const s = interpolate(p, [0.18, 1], [0.35, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{clipPath: `circle(${r}px at ${x}px ${y}px)`, zIndex: 2}}>
      <AbsoluteFill style={{transform: `scale(${s})`, transformOrigin: origin}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

export const zoomThrough = (props: Props): TransitionPresentation<Props> => ({component: Zoom, props});
