import React from 'react';
import {useCurrentFrame} from 'remotion';
import {bob, pop} from '../lib/anim';
import {FONT, Palette} from '../lib/theme';

/** Small white tag with a pointer, pops in at `at` and floats a little. (x, y) = the point it points at. */
export const LabelTag: React.FC<{p: Palette; text: string; x: number; y: number; at: number; color?: string;
  size?: number; phase?: number; pointer?: 'down' | 'left' | 'up'}> = ({p, text, x, y, at, color, size = 34, phase = 0, pointer = 'down'}) => {
  const f = useCurrentFrame();
  const s = pop(f, at, 30, 10, 220);
  const fy = bob(f, phase, 4, 64);
  const down = pointer === 'down';
  if (pointer === 'up') {                                   // the tag hangs under the point (tail on top)
    return (
      <div style={{position: 'absolute', left: x, top: y - fy, transform: `translate(-50%, 0) scale(${s})`,
        transformOrigin: '50% 0%', opacity: Math.min(1, s * 2)}}>
        <div style={{position: 'relative', background: p.panel, color: color ?? p.onPanel, fontFamily: FONT, fontWeight: 800,
          fontSize: size, padding: `${size * 0.3}px ${size * 0.6}px`, borderRadius: size * 0.35, whiteSpace: 'nowrap',
          boxShadow: `0 ${size * 0.15}px 0 ${p.shadow}`, marginTop: size * 0.45}}>
          <div style={{position: 'absolute', left: '50%', top: -size * 0.2, width: size * 0.5, height: size * 0.5, background: p.panel,
            transform: 'translateX(-50%) rotate(45deg)', borderRadius: 3}} />
          <span style={{position: 'relative'}}>{text}</span>
        </div>
      </div>
    );
  }
  return (
    <div style={{position: 'absolute', left: x, top: y + fy, transform: `translate(${down ? '-50%' : '0'}, ${down ? '-100%' : '-50%'}) scale(${s})`,
      transformOrigin: down ? '50% 100%' : '0% 50%', opacity: Math.min(1, s * 2)}}>
      <div style={{position: 'relative', background: p.panel, color: color ?? p.onPanel, fontFamily: FONT, fontWeight: 800,
        fontSize: size, padding: `${size * 0.3}px ${size * 0.6}px`, borderRadius: size * 0.35, whiteSpace: 'nowrap',
        boxShadow: `0 ${size * 0.15}px 0 ${p.shadow}`, marginBottom: down ? size * 0.45 : 0, marginLeft: down ? 0 : size * 0.45}}>
        {text}
        <div style={down
          ? {position: 'absolute', left: '50%', bottom: -size * 0.32, width: size * 0.5, height: size * 0.5, background: p.panel,
             transform: 'translateX(-50%) rotate(45deg)', borderRadius: 3}
          : {position: 'absolute', left: -size * 0.2, top: '50%', width: size * 0.5, height: size * 0.5, background: p.panel,
             transform: 'translateY(-50%) rotate(45deg)', borderRadius: 3}} />
      </div>
    </div>
  );
};
