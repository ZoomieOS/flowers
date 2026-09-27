import { useEffect, useState } from 'react'
import config from './config.json'
import { preloadAll } from './bouquet.js'
import Intro from './components/Intro.jsx'
import Gift from './components/Gift.jsx'

export default function App() {
  // intro → leaving (мягкое исчезновение) → gift
  const [phase, setPhase] = useState('intro')
  const [ready, setReady] = useState(null)

  useEffect(() => {
    setReady(preloadAll())
  }, [])

  const open = async () => {
    if (phase !== 'intro') return
    setPhase('leaving')
    await Promise.all([ready, new Promise((r) => setTimeout(r, 1100))])
    setPhase('gift')
  }

  return phase === 'gift' ? (
    <Gift config={config} />
  ) : (
    <Intro config={config} leaving={phase === 'leaving'} onOpen={open} />
  )
}
