import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { DU, assetUrl, freeSlot, initialFlowers, twine } from '../bouquet.js'
import Flower from './Flower.jsx'
import WaterDrops from './WaterDrops.jsx'
import AddFlower from './AddFlower.jsx'
import styles from './Gift.module.css'

export default function Gift({ config }) {
  const { bouquet, timing, labels } = config
  const [flowers, setFlowers] = useState(() => initialFlowers(config))
  const [scale, setScale] = useState(0.8)
  const [showMessage, setShowMessage] = useState(false)
  const [showPs, setShowPs] = useState(false)
  const [rain, setRain] = useState(0)
  const [panelOpen, setPanelOpen] = useState(false)
  const wrapRef = useRef(null)
  const refs = useRef({})
  const watering = useRef(false)

  const W = bouquet.width * DU
  const H = bouquet.height * DU

  // сцена букета масштабируется под ширину экрана и не занимает больше ~60% высоты
  useLayoutEffect(() => {
    const el = wrapRef.current
    const fit = () => {
      const byW = el.clientWidth / W
      const byH = (window.innerHeight * 0.62) / H
      setScale(Math.min(byW, byH, 1.25))
    }
    fit()
    const ro = new ResizeObserver(fit)
    ro.observe(el)
    window.addEventListener('resize', fit)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', fit)
    }
  }, [W, H])

  useEffect(() => {
    const t1 = setTimeout(() => setShowMessage(true), timing.messageDelayMs)
    const t2 = setTimeout(() => setShowPs(true), timing.psDelayMs + timing.messageDelayMs)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [timing])

  // порядок появления: сначала дальние цветы, потом ближние
  const enterDelays = useMemo(() => {
    const order = [...flowers].filter((f) => !f.added).sort((a, b) => (a.slot.z ?? 0) - (b.slot.z ?? 0))
    const map = {}
    order.forEach((f, i) => (map[f.key] = 120 + (i / Math.max(order.length - 1, 1)) * 800))
    return map
    // считаем только один раз для исходного букета
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const water = useCallback(() => {
    if (watering.current) return
    watering.current = true
    setRain((r) => r + 1)
    const all = Object.values(refs.current).filter(Boolean)
    all.forEach((f) => f.sway(0.9 + Math.random() * 0.8, 450 + Math.random() * 500))
    const shuffled = [...all].sort(() => Math.random() - 0.5)
    shuffled.slice(0, 2).forEach((f, i) => f.lift(900 + i * 350))
    setTimeout(() => (watering.current = false), 2600)
  }, [])

  const add = (type) => {
    const free = freeSlot(config, flowers, type)
    if (!free) return
    setFlowers((list) => [...list, { key: `${type}-${free.index}`, type, slot: free.slot, added: true }])
    setPanelOpen(false)
  }

  const nameOf = (type) => config.flowers.find((f) => f.id === type)?.name ?? ''

  return (
    <main className={styles.gift}>
      <div ref={wrapRef} className={styles.stageWrap} style={{ height: H * scale }}>
        <div className={styles.stage} style={{ width: W, height: H, transform: `scale(${scale})` }}>
          {flowers.map((f) => (
            <Flower
              key={f.key}
              ref={(r) => (refs.current[f.key] = r)}
              config={config}
              flower={f}
              enterDelay={f.added ? 0 : enterDelays[f.key] ?? 0}
              label={nameOf(f.type)}
              onTap={() => refs.current[f.key]?.sway(2.2)}
            />
          ))}
          <img
            className={styles.twine}
            src={assetUrl(twine.file)}
            alt=""
            draggable="false"
            style={{
              width: (twine.w * DU) / twine.ppc,
              height: (twine.h * DU) / twine.ppc,
              left: bouquet.binding.x * DU - (twine.center[0] * DU) / twine.ppc,
              top: bouquet.binding.y * DU - (twine.center[1] * DU) / twine.ppc,
            }}
          />
          <WaterDrops key={rain} active={rain > 0} width={W} height={H} />
        </div>
      </div>

      <section className={`${styles.message} ${showMessage ? styles.visible : ''}`} aria-live="polite">
        <p className={styles.lines}>
          {config.message.map((line, i) => (
            <span key={i} className={styles.line} style={{ transitionDelay: `${i * 420}ms` }}>
              {line}
            </span>
          ))}
        </p>
        <p className={styles.signature} style={{ transitionDelay: `${config.message.length * 420 + 300}ms` }}>
          {config.signature}
        </p>
        <p className={styles.date} style={{ transitionDelay: `${config.message.length * 420 + 600}ms` }}>
          {config.date}
        </p>
      </section>

      <p className={`${styles.ps} ${showPs ? styles.psVisible : ''}`}>{config.ps}</p>

      <nav className={`${styles.controls} ${showMessage ? styles.controlsVisible : ''}`}>
        <button type="button" className={styles.water} onClick={water} aria-label={labels.water} title={labels.water}>
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <path
              d="M12 3.2c-2.9 3.9-5.6 7.4-5.6 10.5a5.6 5.6 0 0 0 11.2 0c0-3.1-2.7-6.6-5.6-10.5z"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.1"
              strokeLinejoin="round"
            />
            <path d="M9.4 14.6a2.7 2.7 0 0 0 2.2 2.4" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" opacity="0.6" />
          </svg>
        </button>
        <button type="button" className={styles.addBtn} onClick={() => setPanelOpen(true)}>
          {labels.addFlower}
        </button>
      </nav>

      <AddFlower
        open={panelOpen}
        config={config}
        flowers={flowers}
        onClose={() => setPanelOpen(false)}
        onPick={add}
      />
    </main>
  )
}
