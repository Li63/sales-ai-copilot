from app.services.transcript_parser import parse_transcript


def test_parse_transcript_recognizes_customer_and_sales_prefixes():
    messages = parse_transcript(
        "客户：价格多少钱？\n销售：标准版一年 9800。\n客户：能优惠吗？",
        sales_userid="sales-1",
        external_userid="external-1",
    )

    assert [item.from_user for item in messages] == ["external-1", "sales-1", "external-1"]
    assert messages[0].content == "价格多少钱？"
    assert messages[1].content == "标准版一年 9800。"


def test_parse_transcript_treats_unprefixed_lines_as_customer_messages():
    messages = parse_transcript(
        "价格有点贵\n有没有同行案例？",
        sales_userid="sales-1",
        external_userid="external-1",
    )

    assert len(messages) == 2
    assert all(item.from_user == "external-1" for item in messages)


def test_parse_transcript_skips_empty_lines_and_caps_content():
    messages = parse_transcript(
        "\n我：您好\n\n对方：" + "功能" * 300,
        sales_userid="sales-1",
        external_userid="external-1",
    )

    assert len(messages) == 2
    assert messages[0].from_user == "sales-1"
    assert len(messages[1].content) <= 500
