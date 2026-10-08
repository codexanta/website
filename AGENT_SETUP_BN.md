# আপনার ফ্রি AI এজেন্ট — সম্পূর্ণ সেটআপ গাইড (বাংলা)

> ⚠️ **আপডেট:** Hugging Face-এ এখন ফ্রি অ্যাকাউন্টে Docker/Gradio Space বানানো যায় না (PRO লাগে)। তাই হোস্টিং **Render.com**-এ নেওয়া হয়েছে — ফ্রি, কার্ড লাগে না। Hugging Face শুধু Static (সাধারণ ওয়েবপেজ) হোস্ট করতে পারবে।

## কোডে কী আছে
| ফাইল | কাজ |
|---|---|
| `agent/agent.py` | এজেন্টের মগজ: LLM (একাধিক ফ্রি provider, অটো-ফলব্যাক) + টুলস |
| `agent/main.py` | সার্ভার: ওয়েব চ্যাট UI (`/`) ও API (`/api/chat`) |
| `agent/telegram_bot.py` | Telegram বট (সার্ভারের ভেতরেই চলে) |
| `agent/mobile/` | Android APK অ্যাপ |
| `agent/Dockerfile` + `render.yaml` | Render-এ অটো-ডিপ্লয় |
| `.github/workflows/build-apk.yml` | GitHub Actions-এ APK বিল্ড |
| `.github/workflows/keep-alive.yml` | Render-কে ঘুম থেকে জাগিয়ে রাখে |

---

## ধাপ ১ — GitHub
1. PR খুলুন: https://github.com/codexanta/website/pull/new/arena/96931092-website → **Merge** করুন (main-এ)।
2. Repo **Public** রাখুন (Actions ফ্রি রাখতে)।
3. Settings → Secrets and variables → Actions → **New repository secret**:
   - `AGENT_URL` — ধাপ ৩ শেষে পাবেন (যেমন `https://personal-agent.onrender.com`)

## ধাপ ২ — Render (হোস্টিং, ফ্রি, কার্ড লাগে না)
1. https://render.com → **Sign up with GitHub**।
2. Dashboard → **New +** → **Blueprint** → `codexanta/website` repo সিলেক্ট করুন → Render `render.yaml` পড়বে।
3. Service-এর নাম `personal-agent` থাকবে। তখন **Environment Variables** পেজে নিচের মানগুলো বসান (ধাপ ৩ ও ৪ দেখুন):
   - `AGENT_TOKEN` — **অবশ্যই** দিন: লম্বা গোপন পাসওয়ার্ড (২০+ অক্ষর)।
   - LLM key: `GEMINI_API_KEY`, `GROQ_API_KEY` ইত্যাদি (অন্তত একটি)।
   - সার্চ: `TAVILY_API_KEY` (ঐচ্ছিক)।
   - Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_IDS` (ঐচ্ছিক)।
4. **Apply / Deploy** চাপুন। Build ৫–১০ মিনিট।
5. URL হবে `https://personal-agent.onrender.com` (নামটি আলাদা হলে সেটা)। ব্রাউজারে খুলুন → চ্যাট পেজ আসবে।
   `https://.../health` খুললে `llm_providers` দেখাবে — আপনার যোগ করা provider গুলো।
6. এই URL কপি করে GitHub-এ `AGENT_URL` Secret হিসেবে দিন (ধাপ ১.৩)।

> Render ফ্রি সার্ভিস ১৫ মিনিট ব্যবহার না হলে ঘুমায়। `keep-alive` workflow প্রতি ১০ মিনিটে ping করে, তাই সাধারণত জাগা থাকবে। GitHub-এর Actions-এ **Keep agent awake** চালু আছে কি না দেখুন।
> Render-এর ফ্রি সীমা: মাসে ৭৫০ ঘণ্টা, ৫১২ MB RAM। ফাইল ডিস্ক রিস্টার্টে মুছে যায়।

## ধাপ ৩ — ফ্রি LLM API (অটো-ফলব্যাক)
যে provider-এর key দেবেন, সেটা চালু হবে। একটা রেট-লিমিটে আটকালে পরেরটা ব্যবহার হবে।

| Provider | কোথায় key | Env নাম | ফ্রি সীমা (অক্টোবর ২০২৬) | ডিফল্ট মডেল |
|---|---|---|---|---|
| **Google Gemini** (মানের জন্য সেরা) | aistudio.google.com/apikey | `GEMINI_API_KEY` | Flash ফ্রি, কার্ড লাগে না। ⚠️ ফ্রি ডাটা Google উন্নতিতে ব্যবহার করতে পারে | `gemini-2.5-flash` |
| **Groq** (সবচেয়ে দ্রুত) | console.groq.com | `GROQ_API_KEY` | ~30 req/min, ~1,000 req/day | `openai/gpt-oss-120b` |
| **OpenRouter** | openrouter.ai/keys | `OPENROUTER_API_KEY` | `:free` মডেল, ২০ req/min, ৫০ req/day | `openrouter/free` |
| **Mistral** | console.mistral.ai | `MISTRAL_API_KEY` | Experiment প্ল্যানে মাসিক ক্রেডিট | `mistral-small-latest` |
| **Hugging Face** | huggingface.co/settings/tokens | `HF_TOKEN` | Inference Providers-এ মাসিক ক্রেডিট | `openai/gpt-oss-120b` |

**সুপারিশ:** `GEMINI_API_KEY` + `GROQ_API_KEY` নিন। মডেল বদলাতে `GEMINI_MODEL` ইত্যাদি Variable দিন।

## ধাপ ৪ — সার্চ
- **Tavily** (সুপারিশ): tavily.com → Sign up → key (`tvly-...`) → `TAVILY_API_KEY`। ১,০০০ credit/মাস, কার্ড লাগে না।
- Brave (`BRAVE_API_KEY`, $৫ credit/মাস, কার্ড লাগে) — ঐচ্ছিক।
- কিছু না দিলে DuckDuckGo দিয়ে কাজ চলবে।

## ধাপ ৫ — Telegram বট (মোবাইল কন্ট্রোল)
1. Telegram-এ **@BotFather** → `/newbot` → Token কপি → `TELEGRAM_BOT_TOKEN`।
2. **@userinfobot**-এ `/start` → আপনার ID → `TELEGRAM_ALLOWED_IDS`। **এটা অবশ্যই দিন**, নইলে যে কেউ বট ব্যবহার করবে।
3. Render-এ env সেভ করে redeploy করলে বট নিজে চালু হবে। Telegram-এ বটকে `/start` লিখুন।

## ধাপ ৬ — Android APK
1. `agent/mobile/main.py`-এ `SERVER_URL` = আপনার Render URL, `AGENT_TOKEN` = ধাপ ২-এর টোকেন।
2. GitHub → **Actions → Build APK → Run workflow**।
3. প্রথমবার ৩০–৬০ মিনিট। শেষে Run পেজের **Artifacts**-এ `my-agent-apk` ডাউনলোড করুন।
4. ফোনে "Unknown sources" অনুমতি দিয়ে ইনস্টল করুন।
5. APK থেকে নিজে বিল্ড চালাতে চাইলে Render-এ `GH_TOKEN` (GitHub token: repo + workflow scope) ও `GH_REPO=codexanta/website` দিন; তখন চ্যাটে `apk` লিখলেই বিল্ড শুরু হবে।

## ধাপ ৭ — ব্যবহার
ওয়েব পেজে উপরে **Agent token** বসিয়ে চ্যাট করুন।
- `search: বাংলাদেশের আজকের আইটি খবর`
- `fetch: https://example.com`
- `read: notes.txt` (ফাইল আগে আপলোড করতে হবে)
- `apk`

---

## এজেন্ট যা পারে, আর যা পারে না (সৎ হিসাব)

**পারে (কোড আছে):**
- প্রশ্নের উত্তর, বাংলা/ইংরেজি/Banglish-এ
- ওয়েব সার্চ ও পেজের লেখা পড়ে সারাংশ/রিসার্চ (Tavily/Brave/DuckDuckGo)
- txt, md, csv, json ও কোড ফাইল পড়া ও লেখা; ফাইল বিশ্লেষণ (LLM দিয়ে)
- APK বিল্ড ট্রিগার (GitHub Actions)
- Telegram ও ওয়েব থেকে কন্ট্রোল
- Android অ্যাপ থেকে ব্যবহার

**এখনও পারে না / সীমাবদ্ধ:**
- **যেকোনো ওয়েবসাইট বানানো বা deploy**: শুধু কোড লিখে ফাইল বানাতে পারে; নিজে Netlify/Vercel-এ deploy করার টুল যুক্ত নেই।
- **Shell / bash**: ডিফল্টে বন্ধ (`ENABLE_SHELL=0`)। চালু করলে শুধু allowlisted কমান্ড ও কোনো pipe/redirect চলবে — নিরাপত্তার জন্য।
- **PDF, Excel, Word, ছবি, অডিও পড়া**: এখনো নেই। লাইব্রেরি যোগ করলে হবে।
- **ইন্টারনেটে যেকোনো কাজ** (লগইন, পেমেন্ট, সোশ্যাল মিডিয়া পোস্ট): নেই।
- **অন্য অ্যাপ/অ্যাকাউন্ট নিয়ন্ত্রণ**: নেই।
- **Live API কল এই সেশনে পরীক্ষা করা যায়নি** (স্যান্ডবক্সে LLM/Render-এ নেটওয়ার্ক নেই)।
- **Free সীমা**: LLM ও সার্চ কোটা শেষ হলে সাময়িক বন্ধ থাকবে; Render ফ্রি সার্ভিস ঘুমায় (keep-alive দিয়ে কমানো যায়, পুরোপুরি শূন্য হয় না)।
- ফ্রি Gemini/OpenRouter-এ আপনার প্রম্পট উন্নতিতে ব্যবহৃত হতে পারে — গোপন তথ্য দেবেন না।

## যাচাই করা হয়েছে
- Python কোড কম্পাইল ✅, FastAPI সার্ভার চালু ও `/health` 200 ✅
- Token ছাড়া 401 ✅, workspace-বাইরের ফাইল আটকানো ✅
- Provider fallback chain ও key-ছাড়া tools-only mode ✅
- Render ডিপ্লয়, Telegram, APK বিল্ড, LLM/Search live কল — আপনার অ্যাকাউন্টে করতে হবে।
