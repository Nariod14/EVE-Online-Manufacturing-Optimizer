import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { Blueprint } from "@/types/blueprints";

interface ConfirmDeleteButtonProps {
  onDelete: () => Promise<void> | void;
  className?: string;
}

export function numberToWords(n: number) {
  // Work on the size of the number so losses are shortened too (-1.50b, not -1500000000)
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000) return sign + (abs / 1_000_000_000).toFixed(2) + "b";
  if (abs >= 1_000_000) return sign + (abs / 1_000_000).toFixed(2) + "m";
  if (abs >= 1_000) return sign + (abs / 1_000).toFixed(2) + "k";
  return n.toString();
}

/**
 * Reads an ISK amount the way people type it: "250000000", "250,000,000", "200m", "1.5b", "750k".
 * An empty box means 0. Returns null when the text is not an amount.
 */
export function parseIskInput(text: string): number | null {
  const cleaned = text.trim().toLowerCase().replace(/,/g, "").replace(/\s+/g, "").replace(/isk$/, "");
  if (cleaned === "") return 0;

  const match = cleaned.match(/^(\d+(?:\.\d+)?|\.\d+)([kmb]?)$/);
  if (!match) return null;

  const multiplier = match[2] === "b" ? 1_000_000_000 : match[2] === "m" ? 1_000_000 : match[2] === "k" ? 1_000 : 1;
  const amount = parseFloat(match[1]) * multiplier;
  return Number.isFinite(amount) ? amount : null;
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


export const groupBlueprintsByStation = (blueprints: Blueprint[]) => {
  const grouped: Record<number, Blueprint[]> = {};

  blueprints.forEach((bp) => {
    if (bp.station_id) {
      if (!grouped[bp.station_id]) {
        grouped[bp.station_id] = [];
      }
      grouped[bp.station_id].push(bp);
    }
  });

  return grouped;
};
