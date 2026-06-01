import { useCallback, useRef, useState } from 'react';

export interface CompareImage {
  src: string;
  label: string;
  caption: string;
  credit: string;
}

interface Props {
  before: CompareImage;
  after: CompareImage;
  /** 0–100, position of the slider */
  initialPosition?: number;
}

export function ImageCompare({ before, after, initialPosition = 50 }: Props) {
  const [position, setPosition] = useState(initialPosition);
  const containerRef = useRef<HTMLDivElement>(null);

  const updateFromPointer = useCallback((clientX: number) => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
    setPosition((x / rect.width) * 100);
  }, []);

  const onPointerDown = (e: React.PointerEvent) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    updateFromPointer(e.clientX);
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      updateFromPointer(e.clientX);
    }
  };

  return (
    <div className="image-compare">
      <div
        className="image-compare__frame"
        ref={containerRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        role="img"
        aria-label={`Comparison: ${before.label} versus ${after.label}`}
      >
        <img
          className="image-compare__img image-compare__img--after"
          src={after.src}
          alt=""
          draggable={false}
        />
        <div className="image-compare__before" style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}>
          <img className="image-compare__img" src={before.src} alt="" draggable={false} />
        </div>
        <div className="image-compare__labels">
          <span>{before.label}</span>
          <span>{after.label}</span>
        </div>
        <div className="image-compare__handle" style={{ left: `${position}%` }} aria-hidden="true">
          <div className="image-compare__handle-line" />
          <div className="image-compare__handle-knob" />
        </div>
      </div>
      <input
        type="range"
        className="image-compare__slider"
        min={0}
        max={100}
        value={position}
        onChange={(e) => setPosition(Number(e.target.value))}
        aria-label="Drag to compare images"
      />
      <p className="image-compare__caption">{before.caption}</p>
      <p className="image-compare__caption">{after.caption}</p>
      <p className="image-compare__credit">
        {before.credit} · {after.credit}
      </p>
    </div>
  );
}
