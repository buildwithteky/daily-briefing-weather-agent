import { NextResponse } from "next/server";
import { fail, forbidden, sameOrigin } from "@/server/guard";
import { generateNow } from "@/server/aws";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

export async function POST(req: Request) {
  if (!sameOrigin(req)) return forbidden();
  try { return NextResponse.json(await generateNow()); } catch (e) { return fail(e); }
}
