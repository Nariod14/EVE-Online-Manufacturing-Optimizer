'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { waitForMswReady } from '@/lib/mswReady';
import { a } from 'vitest/dist/chunks/suite.d.FvehnV49.js';

export default function LoginPanel() {
  const [characterName, setCharacterName] = useState<string | undefined>();
  const [loggingIn, setLoggingIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

useEffect(() => {
const checkAuth = async () => {
  setIsLoading(true)
  if (process.env.NODE_ENV === 'development') {
    await waitForMswReady();
  }
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)  // 5 sec timeout

    const res = await fetch('/auth/status', {
      credentials: 'include',
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!res.ok) throw new Error(`HTTP error ${res.status}`)

    const data = await res.json()
    console.log('FETCHED LOGIN STATUS:', data)

    if (data.logged_in) setCharacterName(data.character_name)
    else setCharacterName(undefined)

  } catch (err) {
    console.error('auth status fetch failed or timed out', err)
    setCharacterName(undefined)  // Force logged out UI on error
  } finally {
    setIsLoading(false)
  }
}


  checkAuth();

  const onFocus = async () => {
    await checkAuth();
  };

  window.addEventListener('focus', onFocus);

  return () => {
    window.removeEventListener('focus', onFocus);
  }
}, []);





const handleLogin = async () => {
  setLoggingIn(true);
  if (process.env.NODE_ENV === 'development') {
    await waitForMswReady();
  }

  // Simulate "logging in" in dev — this makes it persist after the redirect
  if (typeof window !== 'undefined') {
    localStorage.setItem('isLoggedIn', 'true');
  }

  window.location.href = '/login';
};


const handleLogout = async () => {
  console.log("👋 handleLogout started");

  if (process.env.NODE_ENV === 'development') {
    console.log("🧪 waiting for MSW");
    await waitForMswReady();
    console.log("🧪 clearing localStorage");
    localStorage.removeItem('isLoggedIn');
  }

  try {
    console.log("📡 sending POST /logout...");
    const res = await fetch('/logout', {
      method: 'POST',
      credentials: 'include',
    });

    if (res.ok) {
      console.log("✅ Logged out successfully");
      setCharacterName(undefined);
    } else {
      console.error("❌ Logout failed", await res.text());
    }
  } catch (err) {
    console.error("⚠️ Error during logout", err);
  }
};



  return (
    <div className="flex flex-col items-center my-8">
      <h1 className="text-3xl font-bold mb-6 text-blue-300">
        EVE Online Manufacturing Optimizer
      </h1>

      {isLoading ? (
        <div className="text-blue-200 animate-pulse">Checking login status...</div>
      ) : !characterName ? (
        <>
          <Button
            className={cn(
              'bg-gradient-to-r from-blue-900 via-blue-700 to-blue-500 text-white shadow-lg',
              'hover:from-blue-800 hover:to-blue-600 transition-all duration-200'
            )}
            disabled={loggingIn}
            onClick={handleLogin}
            size="lg"
          >
            {loggingIn ? 'Logging in...' : 'Log in with EVE Online'}
          </Button>
          <div className="mt-4 font-semibold text-blue-200">
            {loggingIn && 'Redirecting to EVE SSO...'}
          </div>
        </>
      ) : (
        <>
          <div className="my-4 font-bold text-blue-200">
            Welcome, {characterName}!
          </div>
          {characterName && (
            <Button
              onClick={() => {
                console.log("logout clicked");
                handleLogout();
              }}
              variant={'secondary'}
              className="px-4 py-2 text-blue-100 bg-blue-800 hover:bg-blue-700"
            >
              Logout
            </Button>
          )}

        </>
      )}
    </div>
  );
}
