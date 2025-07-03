// src/global.d.ts
export {};

declare global {
  interface Window {
    __msw?: boolean;
  }
}

// types/globals.d.ts
export {}

declare global {
  interface Window {
    __MSW_READY__?: boolean;
  }

  var __MSW_READY__: boolean | undefined;
}