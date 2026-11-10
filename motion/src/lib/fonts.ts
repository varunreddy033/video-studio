import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';
import {FONT} from './theme';

// Montserrat (SIL Open Font License), bundled in public/fonts so renders never need the internet.
let loaded: Promise<unknown> | null = null;
export const ensureFonts = () => {
  if (!loaded) {
    loaded = Promise.all([500, 700, 800, 900].map((weight) =>
      loadFont({family: FONT, url: staticFile('fonts/Montserrat.ttf'), weight: String(weight)})));
  }
  return loaded;
};
