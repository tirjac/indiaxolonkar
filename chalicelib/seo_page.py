# -*- coding: utf-8 -*-
#
# @project indiaxolonkar
# @file chalicelib/seo_page.py
# @author  Shreos Roychowdhury <shreos@tirja.com>
# @version 1.0.0
# 
# @section DESCRIPTION
# 
#   seo_page.py : Share-page HTML renderer.
# 
# @section LICENSE
# 
# Copyright (c) 2026 Shreos Roychowdhury.
# Copyright (c) 2026 Tirja Consulting LLP.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 

import html


def render_share_page(caption, description, image_url, thumbnail_url, contact_type=None, contact_value=None, page_url=None):
	cap = (caption or "").strip()
	desc = (description or "").strip()
	img = image_url or ""
	thumb = thumbnail_url or image_url or ""
	page = page_url or ""

	buy_url = ""
	buy_label = "Buy"

	if contact_type == "product_url" and contact_value:
		buy_url = contact_value
		buy_label = "Buy Now"
	elif contact_type == "mobile_no" and contact_value:
		digits = "".join(ch for ch in contact_value if ch.isdigit() or ch == "+")
		if digits.startswith("+"):
			digits = digits[1:]
		buy_url = f"https://wa.me/{digits}" if digits else ""
		buy_label = "WhatsApp"

	title = html.escape(cap) if cap else "Product"
	desc_esc = html.escape(desc)
	img_esc = html.escape(img)
	thumb_esc = html.escape(thumb)
	buy_url_esc = html.escape(buy_url)
	buy_label_esc = html.escape(buy_label)

	button_html = ""
	if buy_url:
		button_html = f"<a class=\"btn\" href=\"{buy_url_esc}\" target=\"_blank\" rel=\"noopener\">{buy_label_esc}</a>"

	return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <meta name=\"description\" content=\"{desc_esc}\" />
  <meta property=\"og:type\" content=\"website\" />
  <meta property=\"og:title\" content=\"{title}\" />
  <meta property=\"og:description\" content=\"{desc_esc}\" />
  <meta property=\"og:image\" content=\"{img_esc}\" />
  <meta property=\"og:image:alt\" content=\"{title}\" />
  <meta property=\"og:url\" content=\"{html.escape(page)}\" />
  <meta name=\"twitter:card\" content=\"summary_large_image\" />
  <meta name=\"twitter:title\" content=\"{title}\" />
  <meta name=\"twitter:description\" content=\"{desc_esc}\" />
  <meta name=\"twitter:image\" content=\"{img_esc}\" />
  <link rel=\"icon\" href=\"{thumb_esc}\" />
  <style>
	body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #f7f7f7; color: #111; }}
	.wrap {{ max-width: 780px; margin: 0 auto; padding: 20px; }}
	.card {{ background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 8px 20px rgba(0,0,0,0.06); }}
	.title {{ font-size: 22px; margin: 0 0 8px 0; }}
	.desc {{ font-size: 15px; color: #444; }}
	.img {{ width: 100%; height: auto; border-radius: 10px; margin: 12px 0; }}
	.btn {{ display: inline-block; padding: 10px 14px; background: #1f8f5f; color: #fff; text-decoration: none; border-radius: 8px; font-weight: 600; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
	<div class=\"card\">
	  <h1 class=\"title\">{title}</h1>
	  <img class=\"img\" src=\"{img_esc}\" alt=\"{title}\" />
	  <p class=\"desc\">{desc_esc}</p>
	  {button_html}
	</div>
  </div>
</body>
</html>"""
