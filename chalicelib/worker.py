# -*- coding: utf-8 -*-
#
# @project indiaxolonkar
# @file chalicelib/worker.py
# @author  Shreos Roychowdhury <shreos@tirja.com>
# @version 1.0.0
# 
# @section DESCRIPTION
# 
#   worker.py : SQS worker: image + text generation, S3, task updates.
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

import json
import uuid
import base64
import io
from PIL import Image
from chalicelib.seo_page import render_share_page


class SqsWorker:
	def __init__(self, config, clients, tasks):
		self._config = config
		self._clients = clients
		self._tasks = tasks
		self._debug = bool(getattr(config, "DEBUG_MODE", False))

	def _log(self, msg):
		if self._debug:
			print(f"[worker] {msg}", flush=True)

	def _pad_to_square(self, img, background=(245, 245, 245)):
		width, height = img.size
		side = max(width, height)
		padded = Image.new("RGB", (side, side), background)
		left = (side - width) // 2
		top = (side - height) // 2
		padded.paste(img, (left, top))
		return padded

	def handle(self, event):
		for record in event:
			task_id = None
			try:
				payload = json.loads(record.body)
				task_id = payload.get("task_id")
				item = self._tasks.get_task(task_id)
				if not item:
					raise ValueError("Task not found")
				original_key = item.get("original_key")
				if not original_key:
					raise ValueError("original_key missing")
				content_type = item.get("content_type") or "image/png"
				objective = item.get("objective", "sales")
				comments = item.get("comments", "")
				category = item.get("category", "Others")

				self._log(f"start task_id={task_id}")
				self._tasks.update_task(task_id, {"status": "processing"})

				s3 = self._clients.boto3_client("s3")
				obj = s3.get_object(Bucket=self._config.S3_BUCKET, Key=original_key)
				image_bytes = obj["Body"].read()
				img_base64 = base64.b64encode(image_bytes).decode("utf-8")
				data_url = f"data:{content_type};base64,{img_base64}"

				prompt_image = (
					"Transform the product photo for higher ecommerce conversion. "
					f"Objective: {objective}. "
					f"Category: {category}. "
					"Output must be a 1:1 square image. "
					"WhatsApp-forward friendly; retail-grade, clean, premium. "
					"Keep the product itself visually accurate and recognizable. "
					"Interpret vague style instructions as changes to background, lighting, props, color theme, and composition rather than altering the product itself. "
					"Ensure the product remains the dominant subject occupying ~60-80% of the frame. "
					"Minimal text overlay, strong hierarchy. "
					"Do not add price or discount text unless explicitly requested in user notes. "
					f"User instructions: {comments or 'none'}. "
					"Return TWO outputs: (1) the transformed image and (2) JSON named grounding with fields: primary_product, material_if_visible, color_if_visible, scene_style."
				)
				prompt_text = (
					"Write high-quality ecommerce listing text for the product. "
					f"Objective: {objective}. "
					f"Category: {category}. "
					"Primary product is provided from grounding.primary_product. "
					"Ignore props or background objects when identifying the product. "
					"The caption MUST clearly name the product type from grounding.primary_product and must not change product category. "
					"Caption format rule: [style/material if visible] + primary_product. "
					"Use the canonical product term exactly once in the caption and do not replace it with synonyms. "
					"The caption must read like a natural ecommerce product title (clear, specific, human-sounding). "
					"Avoid generic filler phrases such as 'product', 'display', 'item', 'social type', or template-like wording. "
					"Caption length: ~4-8 words, title case, no emojis, no hashtags. "
					"Ensure the text matches the styling implied by the transformed image and the target audience. "
					"Do not invent specifications that are not visually evident. "
					"Do not add price or discount text unless explicitly requested in user notes. "
					f"User instructions: {comments or 'none'}. "
					"Return strict JSON with keys: caption, description, explanation. "
					"caption: concise ecommerce title following the caption format rule. "
					"description: 2-3 natural marketing sentences suitable for a product page. "
					"explanation: 3-5 short lines describing how the visual changes improve buyer decisions."
				)

				client = self._clients.get_openai()
				response = client.responses.create(
					model="gpt-5.2",
					input=[
						{
							"role": "user",
							"content": [
								{"type": "input_text", "text": prompt_image},
								{"type": "input_image", "image_url": data_url},
							],
						}
					],
					tools=[{"type": "image_generation"}],
				)

				image_data = []
				output_types = []
				for output in response.output:
					output_types.append(getattr(output, "type", "unknown"))
					if getattr(output, "type", "") in ("image_generation_call", "image_generation"):
						if hasattr(output, "result") and output.result:
							image_data.append(output.result)
						elif hasattr(output, "image_base64") and output.image_base64:
							image_data.append(output.image_base64)
				self._log(f"output_types={output_types}")
				if not image_data:
					raise ValueError(
						f"Image generation failed. output_types={output_types} text={response.output_text[:200]}"
					)

				transformed_bytes = base64.b64decode(image_data[0])
				# Ensure square output by padding, not cropping
				try:
					img_sq = Image.open(io.BytesIO(transformed_bytes))
					img_sq = img_sq.convert("RGB")
					img_sq = self._pad_to_square(img_sq)
					buf_sq = io.BytesIO()
					img_sq.save(buf_sq, format="PNG")
					transformed_bytes = buf_sq.getvalue()
				except Exception:
					pass

				transformed_key = f"transformed/{uuid.uuid4().hex}.png"
				s3.put_object(
					Bucket=self._config.S3_BUCKET,
					Key=transformed_key,
					Body=transformed_bytes,
					ContentType="image/png",
				)
				transformed_url = (
					f"https://{self._config.S3_BUCKET}.s3.{self._config.AWS_REGION}.amazonaws.com/{transformed_key}"
				)

				share_image_url = ""
				try:
					img = Image.open(io.BytesIO(transformed_bytes))
					img = img.convert("RGB")
					img = self._pad_to_square(img)
					max_dim = 1080
					if img.size[0] > max_dim:
						img = img.resize((max_dim, max_dim), Image.LANCZOS)

					target_bytes = 300 * 1024
					quality = 85
					buf = io.BytesIO()
					while True:
						buf.seek(0)
						buf.truncate(0)
						img.save(buf, format="JPEG", quality=quality, optimize=True)
						if buf.tell() <= target_bytes or quality <= 40:
							break
						quality -= 5

					if buf.tell() > target_bytes:
						new_dim = int(img.size[0] * 0.85)
						img = img.resize((new_dim, new_dim), Image.LANCZOS)
						quality = 70
						buf.seek(0)
						buf.truncate(0)
						img.save(buf, format="JPEG", quality=quality, optimize=True)

					share_img_key = f"share_img/{uuid.uuid4().hex}.jpg"
					s3.put_object(
						Bucket=self._config.S3_BUCKET,
						Key=share_img_key,
						Body=buf.getvalue(),
						ContentType="image/jpeg",
					)
					share_image_url = (
						f"https://{self._config.S3_BUCKET}.s3.{self._config.AWS_REGION}.amazonaws.com/{share_img_key}"
					)
				except Exception:
					share_image_url = ""

				thumbnail_url = None
				try:
					thumb_img = Image.open(io.BytesIO(transformed_bytes))
					thumb_img = thumb_img.convert("RGB")
					thumb_img = self._pad_to_square(thumb_img)
					thumb_img = thumb_img.resize((128, 128), Image.LANCZOS)
					thumb_buf = io.BytesIO()
					thumb_img.save(thumb_buf, format="JPEG", quality=85)
					thumb_key = f"thumbs/{uuid.uuid4().hex}.jpg"
					s3.put_object(
						Bucket=self._config.S3_BUCKET,
						Key=thumb_key,
						Body=thumb_buf.getvalue(),
						ContentType="image/jpeg",
					)
					thumbnail_url = (
						f"https://{self._config.S3_BUCKET}.s3.{self._config.AWS_REGION}.amazonaws.com/{thumb_key}"
					)
				except Exception:
					thumbnail_url = None

				grounding = {}
				grounding_primary = ""
				try:
					raw_ground = (response.output_text or "").strip()
					if raw_ground:
						clean_ground = raw_ground
						if clean_ground.startswith("```"):
							clean_ground = clean_ground.strip("`")
							if clean_ground.lower().startswith("json"):
								clean_ground = clean_ground[4:].strip()
						parsed_ground = json.loads(clean_ground)
						if isinstance(parsed_ground, dict):
							if "grounding" in parsed_ground and isinstance(parsed_ground["grounding"], dict):
								grounding = parsed_ground["grounding"]
							else:
								grounding = parsed_ground
				except Exception:
					grounding = {}

				grounding_primary = str(grounding.get("primary_product") or "").strip()
				if grounding_primary:
					prompt_text = prompt_text.replace(
						"grounding.primary_product",
						f"grounding.primary_product ({grounding_primary})",
					)

				transformed_b64 = base64.b64encode(transformed_bytes).decode("utf-8")
				transformed_data_url = f"data:image/png;base64,{transformed_b64}"

				text_response = client.responses.create(
					model="gpt-5.2",
					input=[
						{
							"role": "user",
							"content": [
								{"type": "input_text", "text": prompt_text},
								{"type": "input_image", "image_url": transformed_data_url},
							],
						}
					],
				)

				explanation_text = ""
				caption_text = ""
				description_text = ""
				raw_text = text_response.output_text.strip()
				try:
					clean = raw_text
					if clean.startswith("```"):
						clean = clean.strip("`")
						if clean.lower().startswith("json"):
							clean = clean[4:].strip()
					parsed = json.loads(clean)
					caption_text = (parsed.get("caption") or "").strip()
					description_text = (parsed.get("description") or "").strip()
					exp = parsed.get("explanation") or ""
					if isinstance(exp, list):
						explanation_text = "\n".join(
							[str(x).strip() for x in exp if str(x).strip()]
						)
					else:
						explanation_text = str(exp).strip()
				except Exception:
					explanation_text = raw_text

				if not explanation_text:
					explanation_text = (
						"Improved lighting, focus, and composition increase perceived quality and clarity."
					)

				share_url = ""
				try:
					share_key = f"share/{uuid.uuid4().hex}.html"
					share_url = (
						f"https://{self._config.S3_BUCKET}.s3.{self._config.AWS_REGION}.amazonaws.com/{share_key}"
					)
					share_html = render_share_page(
						caption_text,
						description_text,
						share_image_url or transformed_url,
						thumbnail_url,
						item.get("contact_type"),
						item.get("contact_value"),
						share_url,
					)
					s3.put_object(
						Bucket=self._config.S3_BUCKET,
						Key=share_key,
						Body=share_html.encode("utf-8"),
						ContentType="text/html",
					)
				except Exception:
					share_url = ""

				self._tasks.update_task(
					task_id,
					{
						"status": "completed",
						"transformed_url": transformed_url,
						"share_image_url": share_image_url,
						"thumbnail_url": thumbnail_url,
						"explanation": explanation_text,
						"caption": caption_text,
						"description": description_text,
						"share_url": share_url,
						"grounding": grounding,
					},
				)
				self._log(f"completed task_id={task_id}")
			except Exception as e:
				self._log(f"failed task_id={task_id} error={e}")
				self._tasks.update_task(task_id, {"status": "failed", "error": str(e)})
