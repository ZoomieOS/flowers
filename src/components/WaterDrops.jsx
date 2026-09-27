import { useMemo } from 'react'
import styles from './WaterDrops.module.css'

/** Несколько капель, которые мягко падают на букет. Монтируется заново при каждом «поливе». */
export default function WaterDrops({ active, width, height }) {
  const drops = useMemo(() => {
    if (!active) return []
    return Array.from({ length: 9 }, (_, i) => ({
      id: i,
      x: width * (0.26 + Math.random() * 0.48),
      y: height * (0.02 + Math.random() * 0.12),
      fall: height * (0.18 + Math.random() * 0.16),
      delay: Math.random() * 520,
      size: 7 + Math.random() * 5,
    }))
  }, [active, width, height])

  return (
    <div className={styles.layer} aria-hidden="true">
      {drops.map((d) => (
        <svg
          key={d.id}
          className={styles.drop}
          viewBox="0 0 10 14"
          width={d.size}
          height={d.size * 1.4}
          style={{ left: d.x, top: d.y, '--fall': `${d.fall}px`, animationDelay: `${d.delay}ms` }}
        >
          <defs>
            <linearGradient id={`g${d.id}`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#ffffff" stopOpacity="0.95" />
              <stop offset="0.55" stopColor="#dfe8ea" stopOpacity="0.55" />
              <stop offset="1" stopColor="#9fb3b8" stopOpacity="0.55" />
            </linearGradient>
          </defs>
          <path d="M5 0.6C3.4 3.4 1 6.2 1 9a4 4 0 0 0 8 0C9 6.2 6.6 3.4 5 0.6z" fill={`url(#g${d.id})`} stroke="rgba(120,140,145,.35)" strokeWidth="0.5" />
          <ellipse cx="3.6" cy="9" rx="0.9" ry="1.5" fill="#fff" opacity="0.85" />
        </svg>
      ))}
    </div>
  )
}
