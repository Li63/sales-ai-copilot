import pytest
import httpx

from app.services.douyin_resolver import DouyinLinkResolver, format_douyin_link_evidence


@pytest.mark.asyncio
async def test_douyin_resolver_follows_short_link_and_extracts_public_metadata():
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.host == "v.douyin.com":
            return httpx.Response(
                302,
                headers={"location": "https://www.iesdouyin.com/share/video/7656390840890654457/?from_ssr=1"},
            )
        if request.url.host == "www.iesdouyin.com":
            return httpx.Response(302, headers={"location": "https://www.douyin.com/video/7656390840890654457"})
        return httpx.Response(
            200,
            text="""
            <html>
              <head>
                <title>瓜果蔬菜萝卜切条机 - 抖音</title>
                <meta property="og:title" content="金林食品机械设备厂家的作品：瓜果蔬菜萝卜切条机" />
                <meta name="description" content="瓜果蔬菜萝卜切条机 #萝卜切条机 #果蔬推条机" />
                <meta property="og:image" content="https://example.test/cover.jpg" />
              </head>
            </html>
            """,
        )

    resolver = DouyinLinkResolver(http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    evidence = await resolver.resolve("https://v.douyin.com/VhrrmUHw3SM/")

    assert requests[0] == "https://v.douyin.com/VhrrmUHw3SM/"
    assert evidence.status == "resolved"
    assert evidence.video_id == "7656390840890654457"
    assert evidence.final_url == "https://www.douyin.com/video/7656390840890654457"
    assert evidence.title == "金林食品机械设备厂家的作品：瓜果蔬菜萝卜切条机"
    assert evidence.description == "瓜果蔬菜萝卜切条机 #萝卜切条机 #果蔬推条机"
    assert evidence.cover_url == "https://example.test/cover.jpg"


def test_format_douyin_link_evidence_keeps_resolved_facts_separate_from_missing_fields():
    evidence = {
        "status": "partial",
        "source_url": "https://v.douyin.com/VhrrmUHw3SM/",
        "final_url": "https://www.douyin.com/video/7656390840890654457",
        "video_id": "7656390840890654457",
        "title": "",
        "description": "",
        "cover_url": "",
        "redirect_chain": ["https://v.douyin.com/VhrrmUHw3SM/", "https://www.douyin.com/video/7656390840890654457"],
        "missing_fields": ["标题", "作者", "评论"],
    }

    formatted = format_douyin_link_evidence(evidence)

    assert "解析方式：抖音公开链接解析" in formatted
    assert "视频ID：7656390840890654457" in formatted
    assert "最终链接：https://www.douyin.com/video/7656390840890654457" in formatted
    assert "未获取字段：标题、作者、评论" in formatted
    assert "不能把未获取字段当成事实" in formatted


@pytest.mark.asyncio
async def test_douyin_resolver_uses_public_iteminfo_when_page_metadata_is_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "v.douyin.com":
            return httpx.Response(302, headers={"location": "https://www.douyin.com/video/7656390840890654457"})
        if "iteminfo" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "status_code": 0,
                    "item_list": [
                        {
                            "desc": "瓜果蔬菜萝卜切条机 #萝卜切条机",
                            "author": {"nickname": "金林食品机械设备厂家"},
                            "video": {"cover": {"url_list": ["https://example.test/item-cover.jpg"]}},
                        }
                    ],
                },
            )
        return httpx.Response(200, text="<html><body></body></html>")

    resolver = DouyinLinkResolver(http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    evidence = await resolver.resolve("https://v.douyin.com/VhrrmUHw3SM/")

    assert evidence.status == "resolved"
    assert evidence.title == "瓜果蔬菜萝卜切条机 #萝卜切条机"
    assert evidence.description == "作者：金林食品机械设备厂家"
    assert evidence.cover_url == "https://example.test/item-cover.jpg"
