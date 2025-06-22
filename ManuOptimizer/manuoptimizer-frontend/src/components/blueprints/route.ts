import { NextResponse } from "next/server";
import { mockBlueprints } from "@/types/blueprints";

export async function GET() {
  return NextResponse.json(mockBlueprints);
}
