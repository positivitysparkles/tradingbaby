import { NextResponse, type NextRequest } from 'next/server'

export function middleware(req: NextRequest) {
  const pw = process.env.DASHBOARD_PASSWORD
  if (!pw) return NextResponse.next()          // no password set → open

  const cookie = req.cookies.get('dash_auth')?.value
  if (cookie === pw) return NextResponse.next() // already authenticated

  // Check for ?pw= in the URL (deep-link auth)
  const urlPw = req.nextUrl.searchParams.get('pw')
  if (urlPw === pw) {
    const res = NextResponse.redirect(req.nextUrl.origin)
    res.cookies.set('dash_auth', pw, { httpOnly: true, maxAge: 60 * 60 * 24 * 30 }) // 30 days
    return res
  }

  // Show login page
  return new NextResponse(
    `<!DOCTYPE html>
<html>
<head>
  <title>W118 Dashboard</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    *{box-sizing:border-box;margin:0}
    body{background:#0a0a0f;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:monospace}
    .card{background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:40px;width:100%;max-width:360px}
    h1{color:#e2e8f0;font-size:18px;margin-bottom:4px}
    p{color:#475569;font-size:13px;margin-bottom:24px}
    input{width:100%;padding:10px 14px;background:#1e293b;border:1px solid #334155;border-radius:8px;color:#e2e8f0;font-size:14px;font-family:monospace;outline:none}
    input:focus{border-color:#7c3aed}
    button{width:100%;margin-top:12px;padding:10px;background:#7c3aed;color:#fff;border:none;border-radius:8px;font-size:14px;cursor:pointer;font-family:monospace}
    button:hover{background:#6d28d9}
    .err{color:#f87171;font-size:12px;margin-top:8px;display:none}
  </style>
</head>
<body>
  <div class="card">
    <h1>W118 Dashboard</h1>
    <p>Private — enter your password</p>
    <input type="password" id="pw" placeholder="password" autofocus>
    <button onclick="auth()">Enter</button>
    <p class="err" id="err">Wrong password</p>
  </div>
  <script>
    function auth(){
      const v=document.getElementById('pw').value
      window.location.href='/?pw='+encodeURIComponent(v)
    }
    document.getElementById('pw').addEventListener('keydown',e=>{if(e.key==='Enter')auth()})
  </script>
</body>
</html>`,
    { status: 401, headers: { 'Content-Type': 'text/html' } },
  )
}

export const config = { matcher: ['/((?!_next|favicon.ico).*)'] }
