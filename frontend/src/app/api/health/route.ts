import { NextResponse } from "next/server";
import { fail } from "@/server/guard";
import { checkHealth } from "@/server/aws";

export const dynamic = "force-dynamic";

export async function GET() {
  try { return NextResponse.json(await checkHealth()); } catch (e) { return fail(e); }
}
