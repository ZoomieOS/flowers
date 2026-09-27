import styles from './Intro.module.css'

export default function Intro({ config, leaving, onOpen }) {
  return (
    <main className={`${styles.intro} ${leaving ? styles.leaving : ''}`}>
      <p className={styles.text}>{config.intro}</p>
      <button className={styles.button} onClick={onOpen} disabled={leaving}>
        {config.introButton}
      </button>
    </main>
  )
}
