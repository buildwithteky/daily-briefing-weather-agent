import { NextResponse } from "next/server";

/** Blocks cross-site requests (a web page on another origin can't call your local AWS-backed API). */
export function sameOrigin(req: Request): boolean {
  const origin = req.headers.get("origin");
  return !origin || new URL(origin).host === req.headers.get("host");
}

export function fail(e: unknown) {
  const name = (e as Error).constructor?.name;
  const status = name === "ValidationError" ? 400 : 500;
  const message = status === 400 ? (e as Error).message : "AWS request failed: " + ((e as Error).name || "Error") + " - " + (e as Error).message;
  return NextResponse.json({ error: message }, { status });
}
export const forbidden = () => NextResponse.json({ error: "Cross-origin request blocked" }, { status: 403 });
