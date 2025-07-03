'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function CallbackPage() {
  const router = useRouter();

  useEffect(() => {
    // Simulate MSW intercepting /callback → setting login state
    router.push('/'); // Back to homepage after login
  }, [router]);

  return <p>🪄 Handling login... Redirecting...</p>;
}
