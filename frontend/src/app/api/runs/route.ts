import { NextResponse } from "next/server";
import { fail } from "@/server/guard";
import { listRuns } from "@/server/aws";

export const dynamic = "force-dynamic";

export async function GET() {
  try { return NextResponse.json(await listRuns()); } catch (e) { return fail(e); }
}
