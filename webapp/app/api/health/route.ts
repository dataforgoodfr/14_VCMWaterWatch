import { NextResponse } from 'next/server'

// Lightweight health endpoint used by the Docker healthcheck.
// Must not depend on NocoDB or other external services.
export const dynamic = 'force-dynamic'

export function GET() {
	return NextResponse.json({ status: 'ok' }, { status: 200 })
}
