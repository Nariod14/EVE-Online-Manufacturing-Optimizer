// src/mocks/initMocks.ts
export async function initMocks() {
  if (typeof window === 'undefined') return

  const { worker } = await import('./browser')
  await worker.start({
    onUnhandledRequest: 'warn' // logs unmocked requests to console!
  })
}
