// Palettes for style: motion. One palette per channel keeps the look consistent (MOTION_PLAN.md).
// Our own colours: deep navy, warm amber (the classic pipeline's accent), cream, coral, teal, sky.
export type Palette = {
  bg: string; bg2: string; texture: string; ink: string; muted: string; panel: string;
  accent: string; good: string; bad: string; sky: string; coral: string; teal: string; shadow: string;
};

export const NAVY: Palette = {
  bg: '#0F1C33', bg2: '#16294A', texture: 'rgba(255,255,255,0.045)', ink: '#F7F1E5', muted: 'rgba(247,241,229,0.32)',
  panel: '#FFFFFF', accent: '#FFB020', good: '#2EC4B6', bad: '#FF5D5D', sky: '#6FA8DC', coral: '#FF7A59',
  teal: '#2EC4B6', shadow: 'rgba(4,10,22,0.55)',
};

export const FONT = 'Montserrat';
