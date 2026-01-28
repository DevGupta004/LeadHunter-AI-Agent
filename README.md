# 🎯 LeadHunter AI Agent

**Google Maps Lead Generation Tool** - Extract business leads with contact information, ratings, and more!

---

## 🚀 Quick Start

### Step 1: Install

**macOS / Linux:**
```bash
./install.sh
```

**Windows:**
```powershell
python setup.py
```

**Or manually:**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

### Step 2: Run

**Simple Scraper (Recommended):**
```bash
source venv/bin/activate  # Windows: venv\Scripts\activate
streamlit run lead_hunter.py
```

**AI-Powered Scraper (Better accuracy, needs Ollama):**
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run scraper
source venv/bin/activate
streamlit run lead_hunter_ai.py
```

### Step 3: Use

1. Open browser to **http://localhost:8501**
2. Enter Google Maps search URL (e.g., `https://www.google.com/maps/search/real+estate+business+in+lucknow`)
3. Set number of stores to scrape
4. Click "🚀 Start Scraping"
5. Download Excel file for your telecalling team

---

## 📊 Features

- ✅ **Business Name** - Extracted from Google Maps
- ✅ **Contact Number** - Phone numbers (when available)
- ✅ **Location** - Full address
- ✅ **Website** - Business website (if available)
- ✅ **Rating** - Google Maps rating (1-5 stars)
- ✅ **Excel Export** - Ready for telecalling teams
- ✅ **Auto Deduplication** - Removes duplicate records

---

## 📥 Export Options

After scraping, you can download:

1. **Excel File** - Perfect for telecalling teams
   - Includes: Name, Contact, Location, Website, Rating
   - Automatically removes duplicates
   - Formatted and sorted by rating

2. **JSON File** - Complete data for developers
   - All 14 data points
   - Raw extraction results

---

## 🔧 Requirements

- **Python 3.8+** (check with `python3 --version`)
- **2GB free disk space**
- **Internet connection**

**For AI Version:**
- Install [Ollama](https://ollama.ai)
- Run `ollama pull llama3.2`

---

## 🐛 Troubleshooting

### "Python not found"
- Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
- Windows: Check "Add Python to PATH" during installation

### "Playwright browsers not found"
```bash
source venv/bin/activate
python -m playwright install chromium
```

### "Port 8501 already in use"
```bash
# Kill existing process
lsof -ti:8501 | xargs kill -9  # macOS/Linux
# or
netstat -ano | findstr :8501  # Windows, then kill the PID
```

### Same data for all stores?
- Make sure you're clicking different stores
- Wait for the page to load completely
- Check browser window to see if stores are changing

---

## 📁 Project Files

- `lead_hunter.py` - Simple scraper (fast, no AI needed)
- `lead_hunter_ai.py` - AI-powered scraper (better accuracy)
- `install.sh` / `install.ps1` - One-command installer
- `setup.py` - Cross-platform installer
- `run.sh` / `run.bat` - Quick run scripts

---

## 💡 Tips

- **Start small**: Test with 10-20 stores first
- **Enable pagination**: Loads more results automatically
- **Watch the browser**: See what's being scraped
- **Check Excel export**: Perfect format for telecalling teams

---

## 📝 Example Usage

```bash
# 1. Install
./install.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run scraper
streamlit run lead_hunter.py

# 4. In browser:
#    - Enter: https://www.google.com/maps/search/real+estate+business+in+lucknow
#    - Set stores: 20
#    - Click "Start Scraping"
#    - Download Excel file

# 5. Upload Excel to Google Sheets for your team!
```

---

**Happy Lead Hunting! 🎯**
