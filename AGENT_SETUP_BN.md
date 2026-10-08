# আপনার ফ্রি AI এজেন্ট — সম্পূর্ণ সেটআপ গাইড (বাংলা)

## কোডে যা তৈরি হয়েছে (আমি করে দিয়েছি)
| ফাইল | কাজ |
|---|---|
| `agent/agent.py` | এজেন্টের মগজ: LLM + টুলস (web search, URL fetch, ফাইল read/write, shell, APK build) |
| `agent/main.py` | FastAPI সার্ভার — ওয়েব UI ও `/api/chat` API |
| `agent/static/index.html` | ডাবল-প্যানেল চ্যাট ওয়েবপেজ |
| `agent/telegram_bot.py` | Telegram বট (মোবাইল থেকে কন্ট্রোল) |
| `agent/mobile/` | Android APK অ্যাপ (Kivy) |
| `agent/Dockerfile`, `agent/README.md` | Hugging Face Spaces-এর জন্য |
| `.github/workflows/build-apk.yml` | GitHub Actions দিয়ে অটো APK বিল্ড |
| `.github/workflows/deploy-hf-space.yml` | `agent/` ফোল্ডার অটো HF Space-এ পুশ |

---

## ধাপ ১ — GitHub (আপনাকে যা করতে হবে)
1. এই রিপো `codexanta/website`-এ `main` ব্রাঞ্চে কোড মার্জ হলে কাজ করবে।
2. APK বিল্ড ও অটো-ডিপ্লয়ের জন্য রিপোটি **Public** থাকলে GitHub Actions একদম ফ্রি।
3. Settings → **Secrets and variables → Actions** → নিচের Secrets যোগ করুন:
   - `HF_TOKEN` — Hugging Face Access token (ধাপ ২ এ বানাবেন, Write permission দিন)
   - `HF_SPACE` — যেমন `your-username/my-agent`

## ধাপ ২ — Hugging Face Space (হোস্টিং, ২৪/৭ ফ্রি)
1. https://huggingface.co-তে ফ্রি অ্যাকাউন্ট খুলুন।
2. https://huggingface.co/settings/tokens → **New token** → Type: *Write* → কপি করুন (এটাই `HF_TOKEN`)।
3. https://huggingface.co/new-space → Name দিন, **SDK: Docker**, Hardware: *CPU basic (free)*, Create।
4. Space-এর **Settings → Variables and secrets** এ যোগ করুন (Secret হিসেবে):
   - `AGENT_TOKEN` — নিজের একটা লম্বা গোপন পাসওয়ার্ড (যেমন ২০+ অক্ষর)। এটা ছাড়া যে কেউ আপনার এজেন্ট ব্যবহার করতে পারবে — **অবশ্যই দিন**।
   - `LLM_API_KEY` — ফ্রি LLM কী (নিচে ধাপ ৩ দেখুন)।
   - `LLM_BASE_URL`, `LLM_MODEL` (Variables হিসেবে) — ধাপ ৩ অনুযায়ী।
   - `ENABLE_SHELL` = `1` (শুধু যদি shell কমান্ড চালাতে চান)
   - `GH_TOKEN` (GitHub token, repo + workflow scope, APK বিল্ড ট্রিগারের জন্য) ও `GH_REPO` = `codexanta/website`
5. ধাপ ১ এর ৩ নম্বরে `HF_SPACE` সেট করার পর GitHub-এ `main`-এ push করলে বা Actions থেকে **Deploy agent to Hugging Face Space** রান করলে কোড Space-এ যাবে।
6. আপনার URL হবে: `https://your-username-my-agent.hf.space` — `/health` খুললে `{"ok": true}` দেখাবে।

> ⚠️ `deploy-hf-space.yml` প্রতিবার Space-কে force-push করে। Space-এ নিজে কিছু এডিট করলে সেটা মুছে যাবে — তাই সব পরিবর্তন GitHub-এ করুন।

## ধাপ ৩ — ফ্রি AI মডেল (LLM) কী নেবেন
সবচেয়ে সহজ: **Groq** (ফ্রি, দ্রুত)
1. https://console.groq.com → Sign up → API Keys → Create → কপি করুন।
2. Space-এ সেট করুন:
   - `LLM_BASE_URL` = `https://api.groq.com/openai/v1`
   - `LLM_MODEL` = `llama-3.3-70b-versatile`
   - `LLM_API_KEY` = আপনার Groq key

বিকল্প (OpenAI-compatible): OpenRouter (`https://openrouter.ai/api/v1`, মডেল `meta-llama/llama-3.3-70b-instruct:free`), Google Gemini OpenAI endpoint (`https://generativelanguage.googleapis.com/v1beta/openai`).

> LLM কী না দিলে এজেন্ট "tools-only" মোডে চলবে: `search: ...`, `fetch: url`, `read: file`, `apk` ইত্যাদি সরাসরি কাজ করবে।

## ধাপ ৪ — Telegram বট (মোবাইল কন্ট্রোল)
1. Telegram-এ **@BotFather** → `/newbot` → নাম দিন → Token কপি করুন।
2. আপনার Telegram ID জানতে **@userinfobot**-এ `/start` দিন → আপনার ID নম্বরটি নিন।
3. বট চালাতে দুটো উপায়:
   - **(ক)** নিজের কম্পিউটারে/Termux-এ: `cd agent && pip install -r requirements.txt && TELEGRAM_BOT_TOKEN=... TELEGRAM_ALLOWED_IDS=আপনার_ID LLM_API_KEY=... python telegram_bot.py`
   - **(খ)** 24/7 চাইলে: Hugging Face-এর আলাদা একটা Space (Docker) বানিয়ে ওখানে `Dockerfile`-এর `CMD` বদলে `python telegram_bot.py` দিন এবং Secrets-এ `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_IDS` দিন। (Space-এ দুটো প্রসেস চালাতে চাইলে আলাদা Space-ই ভালো।)
   - `TELEGRAM_ALLOWED_IDS` **অবশ্যই** দিন, নইলে যে কেউ আপনার বটকে ব্যবহার করতে পারবে।

## ধাপ ৫ — Android APK বানানো
1. `agent/mobile/main.py`-এ `SERVER_URL` বদলান → আপনার HF Space URL, এবং `AGENT_TOKEN` → Space-এর টোকেন।
2. GitHub → **Actions → Build APK → Run workflow** চাপুন।
3. প্রথমবার ৩০–৬০ মিনিট লাগতে পারে (Android SDK ডাউনলোড হয়)। শেষ হলে Run পেজের **Artifacts** থেকে `my-agent-apk` ডাউনলোড করুন।
4. ফোনে APK ইনস্টল করতে "Unknown sources" অনুমতি দিন।
5. চাইলে অ্যাপের আইকন/নাম `buildozer.spec`-এ বদলাতে পারবেন।

> Play Store-এ দিতে চাইলে আলাদা Google Developer account ($25) লাগবে — সেটা ফ্রি নয়।

## ধাপ ৬ — ওয়েব ইন্টারফেস ব্যবহার
Space-এর URL খুলুন → উপরে **Agent token** বক্সে `AGENT_TOKEN` দিন → চ্যাট শুরু করুন। ফাইল আপলোড করে `read: file.name` লিখলে এজেন্ট ফাইল বিশ্লেষণ করবে।

## কমান্ড উদাহরণ
- `search: বাংলাদেশের আজকের আইটি খবর`
- `fetch: https://example.com` — পেজের লেখা পড়ে সারাংশ
- `read: data.csv` — ফাইল পড়ে বিশ্লেষণ
- `apk` — APK বিল্ড শুরু
- `shell: ls` — (ENABLE_SHELL=1 হলে)

## সীমাবদ্ধতা (জেনে রাখুন)
- HF free CPU Space কিছুক্ষণ ব্যবহার না হলে **sleep** হয়ে যায়; প্রথম রিকোয়েস্টে ১ মিনিট লাগতে পারে। এছাড়া ফাইল স্টোরেজ রিস্টার্টে মুছে যায়।
- `shell` ও `write_file` দিয়ে এজেন্ট ফাইল বানাতে/বদলাতে পারে — তাই `AGENT_TOKEN` সবসময় সেট রাখুন।
- Groq/OpenRouter ফ্রি লিমিট আছে; বেশি ব্যবহারে রিকোয়েস্ট সীমা আসতে পারে।
- "যেকোনো ওয়েবসাইট হ্যাক" বা ক্ষতিকর কাজের জন্য এজেন্ট ব্যবহার করবেন না।
- Telegram বট ও Android APK দুটোই এই সার্ভারের URL-এর ওপর নির্ভরশীল।

## যা আমি এই সেশনে যাচাই করেছি
- Python কোড কম্পাইল ✅, FastAPI সার্ভার চালু ✅, Token-সুরক্ষা (401) ✅, ফাইলের workspace-বাইরে যাওয়া আটকানো ✅
- ওয়েব search এখানে কাজ করেনি কারণ এই স্যান্ডবক্সে শুধু GitHub/PyPI-তে ইন্টারনেট আছে; আপনার HF Space / PC-তে এটি কাজ করবে।
- Hugging Face, Telegram, Groq, APK বিল্ড (Actions) — এগুলো আপনার অ্যাকাউন্টে করতে হবে, আমি সেগুলোতে লগইন করতে পারি না।
