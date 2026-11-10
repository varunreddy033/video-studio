import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {Demo, DEMO_FRAMES} from './demo/Demo';
import {ensureFonts} from './lib/fonts';
import {EXAMPLE} from './motion/example';
import {MotionVideo} from './motion/MotionVideo';
import {Preview, PreviewProps} from './motion/Preview';
import {Timeline} from './motion/types';

ensureFonts();

// Size, fps and length come from the timeline Python passes with --props=timeline.json.
const fromTimeline: CalculateMetadataFunction<Timeline> = ({props}) => ({
  durationInFrames: props.durationFrames, fps: props.fps, width: props.width, height: props.height,
});

export const Root: React.FC = () => (
  <>
    <Composition id="Demo" component={Demo} durationInFrames={DEMO_FRAMES} fps={30} width={1920} height={1080} />
    <Composition id="Motion" component={MotionVideo as unknown as React.FC<Record<string, unknown>>}
      defaultProps={EXAMPLE as unknown as Record<string, unknown>}
      calculateMetadata={fromTimeline as unknown as CalculateMetadataFunction<Record<string, unknown>>}
      durationInFrames={EXAMPLE.durationFrames} fps={30} width={1920} height={1080} />
    <Composition id="Preview" component={Preview as unknown as React.FC<Record<string, unknown>>}
      defaultProps={{timeline: EXAMPLE, frames: [70, 140]} as unknown as Record<string, unknown>}
      calculateMetadata={(({props}: {props: PreviewProps}) => ({durationInFrames: props.frames.length, fps: 30,
        width: props.timeline.width, height: props.timeline.height})) as unknown as CalculateMetadataFunction<Record<string, unknown>>}
      durationInFrames={2} fps={30} width={1920} height={1080} />
  </>
);
