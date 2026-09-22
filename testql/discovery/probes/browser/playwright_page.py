"""Playwright-backed web page probe for JS-rendered content."""

from __future__ import annotations

from typing import Any

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover
    sync_playwright = None  # type: ignore[assignment]
    _PLAYWRIGHT_AVAILABLE = False

from testql.discovery.probes.base import BaseProbe, ProbeResult
from testql.discovery.source import ArtifactSource, SourceKind


def _find_browser_executable() -> str | None:
    import os
    from pathlib import Path
    env_bin = os.environ.get("PLAYWRIGHT_CHROME") or os.environ.get("CLONERD_CHROMIUM")
    if env_bin and Path(env_bin).exists():
        return env_bin
    for candidate in [
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
    ]:
        if Path(candidate).exists():
            return candidate
    return None


class PlaywrightPageProbe(BaseProbe):
    name = "browser.playwright_page"
    artifact_types = ("web_page", "browser_page")
    cost = "expensive"

    def __init__(self, timeout: float = 30.0, wait_until: str = "networkidle"):
        self.timeout = timeout
        self.wait_until = wait_until

    def applicable(self, source: ArtifactSource) -> bool:
        return source.kind == SourceKind.URL

    def probe(self, source: ArtifactSource) -> ProbeResult:
        if not _PLAYWRIGHT_AVAILABLE:
            exc = ImportError("playwright is not installed")
            return self.result(
                0,
                ["browser_page"],
                [self.evidence("browser_unavailable", source.location, str(exc))],
                {"url": source.location, "error": str(exc), "reachable": False},
            )

        console_errors: list[str] = []
        network_calls: list[dict[str, Any]] = []

        with sync_playwright() as p:
            exe = _find_browser_executable()
            launch_kwargs = {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}
            if exe:
                launch_kwargs["executable_path"] = exe
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("request", lambda req: network_calls.append({"url": req.url, "method": req.method, "resource_type": req.resource_type}))

            try:
                response = page.goto(source.location, wait_until=self.wait_until, timeout=self.timeout * 1000)
            except Exception as exc:
                browser.close()
                return self.result(
                    35,
                    ["browser_page"],
                    [self.evidence("browser_error", source.location, str(exc))],
                    {"url": source.location, "error": str(exc), "reachable": False},
                )

            status_code = response.status if response else None
            final_url = page.url
            title = page.title()

            links = page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    url: a.href,
                    text: a.textContent.trim(),
                }))
            """)
            assets = page.evaluate("""
                () => [
                    ...Array.from(document.querySelectorAll('script[src]')).map(el => ({url: el.src, tag: 'script'})),
                    ...Array.from(document.querySelectorAll('link[href]')).map(el => ({url: el.href, tag: 'link', rel: el.rel})),
                    ...Array.from(document.querySelectorAll('img[src]')).map(el => ({url: el.src, tag: 'img'})),
                ]
            """)
            forms = page.evaluate("""
                () => Array.from(document.querySelectorAll('form')).map(f => ({
                    action: f.action,
                    method: (f.method || 'get').toLowerCase(),
                }))
            """)
            layout_anomalies = page.evaluate("""
                () => {
                    const anomalies = [];
                    function getClassName(el) {
                        if (!el) return '';
                        if (typeof el.className === 'string') return el.className;
                        if (el.className && typeof el.className.baseVal === 'string') return el.className.baseVal;
                        return el.getAttribute('class') || '';
                    }
                    function getSelector(el) {
                        if (!el) return '';
                        if (el.id) return `#${el.id}`;
                        const cls = getClassName(el).trim().split(/\\s+/).filter(Boolean)[0];
                        return cls ? `.${cls}` : el.tagName.toLowerCase();
                    }

                    const all = Array.from(document.querySelectorAll('body *')).filter(el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0 && rect.width > 0 && rect.height > 0;
                    });

                    // 1. Horizontal viewport overflow
                    for (const el of all) {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > window.innerWidth + 1.5 || rect.left < -1.5) {
                            anomalies.push({
                                type: 'viewport_overflow',
                                element: getSelector(el),
                                text: (el.innerText || '').slice(0, 50).trim(),
                                details: `right: ${rect.right.toFixed(1)}px > viewport: ${window.innerWidth}px`
                            });
                        }
                    }

                    // 2. Container boundary breakout (child extending outside its parent box)
                    for (const el of all) {
                        const parent = el.parentElement;
                        if (!parent || parent.tagName === 'BODY' || parent.tagName === 'HTML') continue;
                        const pRect = parent.getBoundingClientRect();
                        const cRect = el.getBoundingClientRect();
                        const pStyle = window.getComputedStyle(parent);
                        if (pStyle.overflowX !== 'visible' || ['relative', 'static', 'flex', 'grid'].includes(pStyle.position)) {
                            if (cRect.right > pRect.right + 2 && pRect.width > 50) {
                                anomalies.push({
                                    type: 'container_breakout',
                                    element: getSelector(el),
                                    container: getSelector(parent),
                                    text: (el.innerText || '').slice(0, 50).trim(),
                                    details: `child right (${cRect.right.toFixed(1)}px) exceeds container right (${pRect.right.toFixed(1)}px) by ${(cRect.right - pRect.right).toFixed(1)}px`
                                });
                            }
                        }
                    }

                    // 3. Squished text / flex squishing
                    for (const el of all) {
                        if (['P', 'SPAN', 'DIV', 'LABEL'].includes(el.tagName)) {
                            const text = (el.innerText || '').trim();
                            const words = text.split(/\\s+/).length;
                            const cRect = el.getBoundingClientRect();
                            if (words >= 6 && cRect.width > 0 && cRect.width < 105 && cRect.height > 80) {
                                anomalies.push({
                                    type: 'squished_text',
                                    element: getSelector(el),
                                    text: text.slice(0, 50),
                                    details: `text with ${words} words compressed to width ${cRect.width.toFixed(1)}px (height ${cRect.height.toFixed(1)}px)`
                                });
                            }
                        }
                    }

                    // 4. Clipped scroll overflow
                    for (const el of all) {
                        const style = window.getComputedStyle(el);
                        if (['hidden', 'clip'].includes(style.overflowX) && el.scrollWidth > el.clientWidth + 2) {
                            anomalies.push({
                                type: 'clipped_overflow',
                                element: getSelector(el),
                                text: (el.innerText || '').slice(0, 50).trim(),
                                details: `scrollWidth (${el.scrollWidth}px) > clientWidth (${el.clientWidth}px)`
                            });
                        }
                    }

                    return anomalies.slice(0, 25);
                }
            """)

            browser.close()

        metadata = {
            "url": source.location,
            "final_url": final_url,
            "status_code": status_code,
            "title": title,
            "links": [{"url": l["url"], "text": l["text"], "kind": _link_kind(final_url, l["url"])} for l in links[:100]],
            "assets": [{"url": a["url"], "tag": a["tag"], "kind": _asset_kind(a)} for a in assets[:100]],
            "forms": forms[:25],
            "console_errors": console_errors[:50],
            "layout_anomalies": layout_anomalies,
            "network_calls": [{"url": n["url"], "method": n["method"], "resource_type": n["resource_type"]} for n in network_calls[:200]],
            "page_schema": {
                "url": final_url,
                "status_code": status_code,
                "title": title,
                "links": links[:100],
                "assets": assets[:100],
                "forms": forms[:25],
                "console_errors": console_errors[:50],
                "layout_anomalies": layout_anomalies,
                "network_calls": network_calls[:200],
            },
            "interfaces": [{"type": "browser_page", "location": final_url, "metadata": {"status_code": status_code, "title": title}}],
        }

        confidence = 95 if status_code and 200 <= status_code < 400 else 55
        evidence = [self.evidence("browser", source.location, f"Browser rendered {final_url} HTTP {status_code}")]
        return self.result(confidence, ["web_page", "browser_page"], evidence, metadata)

    def evidence(self, kind: str, location, detail: str = ""):
        from testql.discovery.manifest import Evidence
        return Evidence(self.name, kind, str(location), detail)


def _link_kind(base_url: str, href: str) -> str:
    from urllib.parse import urljoin, urlparse
    target = urljoin(base_url, href)
    base_host = urlparse(base_url).netloc
    target_host = urlparse(target).netloc
    if href.startswith("#"):
        return "anchor"
    if target_host and target_host != base_host:
        return "external"
    return "internal"


def _asset_kind(asset: dict[str, Any]) -> str:
    tag = asset.get("tag", "")
    rel = asset.get("rel", "")
    if tag == "script":
        return "script"
    if tag == "img":
        return "image"
    if tag == "link":
        rel_l = str(rel).lower()
        if "stylesheet" in rel_l:
            return "stylesheet"
        if "icon" in rel_l or "shortcut" in rel_l:
            return "icon"
        if "preload" in rel_l:
            return "preload"
        return "link"
    return "unknown"
