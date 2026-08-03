from __future__ import annotations

import os
import sys
from typing import Callable, Dict, List, Optional
from .store import EmbeddingStore

def create_llm_fn(intent: str = "general") -> Callable[[str], str]:
    """
    Creates an LLM generation function with fallback chain:
    1. Gemini (GEMINI_API_KEY) -> models: gemini-3.1-flash, gemini-2.5-flash, gemini-2.0-flash
    2. DeepSeek (DEEPSEEK_API_KEY) -> models: deepseek-v4-flash, deepseek-chat, deepseek-reasoner
    3. OpenAI (OPENAI_API_KEY) -> models: o4-mini, gpt-4o-mini
    4. Offline RAG Synthesizer (Fallback)
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    # Intent-based system personas
    if intent == "seller":
        system_instruction = (
            "Bạn là Chuyên viên Pháp chế và Quy định Bán hàng Shopee Việt Nam. "
            "Giải thích chính xác các quy định đăng bán, hàng cấm/hạn chế, vi phạm và mức xử phạt cho Người bán. "
            "Trực diện, súc tích, đi thẳng vào câu trả lời. TUYỆT ĐỐI KHÔNG CHÀO HỎI, KHÔNG XƯNG LỜI MỞ ĐẦU."
        )
    elif intent == "buyer":
        system_instruction = (
            "Bạn là Chuyên viên Quyền lợi Người mua Shopee Việt Nam. "
            "Giải thích chính xác thời hạn trả hàng hoàn tiền, hình thức thanh toán, bảo mật thông tin. "
            "Trực diện, súc tích, đi thẳng vào câu trả lời. TUYỆT ĐỐI KHÔNG CHÀO HỎI, KHÔNG XƯNG LỜI MỞ ĐẦU."
        )
    else:
        system_instruction = (
            "Bạn là Chuyên viên Hỗ trợ Điều khoản và Chính sách Shopee Việt Nam. "
            "Cung cấp thông tin chính xác, ngắn gọn, cấu trúc rõ ràng. "
            "Trực diện, súc tích, đi thẳng vào câu trả lời. TUYỆT ĐỐI KHÔNG CHÀO HỎI, KHÔNG XƯNG LỜI MỞ ĐẦU."
        )

    # 1. Try Gemini API first
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            preferred_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash")
            candidate_models = [preferred_model, "gemini-2.5-flash", "gemini-2.0-flash"]
            
            for m_name in candidate_models:
                try:
                    model = genai.GenerativeModel(m_name, system_instruction=system_instruction)
                    res = model.generate_content("Ping")
                    if res and res.text:
                        def gemini_llm(prompt: str) -> str:
                            r = model.generate_content(prompt)
                            return r.text.strip() if (r and r.text) else ""
                        return gemini_llm
                except Exception:
                    continue
        except Exception as err:
            print(f"Warning: Gemini API init failed ({err}), trying DeepSeek...")

    # 2. Try DeepSeek API second
    if deepseek_key:
        try:
            from openai import OpenAI
            ds_client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
            preferred_ds = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
            ds_candidates = [preferred_ds, "deepseek-chat", "deepseek-reasoner"]

            for ds_m in ds_candidates:
                try:
                    def deepseek_llm(prompt: str) -> str:
                        response = ds_client.chat.completions.create(
                            model=ds_m,
                            messages=[
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                        )
                        return response.choices[0].message.content.strip()

                    test_res = deepseek_llm("Ping")
                    if test_res:
                        return deepseek_llm
                except Exception:
                    continue
        except Exception as err:
            print(f"Warning: DeepSeek API init failed ({err}), trying OpenAI...")

    # 3. Try OpenAI API third
    if openai_key and not openai_key.startswith("sk-proj-placeholder"):
        try:
            from openai import OpenAI
            oai_client = OpenAI(api_key=openai_key)
            preferred_oai = os.getenv("OPENAI_MODEL", "o4-mini")
            oai_candidates = [preferred_oai, "gpt-4o-mini", "gpt-4o"]

            for oai_m in oai_candidates:
                try:
                    def openai_llm(prompt: str) -> str:
                        response = oai_client.chat.completions.create(
                            model=oai_m,
                            messages=[
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                        )
                        return response.choices[0].message.content.strip()

                    test_res = openai_llm("Ping")
                    if test_res:
                        return openai_llm
                except Exception:
                    continue
        except Exception as err:
            print(f"Warning: OpenAI API init failed ({err}), falling back to Offline Synthesizer...")

    # 4. Offline RAG Synthesizer Fallback
    def offline_llm(prompt: str) -> str:
        return prompt

    return offline_llm


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Classify Intent & Customer Role.
        2. Retrieve top-k relevant chunks from the store.
        3. Build an intent-specific prompt with context.
        4. Call LLM (No greetings, direct answer).
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Optional[Callable[[str], str]] = None) -> None:
        self.store = store
        self._custom_llm_fn = llm_fn

    def _classify_intent(self, question: str, customer_role: Optional[str] = None) -> str:
        """Classifies query intent into seller, buyer, or general."""
        if customer_role == "seller":
            return "seller"
        if customer_role == "buyer":
            return "buyer"
            
        q_lower = question.lower()
        seller_keywords = ["đăng bán", "hàng cấm", "người bán", "xử phạt", "khóa tài khoản", "danh mục cấm", "kho bãi", "gian hàng"]
        buyer_keywords = ["trả hàng", "hoàn tiền", "trả tiền", "spaylater", "shopeepay", "bảo mật", "vận chuyển", "giao hàng", "cod", "phí ship"]

        if any(k in q_lower for k in seller_keywords):
            return "seller"
        if any(k in q_lower for k in buyer_keywords):
            return "buyer"
            
        return "general"

    def answer(
        self,
        question: str,
        top_k: int = 3,
        customer_role: Optional[str] = None,
        return_dict: bool = False,
    ) -> Union[str, dict[str, Any]]:
        """
        Retrieves context and generates a direct intent-based answer.
        Returns either a string answer or a dictionary with 'answer', 'sources', and 'results'.
        """
        # 1. Classify Intent
        intent = self._classify_intent(question, customer_role)

        # 2. Search with optional metadata filter
        filter_role = customer_role if customer_role in ("buyer", "seller") else (
            "seller" if intent == "seller" else ("buyer" if intent == "buyer" else None)
        )

        if filter_role:
            results = self.store.search_with_filter(
                question, top_k=top_k, metadata_filter={"customer_role": filter_role}
            )
            if not results: # Fallback search without filter if empty
                results = self.store.search(question, top_k=top_k)
        else:
            results = self.store.search(question, top_k=top_k)

        if not results:
            fallback_msg = "Hiện tại hệ thống chưa tìm thấy thông tin chính sách phù hợp cho câu hỏi này. Bạn có thể liên hệ Tổng đài Shopee 19001221 để được hỗ trợ."
            if return_dict:
                return {
                    "answer": fallback_msg,
                    "sources": [],
                    "results": []
                }
            return fallback_msg

        # 3. Build context blocks and sources metadata
        context_blocks = []
        sources = []
        for idx, item in enumerate(results, start=1):
            meta = item.get("metadata", {})
            doc_id = meta.get("doc_id", item.get("id", ""))
            title = meta.get("title", doc_id)
            score = item.get("score", 0.0)
            content = item.get("content", "")
            
            context_blocks.append(f"Tài liệu {idx} [{title}]:\n{content}")
            sources.append({
                "index": idx,
                "doc_id": doc_id,
                "title": title,
                "score": round(score, 4),
                "snippet": content[:300] + ("..." if len(content) > 300 else ""),
                "customer_role": meta.get("customer_role", "both"),
                "source_url": meta.get("source_url", ""),
            })

        context_str = "\n\n".join(context_blocks)
        
        # Intent-driven prompt engineering with STRICT NO GREETINGS RULE
        prompt = (
            f"=== THÔNG TIN CHÍNH SÁCH SHOPEE TRÍCH XUẤT ===\n{context_str}\n\n"
            f"=== CÂU HỎI ===\n{question}\n\n"
            f"=== QUY TẮC TRẢ LỜI CỐT LÕI ===\n"
            f"1. TUYỆT ĐỐI KHÔNG CHÀO HỎI, KHÔNG LỜI MỞ ĐẦU (KHÔNG dùng 'Dạ chào bạn', 'Xin chào', 'Cảm ơn bạn').\n"
            f"2. Đi thẳng trực tiếp vào câu trả lời, trả lời đúng trọng tâm vấn đề.\n"
            f"3. Nêu rõ các quy định, con số cụ thể (mốc thời gian 15 ngày, 24h, % phí, quy định xử phạt).\n"
            f"4. Trình bày dạng danh sách gạch đầu dòng Markdown chuẩn (dùng dấu gạch ngang '-' ở đầu mỗi dòng), in đậm từ khóa chính.\n"
            f"5. Không xưng 'Tôi là AI', không máy móc."
        )

        # 4. Get LLM Runner
        llm_runner = self._custom_llm_fn or create_llm_fn(intent=intent)
        llm_response = llm_runner(prompt)

        # Handle offline fallback if llm_runner returned raw prompt
        if llm_response == prompt or not llm_response:
            top_title = sources[0]["title"]
            top_content = results[0].get("content", "")
            lines = [l.strip() for l in top_content.split("\n") if l.strip() and not l.strip().startswith("#")][:6]
            
            answer = f"**{top_title}**:\n\n"
            for line in lines:
                if len(line) > 10:
                    answer += f"- {line}\n"
        else:
            answer = llm_response

        if return_dict:
            return {
                "answer": answer,
                "sources": sources,
                "results": results
            }
        return answer
