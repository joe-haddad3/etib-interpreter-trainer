# Local Aya Expanse Setup

This project can use Groq or a local Aya Expanse 8B model for Module A text generation.

## 1. Install Python inference packages

From the backend virtual environment:

```powershell
cd C:\Users\user\Desktop\ETIB-Interpreter-Trainer\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Download Aya manually

Go to:

https://huggingface.co/CohereLabs/aya-expanse-8b

Download the model files into a local folder such as:

```text
C:\Users\user\Desktop\ETIB-Interpreter-Trainer\models\aya-expanse-8b
```

The `models/` folder is ignored by Git so the weights are not committed.

## 3. Configure `.env`

Set:

```env
LLM_PROVIDER=local_aya
LOCAL_MODEL_PATH=C:\Users\user\Desktop\ETIB-Interpreter-Trainer\models\aya-expanse-8b
LOCAL_MODEL_DEVICE_MAP=auto
LOCAL_MODEL_TORCH_DTYPE=auto
```

To switch back to Groq:

```env
LLM_PROVIDER=groq
```

## 4. Start the backend

```powershell
cd C:\Users\user\Desktop\ETIB-Interpreter-Trainer\backend
.\.venv\Scripts\Activate.ps1
python app.py
```

The first local generation request will load Aya into memory, which can take time.
