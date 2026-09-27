import { assetUrl, freeSlot, thumbs } from '../bouquet.js'
import styles from './AddFlower.module.css'

export default function AddFlower({ open, config, flowers, onClose, onPick }) {
  return (
    <>
      <div className={`${styles.scrim} ${open ? styles.open : ''}`} onClick={onClose} />
      <div className={`${styles.panel} ${open ? styles.open : ''}`} role="dialog" aria-hidden={!open}>
        <p className={styles.hint}>{config.labels.addFlowerHint}</p>
        <ul className={styles.list}>
          {config.flowers.map((f) => {
            const free = freeSlot(config, flowers, f.id)
            return (
              <li key={f.id}>
                <button
                  type="button"
                  className={styles.item}
                  disabled={!free}
                  title={free ? f.name : config.labels.full}
                  onClick={() => onPick(f.id)}
                  tabIndex={open ? 0 : -1}
                >
                  <span className={styles.thumb}>
                    <img src={assetUrl(thumbs[f.id])} alt="" draggable="false" />
                  </span>
                  <span className={styles.name}>{f.name}</span>
                </button>
              </li>
            )
          })}
        </ul>
        <button type="button" className={styles.close} onClick={onClose} tabIndex={open ? 0 : -1}>
          {config.labels.close}
        </button>
      </div>
    </>
  )
}
