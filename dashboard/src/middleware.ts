import { NextResponse, type NextRequest } from 'next/server'

export function middleware(req: NextRequest) {
  const pw = process.env.DASHBOARD_PASSWORD
  if (!pw) return NextResponse.next()

  const cookie = req.cookies.get('dash_auth')?.value
  if (cookie === pw) return NextResponse.next()

  const urlPw = req.nextUrl.searchParams.get('pw')
  if (urlPw === pw) {
    const res = NextResponse.redirect(req.nextUrl.origin)
    res.cookies.set('dash_auth', pw, { httpOnly: true, maxAge: 60 * 60 * 24 * 30 })
    return res
  }

  return new NextResponse(
    `<!DOCTYPE html>
<html>
<head>
  <title>Olya's Dashboard</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    :root{
      --pink:#ff5fa2;--pink-soft:#ffa6cd;--gold:#e7c79c;
      --ink:#f3eef7;--taupe:#9c90ad;--bg:#0b0910;
      --card:#15111f;--card2:#1c1729;--border:rgba(255,95,162,0.18);
    }
    body{
      background:
        radial-gradient(900px 500px at 88% -8%, rgba(255,95,162,0.18), transparent),
        radial-gradient(700px 500px at 0% 100%, rgba(231,199,156,0.08), transparent),
        var(--bg);
      display:flex;align-items:center;justify-content:center;
      min-height:100vh;
      font-family:'Space Grotesk',system-ui,sans-serif;
      font-weight:400;
      -webkit-font-smoothing:antialiased;
    }
    .mono{font-family:'JetBrains Mono',monospace;}
    .wrap{
      width:100%;max-width:380px;
      padding:48px 40px;
      background:var(--card);
      border:1px solid var(--border);
      border-radius:24px;
      box-shadow:0 0 0 1px rgba(255,95,162,0.06),0 24px 60px rgba(0,0,0,0.55);
    }
    .ornament{
      text-align:center;
      color:var(--pink);
      font-size:11px;
      letter-spacing:0.3em;
      text-transform:uppercase;
      margin-bottom:20px;
      font-weight:500;
      font-family:'JetBrains Mono',monospace;
    }
    h1{
      font-family:'Space Grotesk',sans-serif;
      font-size:38px;font-weight:700;line-height:1;letter-spacing:-0.02em;
      color:var(--ink);
      text-align:center;margin-bottom:4px;
    }
    h1 em{color:var(--pink);font-style:normal;text-shadow:0 0 22px rgba(255,95,162,0.45);}
    .sub{
      font-size:10px;color:var(--taupe);
      text-align:center;letter-spacing:0.2em;
      text-transform:uppercase;margin-bottom:32px;
      font-family:'JetBrains Mono',monospace;
    }
    .divider{
      display:flex;align-items:center;gap:12px;margin-bottom:28px;
    }
    .divider-line{flex:1;height:1px;background:var(--border);}
    .divider-dot{color:var(--pink);font-size:10px;}
    label{
      display:block;
      font-size:9px;letter-spacing:0.25em;text-transform:uppercase;
      color:var(--taupe);margin-bottom:8px;
      font-family:'JetBrains Mono',monospace;
    }
    input{
      width:100%;padding:12px 16px;
      background:var(--card2);
      border:1px solid var(--border);
      border-radius:10px;
      color:var(--ink);
      font-size:14px;font-family:'JetBrains Mono',monospace;font-weight:400;
      outline:none;
      transition:border-color 0.2s,box-shadow 0.2s;
    }
    input:focus{border-color:var(--pink);box-shadow:0 0 0 3px rgba(255,95,162,0.15);}
    input::placeholder{color:var(--taupe);}
    button{
      width:100%;margin-top:16px;padding:13px;
      background:var(--pink);
      color:var(--bg);
      border:none;border-radius:10px;
      font-size:12px;font-family:'Space Grotesk',sans-serif;
      font-weight:600;letter-spacing:0.15em;text-transform:uppercase;
      cursor:pointer;
      transition:opacity 0.2s,box-shadow 0.2s;
      box-shadow:0 0 24px rgba(255,95,162,0.35);
    }
    button:hover{opacity:0.92;box-shadow:0 0 34px rgba(255,95,162,0.55);}
    .err{color:#ff6b81;font-size:11px;margin-top:10px;text-align:center;display:none;font-family:'JetBrains Mono';}
    .quote{
      margin-top:28px;
      font-family:'Space Grotesk',sans-serif;
      font-size:14px;font-weight:500;
      color:var(--taupe);text-align:center;
      line-height:1.6;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="ornament">✦ &nbsp; W118 · Curl if Flow &nbsp; ✦</div>
    <h1><em>Olya&rsquo;s</em> Dashboard</h1>
    <p class="sub">Private access</p>
    <div class="divider">
      <div class="divider-line"></div>
      <span class="divider-dot">✦</span>
      <div class="divider-line"></div>
    </div>
    <label for="pw">Password</label>
    <input type="password" id="pw" placeholder="Enter your password" autofocus>
    <button onclick="auth()">Enter &rarr;</button>
    <p class="err" id="err">Incorrect password. Try again.</p>
    <p class="quote">She doesn&rsquo;t chase. She builds.</p>
  </div>
  <script>
    function auth(){
      const v=document.getElementById('pw').value.trim();
      if(!v){document.getElementById('err').style.display='block';return;}
      window.location.href='/?pw='+encodeURIComponent(v);
    }
    document.getElementById('pw').addEventListener('keydown',function(e){
      if(e.key==='Enter')auth();
    });
    const p=new URLSearchParams(location.search);
    if(p.get('pw'))document.getElementById('err').style.display='block';
  </script>
</body>
</html>`,
    { status: 401, headers: { 'Content-Type': 'text/html' } },
  )
}

export const config = { matcher: ['/((?!_next|favicon.ico).*)'] }
