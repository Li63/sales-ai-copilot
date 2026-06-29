import html
import re
from dataclasses import asdict, dataclass
from urllib.parse import urljoin

import httpx


DOUYIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


@dataclass
class DouyinLinkEvidence:
    status: str
    source_url: str
    final_url: str = ""
    video_id: str = ""
    title: str = ""
    description: str = ""
    cover_url: str = ""
    redirect_chain: list[str] | None = None
    missing_fields: list[str] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class DouyinLinkResolver:
    def __init__(self, http_client: httpx.AsyncClient | None = None):
        self.http_client = http_client

    async def resolve(self, url: str) -> DouyinLinkEvidence:
        source_url = (url or "").strip()
        if not source_url:
            return DouyinLinkEvidence(status="failed", source_url=source_url, missing_fields=["链接"])
        client = self.http_client or httpx.AsyncClient(headers=DOUYIN_HEADERS, timeout=8.0, follow_redirects=False)
        should_close = self.http_client is None
        chain: list[str] = []
        html_text = ""
        current_url = source_url
        try:
            for _ in range(6):
                chain.append(current_url)
                response = await client.get(current_url, headers=DOUYIN_HEADERS)
                location = response.headers.get("location")
                if response.status_code in {301, 302, 303, 307, 308} and location:
                    current_url = urljoin(str(response.url), html.unescape(location))
                    continue
                html_text = response.text or ""
                current_url = str(response.url)
                if not chain or chain[-1] != current_url:
                    chain.append(current_url)
                break
            video_id = _extract_video_id("\n".join([*chain, current_url]))
            title = _extract_meta(html_text, ["og:title", "twitter:title"]) or _extract_title(html_text)
            description = _extract_meta(html_text, ["description", "og:description", "twitter:description"])
            cover_url = _extract_meta(html_text, ["og:image", "twitter:image"])
            if video_id and not (title and description and cover_url):
                iteminfo = await _fetch_public_iteminfo(client, video_id, current_url)
                title = title or iteminfo.get("title", "")
                description = description or iteminfo.get("description", "")
                cover_url = cover_url or iteminfo.get("cover_url", "")
            missing = [
                label
                for label, value in {
                    "标题": title,
                    "简介": description,
                    "封面": cover_url,
                    "评论": "",
                    "作者": "",
                }.items()
                if not value
            ]
            status = "resolved" if video_id and (title or description or cover_url) else "partial" if video_id or current_url != source_url else "failed"
            return DouyinLinkEvidence(
                status=status,
                source_url=source_url,
                final_url=current_url,
                video_id=video_id,
                title=title,
                description=description,
                cover_url=cover_url,
                redirect_chain=chain,
                missing_fields=missing,
            )
        except Exception:
            return DouyinLinkEvidence(status="failed", source_url=source_url, redirect_chain=chain, missing_fields=["公开页面"])
        finally:
            if should_close:
                await client.aclose()


def format_douyin_link_evidence(evidence: DouyinLinkEvidence | dict | None) -> str:
    if not evidence:
        return ""
    data = evidence.to_dict() if isinstance(evidence, DouyinLinkEvidence) else evidence
    if data.get("status") == "failed":
        return (
            "解析方式：抖音公开链接解析\n"
            f"原始链接：{data.get('source_url', '')}\n"
            "解析状态：公开链接暂未解析成功，需要销售补充截图或分享文案。"
        )
    lines = [
        "解析方式：抖音公开链接解析",
        f"解析状态：{data.get('status', 'partial')}",
        f"原始链接：{data.get('source_url', '')}",
        f"最终链接：{data.get('final_url', '')}",
        f"视频ID：{data.get('video_id', '')}",
        f"作品标题：{data.get('title', '')}",
        f"作品简介：{data.get('description', '')}",
        f"封面链接：{data.get('cover_url', '')}",
    ]
    missing = data.get("missing_fields") or []
    if missing:
        lines.append(f"未获取字段：{'、'.join(missing)}")
        lines.append("证据提醒：不能把未获取字段当成事实；缺少评论/作者/主页时，应继续上传截图或粘贴分享文案补证据。")
    return "\n".join(line for line in lines if not line.endswith("："))


def _extract_video_id(text: str) -> str:
    for pattern in [r"/video/(\d+)", r"/share/video/(\d+)"]:
        matched = re.search(pattern, text or "")
        if matched:
            return matched.group(1)
    return ""


async def _fetch_public_iteminfo(client: httpx.AsyncClient, video_id: str, referer: str) -> dict:
    urls = [
        f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}",
        f"https://www.douyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}",
    ]
    for url in urls:
        try:
            response = await client.get(url, headers={**DOUYIN_HEADERS, "Referer": referer, "Accept": "application/json,text/plain,*/*"})
            data = response.json()
        except Exception:
            continue
        if data.get("status_code") != 0 or not data.get("item_list"):
            continue
        item = data["item_list"][0] or {}
        author = item.get("author") or {}
        video = item.get("video") or {}
        cover = video.get("cover") or video.get("origin_cover") or {}
        cover_urls = cover.get("url_list") or []
        nickname = (author.get("nickname") or "").strip()
        return {
            "title": (item.get("desc") or "").strip(),
            "description": f"作者：{nickname}" if nickname else "",
            "cover_url": cover_urls[0] if cover_urls else "",
        }
    return {}


def _extract_title(text: str) -> str:
    matched = re.search(r"<title[^>]*>(.*?)</title>", text or "", re.IGNORECASE | re.DOTALL)
    if not matched:
        return ""
    return html.unescape(re.sub(r"\s+", " ", matched.group(1)).strip())


def _extract_meta(text: str, names: list[str]) -> str:
    for name in names:
        escaped = re.escape(name)
        patterns = [
            rf"<meta[^>]+(?:property|name)=[\"']{escaped}[\"'][^>]+content=[\"']([^\"']+)[\"'][^>]*>",
            rf"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+(?:property|name)=[\"']{escaped}[\"'][^>]*>",
        ]
        for pattern in patterns:
            matched = re.search(pattern, text or "", re.IGNORECASE | re.DOTALL)
            if matched:
                return html.unescape(re.sub(r"\s+", " ", matched.group(1)).strip())
    return ""
