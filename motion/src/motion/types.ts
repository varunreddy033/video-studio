// timeline.json, version 1. Keep in sync with docs/MOTION_TIMELINE.md and pipeline/motion.py.
export type Cue = {frame: number; word?: number; seg?: number; tok?: number;
  anim?: 'pop' | 'grow' | 'slide' | 'fade' | 'draw' | 'drop' | 'none' | 'count' | 'shake'};
export type Box = {x: number; y: number; w: number; h: number};
export type Element = {
  id: string;
  type: 'image' | 'video' | 'card' | 'number' | 'quote' | 'chart' | 'prop' | 'gen' | 'char' | 'label';
  kind?: string;
  props: Record<string, any>;
  box: Box;
  enter: Cue;
  exit?: Cue;
};
export type Transition =
  | {type: 'push'; dir: 'from-right' | 'from-left' | 'from-top' | 'from-bottom'; frames: number}
  | {type: 'zoom'; x: number; y: number; frames: number}
  | {type: 'cut'; frames: number}
  | {type: 'iris' | 'whip' | 'fade'; frames: number};
export type Scene = {
  id: string; from: number; frames: number; transition: Transition | null;
  background?: {tint?: string; name?: string};
  name?: string; line?: number;
  headline?: {appear: number; words: {text: string; word?: number; frame: number}[]};
  elements: Element[];
};
export type Word = {w: string; s: number; e: number; seg: number; frame: number};
export type Timeline = {
  version: 1; fps: number; width: number; height: number; durationFrames: number; palette: string;
  words: Word[]; captions: {show: boolean; style: string}; scenes: Scene[];
};
