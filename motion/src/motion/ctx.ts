import React from 'react';

/** What a lip-synced presenter needs from the timeline: the mouth track of the whole video (absolute frames)
 *  and where its scene starts, so it keeps talking across scene changes. */
export type Talk = {mouth: [number, string][]; blinks: number[]; sceneFrom: number};
export const TalkCtx = React.createContext<Talk>({mouth: [], blinks: [], sceneFrom: 0});

/** Shape at an absolute frame: the last entry at or before it. */
export const shapeAt = (mouth: [number, string][], f: number): string => {
  let lo = 0, hi = mouth.length - 1, ans = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (mouth[mid][0] <= f) { ans = mid; lo = mid + 1; } else hi = mid - 1;
  }
  return ans < 0 ? 'closed' : mouth[ans][1];
};
export const blinkingAt = (blinks: number[], f: number): boolean => blinks.some((b) => f >= b && f < b + 4);
