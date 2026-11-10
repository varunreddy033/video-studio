import {Timeline} from './types';

// A tiny timeline so the Motion composition opens in Remotion Studio without a job (npm run studio).
export const EXAMPLE: Timeline = {
  version: 1, fps: 30, width: 1920, height: 1080, durationFrames: 150, palette: 'navy',
  words: [], captions: {show: false, style: 'amber_word'},
  scenes: [
    {id: 's0', from: 0, frames: 78, transition: null, background: {tint: '#16294A'},
     headline: {appear: 4, words: [{text: 'TIMELINE', frame: 14}, {text: 'EXAMPLE', frame: 24}]},
     elements: [{id: 'e0', type: 'number', box: {x: 0, y: 0, w: 1920, h: 1080}, enter: {frame: 8, anim: 'pop'},
       props: {value: 5.5, decimals: 1, suffix: '%', label: 'count-up number', countFrames: 40}}]},
    {id: 's1', from: 60, frames: 90, transition: {type: 'push', dir: 'from-right', frames: 18}, background: {tint: '#1A2440'},
     elements: [{id: 'e1', type: 'chart', box: {x: 0, y: 0, w: 1920, h: 1080}, enter: {frame: 4, anim: 'pop'},
       props: {kind: 'bar', title: 'Bar chart', data: [['A', 3], ['B', 5], ['C', 8]], unit: ''}}]},
  ],
};
