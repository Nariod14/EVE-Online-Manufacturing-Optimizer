'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button'; // ShadCN Button
import { cn } from '@/lib/utils'; // ShadCN utility for classNames

type LoginPanelProps = {
  characterName?: string;
};

export default function LoginPanel({ characterName }: LoginPanelProps) {
  const [loggingIn, setLoggingIn] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    // Only set mounted to true on the client
    setIsMounted(true);
  }, []);

  const handleLogin = () => {
    setLoggingIn(true);
    window.location.href = '/login'; // Redirect to EVE SSO
  };

  // Prevent rendering until after hydration
  if (!isMounted) return null;

  return (
    <div className="flex flex-col items-center my-8">
      <h1 className="text-3xl font-bold mb-6 text-blue-300">
        EVE Online Manufacturing Optimizer
      </h1>
      {!characterName ? (
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
          <form action="/logout" method="POST" className="inline">
            <Button
              type="submit"
              variant="secondary"
              className="px-4 py-2 text-blue-100 bg-blue-800 hover:bg-blue-700"
            >
              Logout
            </Button>
          </form>
        </>
      )}
    </div>
  );
}
