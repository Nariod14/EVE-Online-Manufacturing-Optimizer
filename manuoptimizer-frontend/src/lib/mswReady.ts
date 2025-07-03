let ready = false;

const readyPromise = new Promise<void>((resolve) => {
  if (ready || (typeof globalThis !== 'undefined' && globalThis.__MSW_READY__ === true)) {
    ready = true;
    resolve();
    return;
  }

  Object.defineProperty(globalThis, '__MSW_READY__', {
    set: (v) => {
      if (v === true) {
        ready = true;
        resolve();
      }
    },
    configurable: true,
  });
});

export function waitForMswReady() {
  return readyPromise;
}
