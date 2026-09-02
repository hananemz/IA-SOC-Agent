import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('ia_soc_auth_token')?.value || request.headers.get('authorization');
  const isAuthPage = request.nextUrl.pathname.startsWith('/login');

  // If trying to access protected dashboard routes without token, redirect to /login
  if (!token && !isAuthPage && !request.nextUrl.pathname.startsWith('/_next') && !request.nextUrl.pathname.startsWith('/api')) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  // If already logged in and visiting /login, redirect to overview
  if (token && isAuthPage) {
    const overviewUrl = new URL('/', request.url);
    return NextResponse.redirect(overviewUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
