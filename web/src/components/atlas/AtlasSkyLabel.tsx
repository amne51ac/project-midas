import type { MutableRefObject, ReactNode } from 'react';
import { Html } from '@react-three/drei';
import type * as THREE from 'three';

export type AtlasSkyLabelVariant =
  | 'star'
  | 'constellation'
  | 'constellation-secondary'
  | 'dso';

/** Screen-space label — fixed CSS size; does not scale with zoom (FOV). */
export function AtlasSkyLabel({
  position,
  children,
  variant = 'star',
  portal,
}: {
  position: THREE.Vector3;
  children: ReactNode;
  variant?: AtlasSkyLabelVariant;
  portal: MutableRefObject<HTMLElement>;
}) {
  return (
    <Html
      position={position}
      center
      portal={portal}
      zIndexRange={[1000, 0]}
      style={{ pointerEvents: 'none', userSelect: 'none' }}
    >
      <span className={`atlas-sky-label atlas-sky-label--${variant}`}>{children}</span>
    </Html>
  );
}
