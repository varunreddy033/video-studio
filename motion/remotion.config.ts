import {Config} from '@remotion/cli/config';

// Video-only render: Python mixes and muxes the audio (voice + music + sfx, -14 LUFS) afterwards.
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setOverwriteOutput(true);
