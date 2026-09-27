import { useImperativeHandle, useRef } from 'react'
import { flowerGeometry } from '../bouquet.js'
import styles from './Flower.module.css'

/**
 * Один цветок на стебле. Все обёртки имеют общий transform-origin в точке обвязки,
 * поэтому покачивание выглядит как движение стебля в руке, а не как вращение картинки.
 */
export default function Flower({ config, flower, enterDelay, ref, onTap, label }) {
  const { slot, type } = flower
  const g = flowerGeometry(config, type, slot)
  const swayRef = useRef(null)
  const liftRef = useRef(null)

  useImperativeHandle(ref, () => ({
    sway(amp = 1.8, delay = 0, dir = Math.random() < 0.5 ? -1 : 1) {
      const a = amp * dir
      swayRef.current?.animate(
        [
          { transform: 'rotate(0deg)' },
          { transform: `rotate(${a}deg)`, offset: 0.22 },
          { transform: `rotate(${-a * 0.62}deg)`, offset: 0.5 },
          { transform: `rotate(${a * 0.3}deg)`, offset: 0.74 },
          { transform: 'rotate(0deg)' },
        ],
        { duration: 1900, delay, easing: 'cubic-bezier(.35,.1,.3,1)' },
      )
    },
    lift(delay = 0) {
      liftRef.current?.animate(
        [
          { transform: 'translateY(0)' },
          { transform: 'translateY(-5px)', offset: 0.35 },
          { transform: 'translateY(-5px)', offset: 0.6 },
          { transform: 'translateY(0)' },
        ],
        { duration: 2600, delay, easing: 'ease-in-out' },
      )
    },
  }))

  const origin = `${g.ox}px ${g.oy}px`
  const box = { width: g.w, height: g.h, transformOrigin: origin }
  const transform = `rotate(${slot.angle}deg)${slot.flip ? ' scaleX(-1)' : ''}`
  // лёгкий «приход на место»: стебель чуть ближе к вертикали и ниже, затем встаёт как надо
  const enterFrom = `rotate(${-slot.angle * 0.22}deg) translateY(${14 + (slot.reach ?? 0) * 0.6}px)`

  return (
    <div
      className={styles.flower}
      style={{ ...box, left: g.left, top: g.top, zIndex: slot.z ?? 1, transform }}
    >
      <div
        className={styles.enter}
        style={{ ...box, '--from': enterFrom, animationDelay: `${enterDelay}ms` }}
      >
        <div ref={swayRef} className={styles.layer} style={box}>
          <div ref={liftRef} className={styles.layer} style={box}>
            <img
              className={styles.img}
              src={g.src}
              width={g.w}
              height={g.h}
              alt=""
              draggable="false"
              style={{ clipPath: `inset(0 0 ${g.clipBottom}px 0)`, '--tone': g.tone }}
            />
            <button
              type="button"
              className={styles.hit}
              aria-label={label}
              onClick={onTap}
              style={{
                left: g.head.x - g.head.r * 0.75,
                top: g.head.y - g.head.r * 0.75,
                width: g.head.r * 1.5,
                height: g.head.r * 1.5,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
