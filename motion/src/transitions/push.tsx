import React from 'react';
import {AbsoluteFill} from 'remotion';
import type {TransitionPresentation, TransitionPresentationComponentProps} from '@remotion/transitions';

export type PushDir = 'from-right' | 'from-left' | 'from-top' | 'from-bottom';
type Props = {direction: PushDir; shadow?: number};

/** Camera push: the old scene slides out while the new one slides in, with a soft dark shadow band on the new
 *  scene's leading edge (it reads as one continuous world moving past the camera). */
const Push: React.FC<TransitionPresentationComponentProps<Props>> = ({children, presentationDirection, presentationProgress, passedProps}) => {
  const p = presentationProgress;
  const {direction, shadow = 0.55} = passedProps;
  const horizontal = direction === 'from-right' || direction === 'from-left';
  const sign = direction === 'from-right' || direction === 'from-bottom' ? 1 : -1;
  const entering = presentationDirection === 'entering';
  const pos = entering ? (1 - p) * 100 * sign : -p * 100 * sign;      // % of the frame
  const tr = horizontal ? `translateX(${pos}%)` : `translateY(${pos}%)`;
  const band = 160;
  const bandStyle: React.CSSProperties = horizontal
    ? {top: 0, bottom: 0, width: band, [sign > 0 ? 'left' : 'right']: -band,
       background: `linear-gradient(${sign > 0 ? 'to left' : 'to right'}, rgba(3,8,18,${shadow}), rgba(3,8,18,0))`}
    : {left: 0, right: 0, height: band, [sign > 0 ? 'top' : 'bottom']: -band,
       background: `linear-gradient(${sign > 0 ? 'to top' : 'to bottom'}, rgba(3,8,18,${shadow}), rgba(3,8,18,0))`};
  return (
    <AbsoluteFill style={{transform: tr, zIndex: entering ? 2 : 1}}>
      {children}
      {entering && <div style={{position: 'absolute', ...bandStyle}} />}
      {!entering && <AbsoluteFill style={{background: `rgba(3,8,18,${0.35 * p})`}} />}
    </AbsoluteFill>
  );
};

export const push = (props: Props): TransitionPresentation<Props> => ({component: Push, props});
