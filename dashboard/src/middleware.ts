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
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    :root{
      --gold:#c9a96e;--gold-dim:#8b6e3c;--rose:#c4789b;
      --cream:#f0ebe0;--taupe:#7a6a5a;--bg:#080807;
      --card:#141210;--border:rgba(201,169,110,0.14);
    }
    body{
      background:var(--bg);
      display:flex;align-items:center;justify-content:center;
      min-height:100vh;
      font-family:'Inter',sans-serif;
      font-weight:300;
      -webkit-font-smoothing:antialiased;
    }
    .wrap{
      width:100%;max-width:380px;
      padding:48px 40px;
      background:var(--card);
      border:1px solid var(--border);
      border-radius:24px;
    }
    .ornament{
      text-align:center;
      color:var(--gold);
      font-size:11px;
      letter-spacing:0.3em;
      text-transform:uppercase;
      margin-bottom:20px;
    }
    h1{
      font-family:'Cormorant Garamond',Georgia,serif;
      font-size:40px;font-weight:600;line-height:1;
      color:var(--cream);
      text-align:center;margin-bottom:4px;
    }
    h1 em{color:var(--gold);font-style:italic;}
    .sub{
      font-size:11px;color:var(--taupe);
      text-align:center;letter-spacing:0.15em;
      text-transform:uppercase;margin-bottom:32px;
    }
    .divider{
      display:flex;align-items:center;gap:12px;margin-bottom:28px;
    }
    .divider-line{flex:1;height:1px;background:var(--border);}
    .divider-dot{color:var(--gold-dim);font-size:10px;}
    label{
      display:block;
      font-size:9px;letter-spacing:0.25em;text-transform:uppercase;
      color:var(--taupe);margin-bottom:8px;
    }
    input{
      width:100%;padding:12px 16px;
      background:rgba(201,169,110,0.04);
      border:1px solid var(--border);
      border-radius:10px;
      color:var(--cream);
      font-size:14px;font-family:'Inter',sans-serif;font-weight:300;
      outline:none;
      transition:border-color 0.2s;
    }
    input:focus{border-color:rgba(201,169,110,0.5);}
    input::placeholder{color:var(--taupe);}
    button{
      width:100%;margin-top:16px;padding:13px;
      background:var(--gold);
      color:var(--bg);
      border:none;border-radius:10px;
      font-size:12px;font-family:'Inter',sans-serif;
      font-weight:500;letter-spacing:0.15em;text-transform:uppercase;
      cursor:pointer;
      transition:opacity 0.2s;
    }
    button:hover{opacity:0.88;}
    .err{color:#c06060;font-size:11px;margin-top:10px;text-align:center;display:none;font-family:'Inter';}
    .quote{
      margin-top:28px;
      font-family:'Cormorant Garamond',Georgia,serif;
      font-size:13px;font-style:italic;
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
