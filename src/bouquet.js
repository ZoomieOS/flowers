import assets from './data/assets.json'

// 1 см в «дизайн-пикселях» сцены букета. Сцена потом целиком масштабируется под экран.
export const DU = 10

// window.__FLOWER_DATA__ используется только в однофайловой версии для предпросмотра (картинки встроены в HTML)
const inlined = typeof window !== 'undefined' ? window.__FLOWER_DATA__ : null
export const assetUrl = (file) => inlined?.[file] ?? `${import.meta.env.BASE_URL}flowers/${file}`

export function assetFor(type, variant) {
  return assets.flowers[`${type}-${variant}`] ?? assets.flowers[`${type}-1`]
}

export const twine = assets.twine
export const thumbs = assets.thumbs

/** Начальный состав букета: первые initialCount мест каждого цветка. */
export function initialFlowers(config) {
  const list = []
  for (const f of config.flowers) {
    const slots = config.bouquet.slots[f.id] ?? []
    for (let i = 0; i < Math.min(f.initialCount, slots.length); i++) {
      list.push({ key: `${f.id}-${i}`, type: f.id, slot: slots[i], added: false })
    }
  }
  return list
}

export function freeSlot(config, flowers, type) {
  const slots = config.bouquet.slots[type] ?? []
  const used = flowers.filter((f) => f.type === type).length
  return used < slots.length ? { index: used, slot: slots[used] } : null
}

/** Геометрия одного цветка внутри сцены (в дизайн-пикселях). */
export function flowerGeometry(config, type, slot) {
  const a = assetFor(type, slot.variant)
  const k = DU / a.ppc
  const { binding, stemBelow } = config.bouquet
  const w = a.w * k
  const h = a.h * k
  const ox = a.stemX * k
  const oy = a.stemTopY * k + slot.reach * DU
  const keep = oy + (slot.below ?? stemBelow) * DU
  return {
    src: assetUrl(a.file),
    w,
    h,
    ox,
    oy,
    left: binding.x * DU - ox,
    top: binding.y * DU - oy,
    clipBottom: Math.max(0, h - keep),
    head: { x: a.head[0] * k, y: a.head[1] * k, r: a.headR * k },
    // глубина: цветы на заднем плане немного приглушены
    tone: slot.tone ?? 0.84 + 0.16 * Math.min((slot.z ?? 0) / 28, 1),
  }
}

export function preloadAll() {
  const files = [
    ...Object.values(assets.flowers).map((a) => a.file),
    assets.twine.file,
    ...Object.values(assets.thumbs),
  ]
  return Promise.all(
    files.map(
      (f) =>
        new Promise((resolve) => {
          const img = new Image()
          img.onload = img.onerror = () => {
            if (img.decode) img.decode().catch(() => {}).finally(resolve)
            else resolve()
          }
          img.src = assetUrl(f)
        }),
    ),
  )
}
