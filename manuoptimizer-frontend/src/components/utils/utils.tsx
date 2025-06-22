import { useState, useEffect } from "react";
import { Button } from "../ui/button";

interface ConfirmDeleteButtonProps {
  onDelete: () => Promise<void> | void;
  className?: string;
}

export function numberToWords(n: number) {
  if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(2) + "b";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "m";
  if (n >= 1_000) return (n / 1_000).toFixed(2) + "k";
  return n.toString();
}




export function ConfirmDeleteButton({ onDelete, children }: { onDelete: () => void; children: React.ReactNode }) {
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (!confirming) return;
    const timer = setTimeout(() => setConfirming(false), 3000);
    return () => clearTimeout(timer);
  }, [confirming]);

  const handleClick = () => {
    if (confirming) {
      onDelete();
      setConfirming(false);
    } else {
      setConfirming(true);
    }
  };

  return (
    <Button
        size="sm"
        variant="destructive"
        onClick={handleClick}
        className={`transition-colors ${
        confirming
            ? "bg-red-700 hover:bg-red-900"
            : "bg-red-600 hover:bg-red-800"
        }`}
    >
        {confirming ? "Confirm Delete?" : children}
    </Button>
  );
}
