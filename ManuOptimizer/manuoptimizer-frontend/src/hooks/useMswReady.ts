'use client';

import { useEffect, useState } from 'react';

export function useMswReady() {
  const [mswReady, setMswReady] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const check = () => {
      if (window.__msw) {
        setMswReady(true);
      } else {
        // Wait for MSW to inject itself
        const interval = setInterval(() => {
          if (window.__msw) {
            clearInterval(interval);
            setMswReady(true);
          }
        }, 50);
      }
    };

    check();
  }, []);

  return mswReady;
}
