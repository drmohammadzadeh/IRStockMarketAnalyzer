"""Zero-Dependency Local Web Server & API for Iranian Stock Market Analyzer.

Author: alimohammadzadeh@ut.ac.ir
Website: tjb24.ir
Role: Serves static browser app files and provides /api/reanalyze endpoint
for single-stock isolated pipeline execution.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import threading
import urllib.error
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Union

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.orchestrator import MultiAgentOrchestrator
from src.agents.frontend_agent import FrontendAgent
from src.auth_db import AuthManager


class ReanalyzeRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler that serves the browser UI and provides the /api/reanalyze endpoint."""

    pipeline_lock = threading.Lock()
    directory = str(Path(__file__).resolve().parent / "browser")
    orchestrator = None
    frontend_agent = None
    auth_mgr = AuthManager()

    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = getattr(
                self.__class__,
                "directory",
                str(Path(__file__).resolve().parent / "browser"),
            )
        super().__init__(*args, directory=str(directory), **kwargs)

    def _send_json_response(self, status_code: int, data: Dict[str, Any]) -> None:
        """Sends a JSON response with proper headers and CORS support."""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Dict[str, Any]:
        """Safely reads and decodes JSON from request body."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        try:
            raw = self.rfile.read(content_length).decode("utf-8")
            if not raw.strip():
                return {}
            return json.loads(raw)
        except Exception:
            return {}

    def _get_auth_token(self) -> Optional[str]:
        """Extracts auth token from Authorization header or cookie or query param."""
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        # Cookie check
        cookie_header = self.headers.get("Cookie", "")
        if "session_token=" in cookie_header:
            for part in cookie_header.split(";"):
                part = part.strip()
                if part.startswith("session_token="):
                    return part.split("=", 1)[1].strip()
        return None

    def do_OPTIONS(self) -> None:
        """Handles CORS preflight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self) -> None:
        """Handles GET requests: handles auth/requests APIs, otherwise serves static assets."""
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path.rstrip("/")
        query_params = urllib.parse.parse_qs(parsed.query)

        if clean_path in ("/api/auth_check", "/api/auth_check.php"):
            token = self._get_auth_token()
            if not token and "token" in query_params:
                token = query_params["token"][0]
            user = self.auth_mgr.get_user_by_session(token)
            self._send_json_response(200, {"logged_in": bool(user), "user": user})
            return

        if clean_path in ("/api/activate", "/api/activate.php"):
            token = query_params.get("token", [""])[0]
            mobile = query_params.get("mobile", [""])[0]
            code = query_params.get("code", [""])[0]
            ok, msg, data = self.auth_mgr.activate(token=token, mobile=mobile, code=code)
            status = 200 if ok else 400
            self._send_json_response(status, {"success": ok, "message": msg, **data})
            return

        if clean_path in ("/api/user_requests", "/api/user_requests.php"):
            token = self._get_auth_token()
            user = self.auth_mgr.get_user_by_session(token)
            mobile = query_params.get("mobile", [""])[0] or (user["mobile"] if user else None)
            email = query_params.get("email", [""])[0] or (user["email"] if user else None)
            user_id = user["id"] if user else None
            reqs = self.auth_mgr.get_requests(user_id=user_id, mobile=mobile, email=email)
            self._send_json_response(200, {"success": True, "count": len(reqs), "requests": reqs})
            return

        if clean_path == "/api/reanalyze":
            self._send_json_response(
                405,
                {
                    "success": False,
                    "error": "Method Not Allowed. Use POST to trigger reanalysis.",
                },
            )
            return

        super().do_GET()

    def do_POST(self) -> None:
        """Handles POST requests for Auth, Analysis Requests, and Reanalyze."""
        parsed = urllib.parse.urlparse(self.path)
        clean_path = parsed.path.rstrip("/")

        # Auth Endpoints
        if clean_path in ("/api/register", "/api/register.php"):
            payload = self._read_json_body()
            ok, msg, data = self.auth_mgr.register(
                payload.get("first_name", ""),
                payload.get("last_name", ""),
                payload.get("mobile", ""),
                payload.get("email", ""),
                payload.get("password", "")
            )
            status = 201 if ok else 400
            self._send_json_response(status, {"success": ok, "message": msg, **data})
            return

        if clean_path in ("/api/activate", "/api/activate.php"):
            payload = self._read_json_body()
            ok, msg, data = self.auth_mgr.activate(
                token=payload.get("token"),
                mobile=payload.get("mobile"),
                code=payload.get("code")
            )
            status = 200 if ok else 400
            self._send_json_response(status, {"success": ok, "message": msg, **data})
            return

        if clean_path in ("/api/login", "/api/login.php"):
            payload = self._read_json_body()
            username = payload.get("username") or payload.get("mobile")
            password = payload.get("password")
            ok, msg, data = self.auth_mgr.login(username, password)
            status = 200 if ok else (403 if data.get("need_activation") else 401)
            self._send_json_response(status, {"success": ok, "message": msg, **data})
            return

        if clean_path in ("/api/logout", "/api/logout.php"):
            token = self._get_auth_token()
            self.auth_mgr.logout(token)
            self._send_json_response(200, {"success": True, "message": "با موفقیت از حساب کاربری خارج شدید."})
            return

        if clean_path in ("/api/forgot_password", "/api/forgot_password.php"):
            payload = self._read_json_body()
            identifier = payload.get("identifier") or payload.get("mobile") or payload.get("email")
            ok, msg, data = self.auth_mgr.forgot_password(identifier)
            status = 200 if ok else 404
            self._send_json_response(status, {"success": ok, "message": msg, **data})
            return

        if clean_path in ("/api/reset_password", "/api/reset_password.php"):
            payload = self._read_json_body()
            new_pwd = payload.get("new_password") or payload.get("password")
            ok, msg = self.auth_mgr.reset_password(
                new_pwd,
                token=payload.get("token"),
                mobile=payload.get("mobile"),
                code=payload.get("code")
            )
            status = 200 if ok else 400
            self._send_json_response(status, {"success": ok, "message": msg})
            return

        if clean_path in ("/api/user_requests", "/api/user_requests.php", "/api/submit_request.php", "/api/submit_request"):
            payload = self._read_json_body()
            token = self._get_auth_token()
            user = self.auth_mgr.get_user_by_session(token)
            sym = payload.get("stock_symbol") or payload.get("symbol")
            name = payload.get("applicant_name") or payload.get("name") or (f"{user['first_name']} {user['last_name']}" if user else "کاربر سامانه")
            email = payload.get("applicant_email") or payload.get("email") or (user["email"] if user else "no-reply@tjb24.ir")
            mobile = payload.get("applicant_mobile") or payload.get("mobile") or (user["mobile"] if user else None)
            rtype = payload.get("request_type") or "تحلیل بنیادی و تکنیکال"
            notes = payload.get("notes") or ""
            uid = user["id"] if user else None
            ok, msg, rid = self.auth_mgr.add_request(sym, name, email, mobile, rtype, notes, uid)
            status = 201 if ok else 400
            self._send_json_response(status, {"success": ok, "message": msg, "request_id": rid})
            return

        if clean_path in ("/api/live_reporter_init", "/api/live_reporter_init.php"):
            self.handle_live_reporter_init()
            return

        if clean_path in ("/api/live_reporter_chat", "/api/live_reporter_chat.php"):
            self.handle_live_reporter_chat()
            return

        if clean_path in ("/api/live_analyst", "/api/live_analyst.php"):
            self.handle_live_analyst()
            return

        if clean_path != "/api/reanalyze":
            self.send_error(404, "Endpoint not found")
            return

        symbol = None

        # 1. Check query parameter (?symbol=...)
        query_params = urllib.parse.parse_qs(parsed.query)
        if "symbol" in query_params and query_params["symbol"]:
            symbol = query_params["symbol"][0]

        # 2. Check request body if symbol not found in query params
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw_body = self.rfile.read(content_length)
            content_type = self.headers.get("Content-Type", "").lower()
            if not symbol:
                try:
                    if "application/json" in content_type:
                        body_json = json.loads(raw_body.decode("utf-8"))
                        if isinstance(body_json, dict):
                            symbol = body_json.get("symbol")
                    else:
                        decoded = raw_body.decode("utf-8").strip()
                        if decoded.startswith("{"):
                            body_json = json.loads(decoded)
                            if isinstance(body_json, dict):
                                symbol = body_json.get("symbol")
                        else:
                            form_params = urllib.parse.parse_qs(decoded)
                            if "symbol" in form_params and form_params["symbol"]:
                                symbol = form_params["symbol"][0]
                except Exception:
                    pass

        if symbol is not None:
            symbol = urllib.parse.unquote(str(symbol)).strip()

        if not symbol:
            self._send_json_response(
                400,
                {
                    "success": False,
                    "error": "Symbol parameter is missing or empty. Provide ?symbol=... or {'symbol': '...'}.",
                },
            )
            return

        # Execute pipeline under thread lock
        try:
            with self.pipeline_lock:
                orch = self._get_orchestrator()
                fe = self._get_frontend_agent()

                success = orch.run_pipeline(symbol)
                if not success:
                    self._send_json_response(
                        500,
                        {
                            "success": False,
                            "symbol": symbol,
                            "error": f"Pipeline analysis failed for symbol '{symbol}'.",
                        },
                    )
                    return

                stock_data = fe.update_single_stock(symbol)
                self._send_json_response(
                    200,
                    {
                        "success": True,
                        "symbol": symbol,
                        "stock": stock_data,
                        "message": f"Successfully reanalyzed {symbol}.",
                    },
                )
        except Exception as exc:
            self._send_json_response(
                500,
                {
                    "success": False,
                    "symbol": symbol,
                    "error": str(exc),
                },
            )

    def handle_live_analyst(self) -> None:
        """Handles POST /api/live_analyst requests using GeminiClient."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}

            prompt = payload.get("prompt", "")
            system_instruction = payload.get("systemInstruction", "")
            if not prompt:
                self._send_json_response(400, {"success": False, "error": "Prompt is required."})
                return

            from src.ai.gemini_client import GeminiClient
            client = GeminiClient()
            result_text = client.generate(prompt=prompt, system_instruction=system_instruction)

            if result_text:
                self._send_json_response(200, {"success": True, "text": result_text})
            else:
                self._send_json_response(500, {"success": False, "error": "Gemini returned empty response."})
        except Exception as e:
            self._send_json_response(500, {"success": False, "error": str(e)})

    def handle_live_reporter_init(self) -> None:
        """Handles POST /api/live_reporter_init:
        1. Extracts latest trading data from TSETMC & Rahavard 365 for current day.
        2. Cross-checks prices to verify accuracy.
        3. Generates concise studio analysis text.
        4. Synthesizes studio WAV audio using GeminiClient.
        """
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            symbol = payload.get("symbol", "").strip()

            if not symbol:
                self._send_json_response(400, {"success": False, "error": "Symbol is required."})
                return

            from src.data.tsetmc_fetcher import TSETMCFetcher
            from src.data.rahavard_fetcher import RahavardFetcher
            from src.ai.gemini_client import GeminiClient

            tf = TSETMCFetcher()
            rf = RahavardFetcher()
            gemini = GeminiClient()

            # 1. Fetch TSETMC
            t_data = tf.fetch_symbol_data(symbol)
            live = t_data.get("live_info", {})
            client_type = t_data.get("client_type", {})

            close_p = live.get("close_price") or live.get("last_price")
            last_p = live.get("last_price") or close_p
            yest_p = live.get("yesterday_price") or close_p
            vol = live.get("volume", 0)
            trades = live.get("trades", 0)

            # 2. Fetch Rahavard
            aid = rf.get_asset_id(symbol)
            r_data = rf.fetch_asset_data(aid) if aid else {}
            r_prices = rf.extract_prices(r_data)
            r_close = r_prices.get("close_price")
            r_last = r_prices.get("last_price")
            chg_pct = r_prices.get("close_change_percent")

            if chg_pct is None and close_p and yest_p and yest_p > 0:
                chg_pct = round(((close_p - yest_p) / yest_p) * 100.0, 2)

            # 3. Cross-check
            audit = rf.cross_check_price(close_p, r_close)

            # Format volume
            vol_str = f"{vol:,.0f}" if vol else "—"
            if vol and vol >= 1_000_000_000:
                vol_str = f"{vol / 1_000_000_000:.1f}B"
            elif vol and vol >= 1_000_000:
                vol_str = f"{vol / 1_000_000:.1f}M"
            elif vol and vol >= 1_000:
                vol_str = f"{vol / 1_000:.1f}K"

            buyer_power = client_type.get("buyer_power", 1.0)
            if buyer_power:
                buyer_power = round(float(buyer_power), 2)

            final_close = close_p or r_close or 0.0
            final_last = last_p or r_last or final_close
            final_chg = chg_pct if chg_pct is not None else 0.0

            stock_info = {
                "symbol": symbol,
                "close_price": final_close,
                "last_price": final_last,
                "change_percent": final_chg,
                "volume": vol,
                "volume_str": vol_str,
                "buyer_power": buyer_power,
                "trades": trades,
                "cross_check": audit,
            }

            # Update stocks.json and stocks.js on disk
            try:
                browser_data_dir = Path(__file__).resolve().parent / "browser" / "data"
                stocks_json_path = browser_data_dir / "stocks.json"
                stocks_js_path = browser_data_dir / "stocks.js"
                if stocks_json_path.exists():
                    with open(stocks_json_path, "r", encoding="utf-8") as f:
                        stocks_list = json.load(f)
                    for item in stocks_list:
                        if item.get("symbol") == symbol:
                            item["current_price"] = final_close
                            item["change_percent"] = final_chg
                            item["volume"] = vol_str
                            item["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            break
                    with open(stocks_json_path, "w", encoding="utf-8") as f:
                        json.dump(stocks_list, f, ensure_ascii=False, indent=2)
                    with open(stocks_js_path, "w", encoding="utf-8") as f:
                        f.write(f"window.STOCKS_DATA = {json.dumps(stocks_list, ensure_ascii=False, indent=2)};\n")
            except Exception:
                pass

            # Load contextual reports (Technical, Fundamental, Rahavard comments)
            stock_dir = Path(__file__).resolve().parent / "سهام" / symbol
            tech_summary = ""
            tech_file = stock_dir / "technical_report.md"
            if tech_file.exists():
                try:
                    tech_summary = tech_file.read_text(encoding="utf-8", errors="ignore")[:1000]
                except Exception:
                    pass

            fund_summary = ""
            fund_file = stock_dir / "fundamental_report.md"
            if fund_file.exists():
                try:
                    fund_summary = fund_file.read_text(encoding="utf-8", errors="ignore")[:1000]
                except Exception:
                    pass

            social_summary = ""
            soc_file = stock_dir / "news" / "social_sentiment.json"
            if soc_file.exists():
                try:
                    social_summary = soc_file.read_text(encoding="utf-8", errors="ignore")[:800]
                except Exception:
                    pass

            rahavard_comments_text = ""
            if social_summary:
                rahavard_comments_text = f"خلاصه نظرات و سنتیمنت کاربران در ره‌آورد ۳۶۵ و شبکه‌های اجتماعی:\n{social_summary}"

            # 4. Generate comprehensive 3-paragraph summary report text with Gemini
            prompt = (
                f"گزارش جامع تابلوی معاملات برای نماد {symbol}:\n"
                f"اطلاعات معاملات امروز: قیمت پایانی {final_close:,.0f} ریال ({final_chg:+0.2f}%) | حجم: {vol_str} | قدرت خریدار حقیقی: {buyer_power} برابر | وضعیت راستی‌آزمایی: {audit.get('message', 'تایید شده')}\n\n"
                f"خلاصه گزارش تکنیکال سهم:\n{tech_summary}\n\n"
                f"خلاصه گزارش بنیادی سهم:\n{fund_summary}\n\n"
                f"{rahavard_comments_text}\n\n"
                f"دستورالعمل:\n"
                f"به عنوان تحلیل‌گر ارشد بازار سرمایه، یک گزارش تحلیلی موثق، متین و دقیق در ۳ پاراگراف مجزا و کامل به شرح زیر ارائه بده:\n"
                f"- پاراگراف اول: تحلیل موشکافانه تابلوی معاملات، قیمت پایانی، حجم معاملات امروز و نسبت ورود پول و برتری قدرت خریداران حقیقی.\n"
                f"- پاراگراف دوم: ارزیابی ساختار تکنیکال سهم، میانگین‌های متحرک، ابر کومو (ایچیموکو) و سطوح کلیدی حمایت و مقاومت پیش‌رو.\n"
                f"- پاراگراف سوم: بررسی ارزندگی بنیادی شرکت، بازتاب نظرات سهامداران در کامنت‌های ره‌آورد ۳۶۵ و نتیجه‌گیری راهبردی برای معاملات.\n\n"
                f"قوانین نگارش:\n"
                f"۱. حجم متن باید مفصل و حداقل ۳ پاراگراف کامل و مجزا باشد.\n"
                f"۲. لحن باید کاملاً فارسی روان، استوار، پرانرژی و شنیدنی باشد.\n"
                f"۳. از ستاره (*)، هشتگ و علائم مارک‌داون استفاده نکن تا متن مناسب برای خوانش صوتی باشد.\n"
                f"۴. از بکار بردن اصطلاحات تکراری یا القاب استودیویی خودداری کن."
            )

            system_instruction = (
                "تو تحلیل‌گر ارشد بازار سرمایه ایران هستی. تحلیل خود را در ۳ پاراگراف مجزا، فاخر، دقیق، بدون مارک‌داون و کاملاً فارسی بیان کن."
            )

            analysis_text = gemini.generate(prompt=prompt, system_instruction=system_instruction)
            if not analysis_text:
                analysis_text = (
                    f"نماد {symbol} در معاملات امروز با آخرین قیمت {final_close:,.0f} ریال و تغییر {final_chg:+0.2f} درصد کار خود را دنبال کرد. حجم معاملات به {vol_str} برگه سهم رسید و نسبت قدرت خریداران حقیقی با ثبت عدد {buyer_power} برابر، از ورود معنادار پول و تمایل خریداران به جمع‌آوری سهم حکایت دارد.\n\n"
                    f"از منظر تحلیل تکنیکال، قیمت بالاتر از میانگین‌های متحرک کلیدی تثبیت شده و در کانال صعودی با حمایت‌های معتبر در حرکت است. با رصد ساختار امواج و موقعیت ابر کومو، حفظ سطوح حمایتی فعلی می‌تواند هدف‌های بالاتر را در دسترس قرار دهد، هرچند که در نزدیکی مقاومت‌های کوتاه‌مدت احتیاط و مدیریت ریسک ضروری است.\n\n"
                    f"از دیدگاه بنیادی و رصد نظرات سهامداران در ره‌آورد ۳۶۵، خوش‌بینی نسبی و انتظار بهبود سودآوری شرکت مشهود است. داده‌ها از سامانه‌های TSETMC و ره‌آورد ۳۶۵ استخراج و تطبیق داده شدند و پیشنهاد می‌شود تا زمان تثبیت کامل بالای مقاومت، از استراتژی پله‌ای استفاده شود."
                )

            # 5. Synthesize speech WAV
            audio_b64 = gemini.generate_speech(analysis_text)

            self._send_json_response(200, {
                "success": True,
                "symbol": symbol,
                "stock": stock_info,
                "analysis_text": analysis_text,
                "audio_base64": audio_b64 or "",
            })
        except Exception as e:
            self._send_json_response(500, {"success": False, "error": str(e)})

    def handle_live_reporter_chat(self) -> None:
        """Handles POST /api/live_reporter_chat:
        Answers user's voice question via GeminiClient and synthesizes speech.
        """
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}

            symbol = payload.get("symbol", "").strip()
            question = payload.get("question", "").strip()
            market_context = payload.get("market_context", "").strip()

            if not question:
                self._send_json_response(400, {"success": False, "error": "Question is required."})
                return

            from src.ai.gemini_client import GeminiClient
            gemini = GeminiClient()

            prompt = (
                f"کاربر درباره نماد {symbol} این سوال را مطرح کرده است:\n«{question}»\n\n"
                f"اطلاعات تابلوی نماد:\n{market_context}\n\n"
                f"به عنوان تحلیل‌گر ارشد بورس، در ۲ الی ۳ جمله رسا، روشن و فارسی به صورت مستقیم و بدون مقدمه‌چینی به سوال پاسخ بده. بدون ستاره و مارک‌داون."
            )

            system_instruction = "تو تحلیل‌گر ارشد بازار سرمایه هستی. پاسخ کوتاه، دقیق، فارسی و حرفه‌ای بده."

            answer_text = gemini.generate(prompt=prompt, system_instruction=system_instruction)
            if not answer_text:
                answer_text = f"با توجه به وضعیت فعلی تابلوی نماد {symbol} و حجم معاملات، توصیه می‌شود نسبت قدرت خریدار و ورود پول هوشمند را در دقایق آتی زیر نظر داشته باشید."

            audio_b64 = gemini.generate_speech(answer_text)

            self._send_json_response(200, {
                "success": True,
                "answer_text": answer_text,
                "audio_base64": audio_b64 or "",
            })
        except Exception as e:
            self._send_json_response(500, {"success": False, "error": str(e)})


    def _get_orchestrator(self) -> Any:
        """Retrieves or creates an orchestrator instance."""
        if self.orchestrator is not None:
            return self.orchestrator
        server_orch = getattr(self.server, "orchestrator", None)
        if server_orch is not None:
            return server_orch
        return MultiAgentOrchestrator()

    def _get_frontend_agent(self) -> Any:
        """Retrieves or creates a frontend agent instance."""
        if self.frontend_agent is not None:
            return self.frontend_agent
        server_fe = getattr(self.server, "frontend_agent", None)
        if server_fe is not None:
            return server_fe
        return FrontendAgent()


def create_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    directory: Optional[Union[str, Path]] = None,
    orchestrator: Optional[Any] = None,
    frontend_agent: Optional[Any] = None,
) -> ThreadingHTTPServer:
    """Creates and configures a ThreadingHTTPServer instance serving the browser app."""
    target_dir = str(
        Path(directory).resolve()
        if directory
        else Path(__file__).resolve().parent / "browser"
    )

    class ConfiguredRequestHandler(ReanalyzeRequestHandler):
        pass

    ConfiguredRequestHandler.directory = target_dir
    if orchestrator is not None:
        ConfiguredRequestHandler.orchestrator = orchestrator
    if frontend_agent is not None:
        ConfiguredRequestHandler.frontend_agent = frontend_agent

    server = ThreadingHTTPServer((host, port), ConfiguredRequestHandler)
    server.orchestrator = orchestrator
    server.frontend_agent = frontend_agent
    server.directory = target_dir
    return server


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments for the server."""
    parser = argparse.ArgumentParser(
        description="Zero-Dependency Local Web Server & API for Iranian Stock Market Analyzer"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind the HTTP server to (default: 8080)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host/IP address to bind the HTTP server to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Automatically open web browser upon launch",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint for running the local server."""
    args = parse_args(argv)
    server = create_server(host=args.host, port=args.port)
    actual_host, actual_port = server.server_address
    url = f"http://{actual_host}:{actual_port}/"

    print(f"🚀 Serving Iranian Stock Market Watchlist at {url}")
    print(f"⚡ Reanalyze API ready at {url}api/reanalyze")
    print("Press Ctrl+C to terminate.")

    if args.open:
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Failed to open browser automatically: {e}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
