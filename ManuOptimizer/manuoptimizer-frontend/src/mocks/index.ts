if (typeof window === 'undefined') {
  // don't start worker on server
  // (for SSR or testing use node setup, if you want)
} else {
  const { worker } = require('./browser');
  worker.start({ onUnhandledRequest: 'warn' });
}
