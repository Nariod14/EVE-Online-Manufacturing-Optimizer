'use client'; // ✅ This makes it a Client Component

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    // Simulate OAuth redirect in dev
    if (process.env.NODE_ENV === 'development') {
      router.push('/callback');
    } else {
      router.push('/');
    }
  }, [router]);

  return <p>🔐 Redirecting to callback...</p>;
}
