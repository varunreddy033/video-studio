import {Easing, interpolate, spring} from 'remotion';

export const FPS = 30;
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** 0 -> 1 with a little overshoot, starting at frame `at` (pop / grow). */
export const pop = (frame: number, at: number, fps = FPS, damping = 11, stiffness = 170) =>
  spring({frame: frame - at, fps, config: {damping, stiffness, mass: 0.7}});

/** Plain eased 0 -> 1 over `dur` frames from `at`. */
export const ease = (frame: number, at: number, dur: number, easing = Easing.out(Easing.cubic)) =>
  interpolate(frame, [at, at + dur], [0, 1], {...clamp, easing});

/** Idle float: never stops, so something moves every second. */
export const bob = (frame: number, phase = 0, amp = 6, period = 70) =>
  Math.sin(((frame + phase) / period) * Math.PI * 2) * amp;

/** Seconds -> frame inside a scene that starts at absolute frame `sceneFrom`. */
export const at = (seconds: number, sceneFrom: number, fps = FPS) => Math.round(seconds * fps) - sceneFrom;
