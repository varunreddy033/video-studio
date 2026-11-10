import React from 'react';
import {Freeze, useCurrentFrame} from 'remotion';
import {MotionVideo} from './MotionVideo';
import {Timeline} from './types';

export type PreviewProps = {timeline: Timeline; frames: number[]};

/** Check-page previews: output frame k = the timeline frozen at frames[k] (one representative moment per scene).
 *  Rendered as an image sequence, so one Remotion call (one bundle) makes every preview. */
export const Preview: React.FC<PreviewProps> = ({timeline, frames}) => {
  const k = useCurrentFrame();
  return <Freeze frame={frames[Math.min(k, frames.length - 1)] ?? 0}><MotionVideo {...timeline} /></Freeze>;
};
