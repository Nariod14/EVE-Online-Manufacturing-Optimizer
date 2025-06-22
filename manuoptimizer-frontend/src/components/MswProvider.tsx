'use client';

import { useEffect } from 'react';

export function MswProvider() {
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      import('@/mocks/browser')
        .then(({ worker }) => {
          return worker.start({
            onUnhandledRequest: 'warn',
          }).then(() => {
            console.log('[MSW] Worker started');
            window.__msw = true;
            if ('__MSW_READY__' in globalThis) {
              globalThis.__MSW_READY__ = true;
            }
            
          });
        })
        .catch((err) => {
          console.error('[MSW] Failed to start worker', err);
        });
    }
  }, []);

  return null;
}
