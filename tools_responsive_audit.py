import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE = os.environ.get("AUDIT_BASE", "http://127.0.0.1:5000")
OUT = Path(__file__).resolve().parent / "responsive-audit-results.json"
PAGES = {
    "student": ["/dashboard.html", "/homework.html", "/my_classes.html", "/grades.html", "/schedule.html", "/messages.html", "/settings.html"],
    "mentor": ["/mentor/dashboard.html", "/mentor/attendance.html", "/mentor/timetable.html", "/mentor/assignments.html", "/mentor/marks.html", "/mentor/notes.html", "/mentor/grades.html", "/mentor/schedule.html", "/mentor/messages.html", "/mentor/settings.html"],
}
VIEWPORTS = {"mobile": {"width": 390, "height": 844}, "tablet": {"width": 768, "height": 1024}, "desktop": {"width": 1440, "height": 900}}

async def login_once(page, role):
    email = f"responsive_{role}@example.com"
    payload = {"fullname": f"Responsive {role.title()}", "email": email, "phone": "9199999001" if role == "student" else "9199999002", "password": "StrongPass9!", "role": role}
    if role == "mentor":
        payload["mentorId"] = "RESP-001"
    await page.goto(BASE + "/", wait_until="domcontentloaded")
    async def call(endpoint, data):
        return await page.evaluate("""async ({endpoint, data}) => { const r = await fetch(endpoint, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)}); return {status:r.status, body:await r.json()}; }""", {"endpoint": endpoint, "data": data})
    login = await call("/login", {"username": email, "password": payload["password"], "role": role})
    if login["body"].get("status") != "success":
        signup = await call("/signup", payload)
        if signup["status"] != 200 or signup["body"].get("status") not in ("created", "exists"):
            raise RuntimeError(f"signup failed for {role}: {signup}")
        login = await call("/login", {"username": email, "password": payload["password"], "role": role})
    if login["status"] != 200 or login["body"].get("status") != "success":
        raise RuntimeError(f"login failed for {role}: {login}")
    if role == "mentor":
        complete = await page.evaluate("""async () => { const r=await fetch('/api/profile/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({department:'Computer Science',designation:'Lecturer'})}); return {status:r.status,body:await r.json()}; }""")
        if complete["status"] != 200:
            raise RuntimeError(f"mentor onboarding failed: {complete}")

async def audit_engine(browser_type, role):
    opts = {"headless": True}
    if browser_type.name == "chromium" and Path("/usr/bin/chromium").exists():
        opts["executable_path"] = "/usr/bin/chromium"
    browser = await browser_type.launch(**opts)
    context = await browser.new_context(viewport=VIEWPORTS["desktop"], device_scale_factor=1)
    page = await context.new_page()
    await login_once(page, role)
    results = []
    for viewport_name, viewport in VIEWPORTS.items():
        await page.set_viewport_size(viewport)
        for path in PAGES[role]:
            console_errors, failed_requests = [], []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url}: {req.failure}"))
            response = await page.goto(BASE + path, wait_until="networkidle")
            await page.wait_for_timeout(200)
            metrics = await page.evaluate("""() => { const vw=innerWidth, vh=innerHeight, b=document.body, d=document.documentElement; const overflowing=[...document.querySelectorAll('body *')].map(el=>{const r=el.getBoundingClientRect();return {tag:el.tagName.toLowerCase(),id:el.id,cls:String(el.className||'').slice(0,80),right:Math.round(r.right),left:Math.round(r.left),width:Math.round(r.width)};}).filter(x=>x.width>0&&(x.right>vw+1||x.left<-1)); return {innerWidth:vw,innerHeight:vh,scrollWidth:Math.max(b.scrollWidth,d.scrollWidth),clientWidth:d.clientWidth,viewportOverflow:Math.max(b.scrollWidth,d.scrollWidth)>vw+1,overflowing:overflowing.slice(0,12),title:d.title}; }""")
            results.append({"viewport": viewport_name, "page": path, "status": response.status if response else None, "final_url": page.url, "redirected_to_login": "/login" in page.url, "metrics": metrics, "console_errors": console_errors, "failed_requests": failed_requests})
    await browser.close()
    return {"browser": browser_type.name, "role": role, "results": results}

async def main():
    all_results = []
    async with async_playwright() as p:
        for engine in (p.chromium, p.firefox, p.webkit):
            for role in PAGES:
                try:
                    result = await audit_engine(engine, role)
                    all_results.append(result)
                    print(f"completed {result['browser']} {role}", flush=True)
                except Exception as exc:
                    all_results.append({"browser": engine.name, "role": role, "error": repr(exc)})
                    print(f"ERROR {engine.name} {role}: {exc!r}", flush=True)
    OUT.write_text(json.dumps(all_results, indent=2))
    checks = [x for r in all_results if "results" in r for x in r["results"]]
    failures = [x for x in checks if x["status"] != 200 or x["redirected_to_login"] or x["metrics"]["viewportOverflow"] or x["console_errors"] or x["failed_requests"]]
    print(json.dumps({"runs": len(all_results), "page_checks": len(checks), "failures": len(failures), "engine_errors": [r for r in all_results if "error" in r], "output": str(OUT)}, indent=2))
    for x in failures:
        print(json.dumps({"viewport":x["viewport"],"page":x["page"],"status":x["status"],"overflow":x["metrics"]["viewportOverflow"],"console_errors":x["console_errors"],"failed_requests":x["failed_requests"],"final_url":x["final_url"]}, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
