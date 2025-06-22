// lib/mswReady.ts
let ready = false
const readyPromise = new Promise<void>((resolve) => {
  if (ready) return resolve()
  Object.defineProperty(globalThis, '__MSW_READY__', {
    set: () => {
      ready = true
      resolve()
    },
    configurable: true
  })
})

export function waitForMswReady() {
  return readyPromise
}
